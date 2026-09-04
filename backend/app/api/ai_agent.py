import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.audit_event import AuditEvent
from app.schemas.ai_agent import (
    RecoveryExecutionResponse,
    AiDecisionLogItem,
    RecoveryCaseWorkflowResponse,
)
from app.services.ai_agent_service import execute_recovery_workflow

router = APIRouter(prefix="/ai", tags=["AI Recovery Agent & Decisions"])


@router.post("/recover/{recovery_case_id}", response_model=RecoveryExecutionResponse)
async def recover_case_endpoint(
    recovery_case_id: str,
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Executes the bounded AI Recovery Agent workflow on an active recovery case.
    """
    try:
        res = execute_recovery_workflow(
            db=db,
            recovery_case_id=recovery_case_id,
            merchant_id=merchant.merchant_id,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recovery execution error: {str(e)}")


@router.get("/decisions", response_model=List[AiDecisionLogItem])
async def get_ai_decisions_endpoint(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns audit trail logs of AI decisions and tool executions for the merchant.
    Excludes memory-learning log events (AGENT_MEMORY_LEARNED).
    """
    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.merchant_id == merchant.merchant_id,
            AuditEvent.event_type.like("RECOVERY_%"),
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    # Fallback to any merchant audit event excluding memory-learning records
    if not events:
        events = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.merchant_id == merchant.merchant_id,
                AuditEvent.event_type != "AGENT_MEMORY_LEARNED",
            )
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    items = []
    for ev in events:
        meta = {}
        if ev.metadata_json:
            try:
                meta = json.loads(ev.metadata_json)
            except Exception:
                meta = {"raw": ev.metadata_json}
        items.append(
            AiDecisionLogItem(
                id=ev.id,
                recovery_case_id=ev.entity_id,
                event_type=ev.event_type,
                actor=ev.actor,
                metadata=meta,
                created_at=ev.created_at,
            )
        )
    return items


@router.get("/recovery-case/{recovery_case_id}/workflow", response_model=RecoveryCaseWorkflowResponse)
async def get_recovery_case_workflow_endpoint(
    recovery_case_id: str,
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns the complete end-to-end lifecycle history (Payment -> ML Probability -> AI Decisions -> Actions -> Audit Events) for a recovery case.
    """
    rec_case = (
        db.query(RecoveryCase)
        .filter(RecoveryCase.id == recovery_case_id, RecoveryCase.merchant_id == merchant.merchant_id)
        .first()
    )
    if not rec_case:
        raise HTTPException(status_code=404, detail=f"Recovery case '{recovery_case_id}' not found.")

    payment = db.query(Payment).filter(Payment.id == rec_case.payment_id).first()

    audit_records = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_id == recovery_case_id, AuditEvent.merchant_id == merchant.merchant_id)
        .order_by(AuditEvent.created_at.asc())
        .all()
    )

    actions_list = []
    for a in rec_case.actions:
        meta = {}
        if a.metadata_json:
            try:
                meta = json.loads(a.metadata_json)
            except Exception:
                meta = {}
        actions_list.append({
            "id": a.id,
            "action_type": a.action_type,
            "agent_reason": a.agent_reason,
            "result": a.result,
            "metadata": meta,
            "executed_at": a.executed_at.isoformat(),
        })

    audit_list = []
    for ev in audit_records:
        meta = {}
        if ev.metadata_json:
            try:
                meta = json.loads(ev.metadata_json)
            except Exception:
                meta = {}
        audit_list.append({
            "id": ev.id,
            "event_type": ev.event_type,
            "actor": ev.actor,
            "metadata": meta,
            "created_at": ev.created_at.isoformat(),
        })

    return RecoveryCaseWorkflowResponse(
        case_id=rec_case.id,
        payment_id=rec_case.payment_id,
        customer_id=payment.customer_id if payment else "UNKNOWN",
        amount_inr=round((rec_case.expected_revenue or 0) / 100, 2),
        failure_reason=payment.failure_reason if payment else None,
        status=rec_case.status,
        ml_probability=rec_case.recovery_probability,
        selected_strategy=rec_case.selected_strategy,
        attempt_count=rec_case.attempt_count,
        recovered_amount_inr=round(rec_case.recovered_amount / 100, 2),
        actions=actions_list,
        audit_events=audit_list,
    )
