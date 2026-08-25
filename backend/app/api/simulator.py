from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.schemas.simulator import (
    CaseSimulationRequest,
    BatchSimulationRequest,
    CaseSimulationResponse,
    BatchSimulationResponse,
    SimulatorMetricsResponse,
    SimulatorResetResponse,
)
from app.services.simulator_service import (
    simulate_case_recovery,
    run_batch_simulation,
    get_simulator_metrics,
    reset_simulator_state,
)

router = APIRouter(prefix="/simulator", tags=["Autonomous Payment & Recovery Simulator"])


@router.post("/case/{recovery_case_id}", response_model=CaseSimulationResponse)
async def simulate_case_endpoint(
    recovery_case_id: str,
    body: CaseSimulationRequest = CaseSimulationRequest(),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Executes the autonomous recovery loop for a single case with optional demo scenario controls.
    """
    try:
        res = simulate_case_recovery(
            db=db,
            recovery_case_id=recovery_case_id,
            merchant_id=merchant.merchant_id,
            scenario=body.scenario,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/run", response_model=BatchSimulationResponse)
async def run_batch_simulation_endpoint(
    body: BatchSimulationRequest = BatchSimulationRequest(),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Executes autonomous recovery simulation across an active cohort of cases.
    """
    try:
        res = run_batch_simulation(
            db=db,
            merchant_id=merchant.merchant_id,
            batch_size=body.batch_size,
            scenario=body.scenario,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch simulation error: {str(e)}")


@router.get("/status", response_model=SimulatorMetricsResponse)
async def get_simulator_status_endpoint(
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns aggregate simulator status, active cohort metrics, and recovered vs at-risk totals.
    """
    try:
        return get_simulator_metrics(db=db, merchant_id=merchant.merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching simulator status: {str(e)}")


@router.post("/reset", response_model=SimulatorResetResponse)
async def reset_simulator_endpoint(
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Resets demo simulation state to baseline for clean re-runs.
    """
    try:
        return reset_simulator_state(db=db, merchant_id=merchant.merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting simulator: {str(e)}")
