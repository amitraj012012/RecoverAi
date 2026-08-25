import json
import uuid
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.audit_event import AuditEvent
from app.services.ml_prediction_service import predict_recovery
from app.services.tool_registry import dispatch_tool, ALLOWED_TOOLS
from app.services.memory_service import (
    retrieve_relevant_experiences,
    record_recovery_experience,
    MEMORY_VERSION,
)

# Strictly 6 Approved Recovery Strategies
ALLOWED_STRATEGIES = [
    "RETRY_PAYMENT",
    "CREATE_PAYMENT_LINK",
    "ALTERNATE_PAYMENT_METHOD",
    "SEND_REMINDER",
    "OFFER_INCENTIVE",
    "ESCALATE_TO_HUMAN",
]

STRATEGY_TOOL_MAPPING = {
    "RETRY_PAYMENT": "payment_retry_simulator",
    "CREATE_PAYMENT_LINK": "payment_link_simulator",
    "ALTERNATE_PAYMENT_METHOD": "payment_method_update_simulator",
    "SEND_REMINDER": "customer_notification_simulator",
    "OFFER_INCENTIVE": "incentive_offer_simulator",
    "ESCALATE_TO_HUMAN": "human_escalation_tool",
}

VALID_STATE_TRANSITIONS = {
    "FAILED": ["ANALYZING", "ESCALATED"],
    "ANALYZING": ["ACTION_SELECTED", "ESCALATED"],
    "ACTION_SELECTED": ["ACTION_EXECUTED", "ESCALATED"],
    "ACTION_EXECUTED": ["WAITING", "VERIFIED", "RECOVERED", "FAILED", "ESCALATED"],
    "WAITING": ["VERIFIED", "RECOVERED", "FAILED", "ESCALATED"],
    "VERIFIED": ["RECOVERED"],
    "RECOVERED": [],
    "ESCALATED": [],
}


def validate_state_transition(current_state: str, new_state: str) -> bool:
    """
    Validates state machine transitions against strict architecture state graph.
    """
    if current_state == new_state:
        return True
    allowed = VALID_STATE_TRANSITIONS.get(current_state, [])
    return new_state in allowed


