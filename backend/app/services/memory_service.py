import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from app.models.recovery_memory import RecoveryMemory
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction
from app.models.audit_event import AuditEvent

MEMORY_VERSION = "agent-memory-v1"


def derive_context_cluster(
    failure_reason: str,
    activity_score: float = 0.5,
    tenure: int = 1,
) -> str:
    """
    Categorizes the recovery scenario into an explainable behavioral/failure cluster.
    """
    r = failure_reason or "Unknown"

    if "Expired" in r:
        return "CARD_EXPIRED"
    elif "UPI" in r or "Timeout" in r:
        return "UPI_NETWORK_TIMEOUT"
    elif "Bank" in r or "Unavailable" in r:
        return "BANK_SERVER_UNAVAILABLE"
    elif "Limit" in r:
        return "TRANSACTION_LIMIT_EXCEEDED"
    elif "Insufficient" in r or "Declined" in r:
        if activity_score >= 0.70 and tenure >= 6:
            return "INSUFFICIENT_FUNDS_LOYAL_CUSTOMER"
        elif activity_score < 0.35:
            return "INSUFFICIENT_FUNDS_CHURN_RISK"
        else:
            return "INSUFFICIENT_FUNDS_STANDARD"
    else:
        return "GENERAL_PAYMENT_FAILURE"


def record_recovery_experience(
    db: Session,
    recovery_case_id: str,
    merchant_id: str,
    strategy: str,
    tool_invoked: str,
    tool_result: str,
    is_recovered: bool,
    recovered_amount_paise: int,
    attempt_count: int,
) -> Optional[RecoveryMemory]:
    """
    Persists a recovery outcome into adaptive agent memory strictly AFTER simulator outcome settles.
    Guarantees temporal integrity (no future leakage).
    """
    rec_case = (
        db.query(RecoveryCase)
        .filter(RecoveryCase.id == recovery_case_id, RecoveryCase.merchant_id == merchant_id)
        .first()
    )
    if not rec_case:
        return None

    payment = db.query(Payment).filter(Payment.id == rec_case.payment_id).first()
    if not payment:
        return None

    customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
    activity = customer.activity_score if customer else 0.5
    tenure = customer.tenure if customer else 1

    cluster = derive_context_cluster(
        failure_reason=payment.failure_reason or "",
        activity_score=activity,
        tenure=tenure,
    )

    mem_id = f"mem_{rec_case.id.replace('rec_', '')}_{attempt_count}_{str(uuid.uuid4())[:8]}"

    memory = RecoveryMemory(
        id=mem_id,
        merchant_id=merchant_id,
        recovery_case_id=rec_case.id,
        payment_id=payment.id,
        customer_id=payment.customer_id,
        failure_reason=payment.failure_reason or "Unknown",
        payment_method=payment.payment_method,
        ml_probability=rec_case.recovery_probability or 0.85,
        strategy_used=strategy,
        tool_invoked=tool_invoked,
        outcome_result=tool_result,
        is_recovered=is_recovered,
        recovered_amount_paise=recovered_amount_paise,
        attempt_count=attempt_count,
        context_cluster=cluster,
        memory_version=MEMORY_VERSION,
        created_at=datetime.now(timezone.utc),
    )
    db.add(memory)

    # Persist learning audit event
    audit_id = f"aud_mem_{mem_id}"
    db.add(
        AuditEvent(
            id=audit_id,
            merchant_id=merchant_id,
            event_type="AGENT_MEMORY_LEARNED",
            entity_id=memory.id,
            actor="adaptive_memory_engine_v1",
            metadata_json=f'{{"memory_id": "{mem_id}", "cluster": "{cluster}", "strategy": "{strategy}", "is_recovered": {str(is_recovered).lower()}, "recovered_amount": {recovered_amount_paise}, "memory_version": "{MEMORY_VERSION}", "demo": true}}',
            created_at=datetime.now(timezone.utc),
        )
    )

    db.commit()
    db.refresh(memory)
    return memory


