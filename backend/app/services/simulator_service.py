import json
import uuid
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.audit_event import AuditEvent
from app.models.recovery_memory import RecoveryMemory
from app.services.ml_prediction_service import predict_recovery
from app.services.tool_registry import dispatch_tool, ALLOWED_TOOLS
from app.services.ai_agent_service import (
    evaluate_recovery_strategy,
    validate_state_transition,
    ALLOWED_STRATEGIES,
    STRATEGY_TOOL_MAPPING,
)
from app.services.memory_service import (
    record_recovery_experience,
    MEMORY_VERSION,
)


def simulate_case_recovery(
    db: Session,
    recovery_case_id: str,
    merchant_id: str,
    scenario: str = "auto",  # 'auto', 'force_success', 'force_fail', 'force_escalate'
) -> Dict[str, Any]:
    """
    Executes an autonomous recovery simulation loop for a single case.
    Supports controlled judge scenarios ('auto', 'force_success', 'force_fail', 'force_escalate').
    Integrates adaptive agent memory recording for continuous learning.
    """
    rec_case = (
        db.query(RecoveryCase)
        .filter(RecoveryCase.id == recovery_case_id, RecoveryCase.merchant_id == merchant_id)
        .first()
    )
    if not rec_case:
        raise ValueError(f"Recovery case '{recovery_case_id}' not found or unauthorized.")

    payment = db.query(Payment).filter(Payment.id == rec_case.payment_id).first()
    if not payment:
        raise ValueError(f"Payment record '{rec_case.payment_id}' not found.")

    customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
    if not customer:
        raise ValueError(f"Customer '{payment.customer_id}' not found.")

    # Guard: Terminal cases cannot be recovered again
    if rec_case.status in ["RECOVERED", "ESCALATED"]:
        raise ValueError(f"Recovery case '{recovery_case_id}' is already in terminal state '{rec_case.status}'.")

    # Step 1: Transition to ANALYZING
    if validate_state_transition(rec_case.status, "ANALYZING"):
        rec_case.status = "ANALYZING"
        db.commit()

    # Step 2: ML Recovery Probability (Phase 5)
    ml_pred = predict_recovery(db, recovery_case_id=rec_case.id, merchant_id=merchant_id)
    ml_prob = ml_pred["recovery_probability"]

    # Step 3: AI Recovery Agent Decision (with Memory Retrieval)
    selected_strategy, reason, confidence = evaluate_recovery_strategy(
        customer=customer,
        payment=payment,
        recovery_case=rec_case,
        ml_probability=ml_prob,
        db=db,
    )

    # Force scenario overrides for judge demonstration if requested
    if scenario == "force_escalate":
        selected_strategy = "ESCALATE_TO_HUMAN"
        reason = "Judge scenario control: Forced human operations escalation."
    elif selected_strategy not in ALLOWED_STRATEGIES:
        selected_strategy = "ESCALATE_TO_HUMAN"
        reason = "Guardrail violation: Rejected unsupported strategy. Routed to human ops."

    tool_name = STRATEGY_TOOL_MAPPING.get(selected_strategy, "human_escalation_tool")
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError(f"Disallowed tool '{tool_name}' blocked by security guardrail.")

    # Step 4: Transition to ACTION_SELECTED
    rec_case.selected_strategy = selected_strategy
    if validate_state_transition(rec_case.status, "ACTION_SELECTED"):
        rec_case.status = "ACTION_SELECTED"
        db.commit()

    # Step 5: Execute Approved Simulator Tool
    if scenario == "force_success":
        tool_result_status, tool_metadata, is_recovered = "SUCCESS", {
            "simulator": tool_name,
            "scenario": "force_success",
            "amount_paise": payment.amount,
            "demo": True,
        }, True
    elif scenario == "force_fail":
        tool_result_status, tool_metadata, is_recovered = "FAILED", {
            "simulator": tool_name,
            "scenario": "force_fail",
            "amount_paise": payment.amount,
            "demo": True,
        }, False
    else:
        # Standard stochastic simulator dispatch based on ML probability
        tool_result_status, tool_metadata, is_recovered = dispatch_tool(
            tool_name=tool_name,
            case_id=rec_case.id,
            payment_id=payment.id,
            customer_id=customer.id,
            amount_paise=payment.amount,
            ml_probability=ml_prob,
            reason=reason,
        )

    # Step 6: Increment attempt count and transition to ACTION_EXECUTED
    rec_case.attempt_count += 1
    action_uuid = str(uuid.uuid4())[:8]
    action_id = f"act_{rec_case.id.replace('rec_', '')}_{rec_case.attempt_count}_{action_uuid}"

    if validate_state_transition(rec_case.status, "ACTION_EXECUTED"):
        rec_case.status = "ACTION_EXECUTED"
        db.commit()

    # Step 7: Transition to final state based on outcome
    if selected_strategy == "ESCALATE_TO_HUMAN":
        rec_case.status = "ESCALATED"
        state_log = "ACTION_SELECTED -> ACTION_EXECUTED -> ESCALATED"
    elif is_recovered:
        rec_case.status = "RECOVERED"
        rec_case.recovered_amount = min(payment.amount, rec_case.expected_revenue or payment.amount)
        state_log = "ACTION_SELECTED -> ACTION_EXECUTED -> RECOVERED"
    else:
        state_log = "ACTION_SELECTED -> ACTION_EXECUTED"

    rec_case.updated_at = datetime.now(timezone.utc)

    # Step 8: Persist Recovery Action
    recovery_action = RecoveryAction(
        id=action_id,
        recovery_case_id=rec_case.id,
        action_type=selected_strategy,
        agent_reason=reason,
        result=tool_result_status,
        metadata_json=json.dumps(tool_metadata),
        executed_at=datetime.now(timezone.utc),
    )
    db.add(recovery_action)

    # Step 9: Persist Audit Event
    audit_id = f"aud_{action_id}"
    audit_event = AuditEvent(
        id=audit_id,
        merchant_id=merchant_id,
        event_type=f"SIMULATOR_{selected_strategy}",
        entity_id=rec_case.id,
        actor="autonomous_simulator_engine_v1",
        metadata_json=json.dumps({
            "recovery_case_id": rec_case.id,
            "payment_id": payment.id,
            "customer_id": customer.id,
            "ml_probability": ml_prob,
            "selected_strategy": selected_strategy,
            "scenario": scenario,
            "tool_invoked": tool_name,
            "tool_result": tool_result_status,
            "state_transition": state_log,
            "recovered_amount_paise": rec_case.recovered_amount,
            "original_amount_paise": payment.amount,
            "memory_version": MEMORY_VERSION,
            "demo": True,
        }),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit_event)
    db.commit()

    # Step 10: Persist Experience to Adaptive Agent Memory
    record_recovery_experience(
        db=db,
        recovery_case_id=rec_case.id,
        merchant_id=merchant_id,
        strategy=selected_strategy,
        tool_invoked=tool_name,
        tool_result=tool_result_status,
        is_recovered=is_recovered,
        recovered_amount_paise=rec_case.recovered_amount,
        attempt_count=rec_case.attempt_count,
    )

    db.refresh(rec_case)

    return {
        "recovery_case_id": rec_case.id,
        "payment_id": payment.id,
        "customer_id": customer.id,
        "original_amount_paise": payment.amount,
        "original_amount_inr": round(payment.amount / 100, 2),
        "recovered_amount_paise": rec_case.recovered_amount,
        "recovered_amount_inr": round(rec_case.recovered_amount / 100, 2),
        "ml_probability": ml_prob,
        "ml_probability_percentage": round(ml_prob * 100, 1),
        "selected_strategy": selected_strategy,
        "decision_reason": reason,
        "tool_invoked": tool_name,
        "tool_result": tool_result_status,
        "recovery_action_id": action_id,
        "current_status": rec_case.status,
        "attempt_count": rec_case.attempt_count,
        "is_recovered": is_recovered,
        "scenario": scenario,
        "memory_version": MEMORY_VERSION,
        "demo": True,
    }