def evaluate_recovery_strategy(
    customer: Customer,
    payment: Payment,
    recovery_case: RecoveryCase,
    ml_probability: float,
    db: Optional[Session] = None,
) -> Tuple[str, str, float]:
    """
    Bounded Adaptive Decision Engine:
    Selects from strictly 6 allowed recovery strategies based on:
    1. Phase 5 ML Recovery Probability
    2. Failure taxonomy & payment rails
    3. Customer longevity & engagement scores
    4. Guardrail limits (attempt_count < 3)
    5. Adaptive historical memory signals from previous simulator outcomes
    """
    attempt_count = recovery_case.attempt_count
    failure_reason = payment.failure_reason or ""
    activity_score = customer.activity_score
    tenure = customer.tenure

    # Guardrail 1: Max 3 retry attempts exceeded -> Forced Escalation
    if attempt_count >= 3:
        return (
            "ESCALATE_TO_HUMAN",
            f"Maximum automatic retry threshold reached ({attempt_count} attempts). Escalating to merchant operations.",
            0.95,
        )

    # Query Adaptive Memory for historical empirical evidence if DB session available
    memory_signal = None
    if db:
        mem_data = retrieve_relevant_experiences(
            db=db,
            merchant_id=customer.merchant_id,
            failure_reason=failure_reason,
            activity_score=activity_score,
            tenure=tenure,
            limit=5,
        )
        perf = mem_data.get("strategy_performance", {})
        # Look for empirical win-rate dominance
        for strat, stats in perf.items():
            if stats["attempts"] >= 3 and stats["win_rate"] >= 0.70:
                memory_signal = (strat, stats["win_rate_percentage"])
                break

    # Strategy Selection by Failure Type & ML Probability
    if "Expired" in failure_reason:
        reason_text = f"Card expired on established customer ({tenure}mo tenure). Dispatched automated self-serve payment link."
        if memory_signal and memory_signal[0] == "CREATE_PAYMENT_LINK":
            reason_text += f" (Adaptive memory confirmed {memory_signal[1]}% empirical conversion on expired cards)."
        return ("CREATE_PAYMENT_LINK", reason_text, 0.92)

    elif "UPI" in failure_reason or "Bank" in failure_reason or "Timeout" in failure_reason:
        if attempt_count == 0 and ml_probability >= 0.65:
            reason_text = f"Transient infrastructure timeout ({failure_reason}) with high ML probability ({ml_probability*100:.1f}%). Scheduled smart gateway retry."
            if memory_signal and memory_signal[0] == "RETRY_PAYMENT":
                reason_text += f" (Adaptive memory: {memory_signal[1]}% retry success for transient timeouts)."
            return ("RETRY_PAYMENT", reason_text, 0.89)
        else:
            return (
                "ALTERNATE_PAYMENT_METHOD",
                "Transient rail failure persisted. Prompted customer to complete via alternate payment rail (UPI/Netbanking).",
                0.82,
            )

    elif "Insufficient" in failure_reason:
        if ml_probability >= 0.75 and activity_score >= 0.70:
            reason_text = f"High-engagement loyal customer ({activity_score*100:.0f}% activity, {tenure}mo tenure) with temporary decline. Dispatched priority payment link."
            if memory_signal:
                reason_text += f" (Adaptive memory: reinforced by {memory_signal[0]} win-rate {memory_signal[1]}%)."
            return ("CREATE_PAYMENT_LINK", reason_text, 0.88)
        elif activity_score < 0.35 and attempt_count >= 1:
            return (
                "OFFER_INCENTIVE",
                "Low engagement subscriber at churn risk. Dispatched 10% renewal incentive to secure retention.",
                0.68,
            )
        else:
            return (
                "SEND_REMINDER",
                "Temporary decline. Sent courteous reminder notice with payment retry instructions.",
                0.72,
            )

    elif "Limit" in failure_reason:
        return (
            "ALTERNATE_PAYMENT_METHOD",
            "Transaction exceeded card limit ceiling. Requested alternate enterprise billing method.",
            0.76,
        )

    elif ml_probability < 0.30:
        return (
            "ESCALATE_TO_HUMAN",
            f"Low recovery probability ({ml_probability*100:.1f}%) with complex failure profile. Escalated to Human Ops.",
            0.90,
        )

    else:
        return (
            "CREATE_PAYMENT_LINK",
            f"Automated recovery link generated (ML probability: {ml_probability*100:.1f}%).",
            0.80,
        )