def retrieve_relevant_experiences(
    db: Session,
    merchant_id: str,
    failure_reason: str,
    activity_score: float = 0.5,
    tenure: int = 1,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Bounded Memory Retrieval:
    Retrieves historical recovery experiences matching the customer context cluster
    and computes empirical strategy win-rates to guide adaptive reasoning.
    """
    cluster = derive_context_cluster(failure_reason, activity_score, tenure)

    # Query strictly merchant-isolated historical memory
    memories = (
        db.query(RecoveryMemory)
        .filter(
            RecoveryMemory.merchant_id == merchant_id,
            RecoveryMemory.context_cluster == cluster,
        )
        .order_by(RecoveryMemory.created_at.desc())
        .limit(limit)
        .all()
    )

    # Calculate empirical strategy performance for this context cluster
    stats = (
        db.query(
            RecoveryMemory.strategy_used,
            func.count(RecoveryMemory.id).label("total_attempts"),
            func.sum(func.cast(RecoveryMemory.is_recovered, Integer)).label("successful_recoveries"),
            func.sum(RecoveryMemory.recovered_amount_paise).label("total_recovered_paise"),
        )
        .filter(
            RecoveryMemory.merchant_id == merchant_id,
            RecoveryMemory.context_cluster == cluster,
        )
        .group_by(RecoveryMemory.strategy_used)
        .all()
    )

    strategy_conversion = {}
    for strat, total, success, amt in stats:
        tot_cnt = total or 0
        succ_cnt = success or 0
        rate = (succ_cnt / tot_cnt) if tot_cnt > 0 else 0.0
        strategy_conversion[strat] = {
            "attempts": tot_cnt,
            "successes": succ_cnt,
            "win_rate": round(rate, 2),
            "win_rate_percentage": round(rate * 100, 1),
            "total_recovered_paise": amt or 0,
            "total_recovered_inr": round((amt or 0) / 100, 2),
        }

    items = []
    for m in memories:
        items.append({
            "id": m.id,
            "recovery_case_id": m.recovery_case_id,
            "customer_id": m.customer_id,
            "failure_reason": m.failure_reason,
            "strategy_used": m.strategy_used,
            "tool_invoked": m.tool_invoked,
            "outcome_result": m.outcome_result,
            "is_recovered": m.is_recovered,
            "recovered_amount_inr": round(m.recovered_amount_paise / 100, 2),
            "created_at": m.created_at.isoformat(),
        })

    return {
        "context_cluster": cluster,
        "memory_version": MEMORY_VERSION,
        "sample_size": len(items),
        "strategy_performance": strategy_conversion,
        "recent_experiences": items,
    }


def get_strategy_performance_analytics(
    db: Session,
    merchant_id: str,
) -> List[Dict[str, Any]]:
    """
    Aggregates overall strategy performance from actual simulator outcome memories.
    """
    stats = (
        db.query(
            RecoveryMemory.strategy_used,
            func.count(RecoveryMemory.id).label("total_attempts"),
            func.sum(func.cast(RecoveryMemory.is_recovered, Integer)).label("successful_recoveries"),
            func.sum(RecoveryMemory.recovered_amount_paise).label("total_recovered_paise"),
            func.avg(RecoveryMemory.ml_probability).label("avg_ml_probability"),
        )
        .filter(RecoveryMemory.merchant_id == merchant_id)
        .group_by(RecoveryMemory.strategy_used)
        .all()
    )

    results = []
    for strat, total, success, amt, avg_prob in stats:
        tot_cnt = total or 0
        succ_cnt = success or 0
        rate = (succ_cnt / tot_cnt * 100) if tot_cnt > 0 else 0.0
        results.append({
            "strategy": strat,
            "label": strat.replace("_", " ").title(),
            "total_attempts": tot_cnt,
            "successful_recoveries": succ_cnt,
            "recovery_rate": round(rate, 1),
            "recovered_amount_paise": amt or 0,
            "recovered_amount_inr": round((amt or 0) / 100, 2),
            "avg_ml_probability": round(float(avg_prob or 0.85), 3),
        })

    results.sort(key=lambda x: x["recovered_amount_paise"], reverse=True)
    return results


def get_memory_status(db: Session, merchant_id: str) -> Dict[str, Any]:
    """
    Returns adaptive memory status, active learning events, and cluster distribution.
    """
    total_memories = db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).count()
    successful_memories = (
        db.query(RecoveryMemory)
        .filter(RecoveryMemory.merchant_id == merchant_id, RecoveryMemory.is_recovered == True)
        .count()
    )
    latest_event = (
        db.query(RecoveryMemory)
        .filter(RecoveryMemory.merchant_id == merchant_id)
        .order_by(RecoveryMemory.created_at.desc())
        .first()
    )

    clusters = (
        db.query(
            RecoveryMemory.context_cluster,
            func.count(RecoveryMemory.id).label("count"),
        )
        .filter(RecoveryMemory.merchant_id == merchant_id)
        .group_by(RecoveryMemory.context_cluster)
        .all()
    )

    return {
        "memory_version": MEMORY_VERSION,
        "total_memory_records": total_memories,
        "successful_learning_events": successful_memories,
        "last_learned_at": latest_event.created_at.isoformat() if latest_event else None,
        "context_clusters_tracked": [{"cluster": c[0], "count": c[1]} for c in clusters],
        "demo": True,
    }