def run_batch_simulation(
    db: Session,
    merchant_id: str,
    batch_size: int = 25,
    scenario: str = "auto",
) -> Dict[str, Any]:
    """
    Executes autonomous recovery simulation across an active cohort of cases.
    """
    active_cases = (
        db.query(RecoveryCase)
        .filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryCase.status.in_(["FAILED", "ACTION_EXECUTED"]),
        )
        .limit(batch_size)
        .all()
    )

    results = []
    total_recovered_paise = 0
    total_recovered_count = 0
    total_escalated_count = 0

    for c in active_cases:
        try:
            res = simulate_case_recovery(
                db=db,
                recovery_case_id=c.id,
                merchant_id=merchant_id,
                scenario=scenario,
            )
            results.append(res)
            if res["is_recovered"]:
                total_recovered_count += 1
                total_recovered_paise += res["recovered_amount_paise"]
            elif res["current_status"] == "ESCALATED":
                total_escalated_count += 1
        except Exception:
            continue

    return {
        "batch_size_requested": batch_size,
        "cases_processed": len(results),
        "recovered_count": total_recovered_count,
        "escalated_count": total_escalated_count,
        "still_active_count": len(results) - (total_recovered_count + total_escalated_count),
        "total_recovered_paise": total_recovered_paise,
        "total_recovered_inr": round(total_recovered_paise / 100, 2),
        "simulation_results": results,
        "memory_version": MEMORY_VERSION,
        "demo": True,
    }