def execute_recovery_workflow(
    db: Session,
    recovery_case_id: str,
    merchant_id: str,
) -> Dict[str, Any]:
    """
    Full Adaptive Recovery Execution Pipeline:
    1. Validate merchant ownership & case state
    2. Transition to ANALYZING
    3. Query Phase 5 ML Recovery Probability
    4. Retrieve Adaptive Historical Memory
    5. AI Agent selects allowed recovery strategy
    6. Guardrails validate strategy & limits
    7. Transition to ACTION_SELECTED
    8. Execute allowlisted simulator tool
    9. Transition to ACTION_EXECUTED -> RECOVERED / ESCALATED
    10. Persist RecoveryAction & AuditEvent
    11. Persist new experience to Adaptive Memory (continuous learning)
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
        raise ValueError(f"Associated payment '{rec_case.payment_id}' not found.")

    customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
    if not customer:
        raise ValueError(f"Customer profile '{payment.customer_id}' not found.")

    # 1. State machine check: cannot re-execute already resolved terminal cases
    if rec_case.status in ["RECOVERED", "ESCALATED"]:
        raise ValueError(f"Recovery case is already in terminal state '{rec_case.status}'.")

    # Step 1: Transition to ANALYZING
    if validate_state_transition(rec_case.status, "ANALYZING"):
        rec_case.status = "ANALYZING"
        db.commit()

    # Step 2: Obtain ML Recovery Probability (Phase 5)
    ml_pred = predict_recovery(db, recovery_case_id=rec_case.id, merchant_id=merchant_id)
    ml_prob = ml_pred["recovery_probability"]

    # Step 3: Adaptive AI Strategy Reasoning (with Memory Context)
    selected_strategy, reason, confidence = evaluate_recovery_strategy(
        customer=customer,
        payment=payment,
        recovery_case=rec_case,
        ml_probability=ml_prob,
        db=db,
    )

    # Step 4: Deterministic Guardrails Check
    if selected_strategy not in ALLOWED_STRATEGIES:
        selected_strategy = "ESCALATE_TO_HUMAN"
        reason = "Rejected unsupported strategy. Safe fallback to human escalation."

    tool_name = STRATEGY_TOOL_MAPPING.get(selected_strategy, "human_escalation_tool")
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError(f"Disallowed tool '{tool_name}' blocked by guardrail.")

    # Step 5: Transition to ACTION_SELECTED
    rec_case.selected_strategy = selected_strategy
    if validate_state_transition(rec_case.status, "ACTION_SELECTED"):
        rec_case.status = "ACTION_SELECTED"
        db.commit()

    # Step 6: Execute Approved Allowlisted Simulator Tool
    tool_result_status, tool_metadata, is_recovered = dispatch_tool(
        tool_name=tool_name,
        case_id=rec_case.id,
        payment_id=payment.id,
        customer_id=customer.id,
        amount_paise=payment.amount,
        ml_probability=ml_prob,
        reason=reason,
    )

    # Step 7: Increment attempt count and transition to ACTION_EXECUTED
    rec_case.attempt_count += 1
    action_uuid = str(uuid.uuid4())[:8]
    action_id = f"act_{rec_case.id.replace('rec_', '')}_{rec_case.attempt_count}_{action_uuid}"

    if validate_state_transition(rec_case.status, "ACTION_EXECUTED"):
        rec_case.status = "ACTION_EXECUTED"
        db.commit()

    # Step 8: Complete terminal transition based on verification / tool outcome
    if selected_strategy == "ESCALATE_TO_HUMAN":
        rec_case.status = "ESCALATED"
        state_transition_log = "ACTION_SELECTED -> ACTION_EXECUTED -> ESCALATED"
    elif is_recovered:
        rec_case.status = "RECOVERED"
        rec_case.recovered_amount = min(payment.amount, rec_case.expected_revenue or payment.amount)
        state_transition_log = "ACTION_SELECTED -> ACTION_EXECUTED -> RECOVERED"
    else:
        state_transition_log = "ACTION_SELECTED -> ACTION_EXECUTED"

    rec_case.updated_at = datetime.now(timezone.utc)

    # Step 9: Persist RecoveryAction
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

    # Step 10: Persist AuditEvent
    audit_id = f"aud_{action_id}"
    audit_event = AuditEvent(
        id=audit_id,
        merchant_id=merchant_id,
        event_type=f"RECOVERY_{selected_strategy}",
        entity_id=rec_case.id,
        actor="ai_recovery_agent_v1",
        metadata_json=json.dumps({
            "recovery_case_id": rec_case.id,
            "payment_id": payment.id,
            "customer_id": customer.id,
            "ml_probability": ml_prob,
            "selected_strategy": selected_strategy,
            "agent_reason": reason,
            "confidence": confidence,
            "tool_invoked": tool_name,
            "tool_result": tool_result_status,
            "state_transition": state_transition_log,
            "amount_paise": payment.amount,
            "memory_version": MEMORY_VERSION,
            "demo": True,
        }),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit_event)
    db.commit()

    # Step 11: Record Outcome into Adaptive Agent Memory (Continuous Learning)
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
        "amount_paise": payment.amount,
        "amount_inr": round(payment.amount / 100, 2),
        "ml_probability": ml_prob,
        "ml_probability_percentage": round(ml_prob * 100, 1),
        "selected_strategy": selected_strategy,
        "decision_reason": reason,
        "confidence": confidence,
        "tool_invoked": tool_name,
        "tool_result": tool_result_status,
        "recovery_action_id": action_id,
        "current_status": rec_case.status,
        "attempt_count": rec_case.attempt_count,
        "recovered_amount_paise": rec_case.recovered_amount,
        "is_recovered": is_recovered,
        "memory_version": MEMORY_VERSION,
        "demo": True,
    }