def get_simulator_metrics(db: Session, merchant_id: str) -> Dict[str, Any]:
    total_cases = db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).count()
    failed_cases = (
        db.query(RecoveryCase)
        .filter(RecoveryCase.merchant_id == merchant_id, RecoveryCase.status == "FAILED")
        .count()
    )
    recovered_cases = (
        db.query(RecoveryCase)
        .filter(RecoveryCase.merchant_id == merchant_id, RecoveryCase.status == "RECOVERED")
        .count()
    )
    escalated_cases = (
        db.query(RecoveryCase)
        .filter(RecoveryCase.merchant_id == merchant_id, RecoveryCase.status == "ESCALATED")
        .count()
    )
    in_progress_cases = (
        db.query(RecoveryCase)
        .filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryCase.status.in_(["ANALYZING", "ACTION_SELECTED", "ACTION_EXECUTED", "WAITING"]),
        )
        .count()
    )

    total_recovered_paise = (
        db.query(func.sum(RecoveryCase.recovered_amount))
        .filter(RecoveryCase.merchant_id == merchant_id)
        .scalar()
        or 0
    )

    total_at_risk_paise = (
        db.query(func.sum(RecoveryCase.expected_revenue))
        .filter(RecoveryCase.merchant_id == merchant_id, RecoveryCase.status != "RECOVERED")
        .scalar()
        or 0
    )

    recovery_rate = (recovered_cases / total_cases * 100) if total_cases > 0 else 0.0

    return {
        "total_recovery_cases": total_cases,
        "failed_cases": failed_cases,
        "in_progress_cases": in_progress_cases,
        "recovered_cases": recovered_cases,
        "escalated_cases": escalated_cases,
        "recovery_rate_percentage": round(recovery_rate, 2),
        "total_revenue_recovered_paise": total_recovered_paise,
        "total_revenue_recovered_inr": round(total_recovered_paise / 100, 2),
        "revenue_still_at_risk_paise": total_at_risk_paise,
        "revenue_still_at_risk_inr": round(total_at_risk_paise / 100, 2),
        "memory_version": MEMORY_VERSION,
        "demo": True,
    }


def reset_simulator_state(db: Session, merchant_id: str) -> Dict[str, Any]:
    cases = db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).all()
    count = 0
    for c in cases:
        c.status = "FAILED"
        c.attempt_count = 0
        c.recovered_amount = 0
        c.selected_strategy = None
        count += 1

    # Clear actions, simulation audit events, and adaptive memories
    db.query(RecoveryAction).delete()
    db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).delete()
    db.query(AuditEvent).filter(
        AuditEvent.merchant_id == merchant_id,
        AuditEvent.actor.in_(["ai_recovery_agent_v1", "autonomous_simulator_engine_v1", "adaptive_memory_engine_v1"]),
    ).delete()

    db.commit()
    return {
        "reset_status": "SUCCESS",
        "cases_reset": count,
        "message": "Simulator and adaptive memory state cleanly reset to baseline.",
        "memory_version": MEMORY_VERSION,
        "demo": True,
    }
