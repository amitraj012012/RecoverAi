from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.schemas.ml_prediction import PredictRecoveryRequest, PredictRecoveryResponse
from app.services.ml_prediction_service import (
    predict_recovery,
    populate_all_recovery_probabilities,
    get_metadata,
)

router = APIRouter(prefix="/ai", tags=["ML Recovery Prediction"])


@router.post("/predict-recovery", response_model=PredictRecoveryResponse)
async def predict_recovery_endpoint(
    req: PredictRecoveryRequest,
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Predicts the recovery probability for a failed payment using the trained ML model.
    """
    if not req.payment_id and not req.recovery_case_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'payment_id' or 'recovery_case_id' must be provided.",
        )

    try:
        res = predict_recovery(
            db,
            payment_id=req.payment_id,
            recovery_case_id=req.recovery_case_id,
            merchant_id=merchant.merchant_id,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/batch-predict")
async def batch_predict_endpoint(
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Batch computes ML recovery probabilities for all recovery cases in the merchant workspace.
    """
    count = populate_all_recovery_probabilities(db, merchant_id=merchant.merchant_id)
    return {"status": "success", "updated_cases": count}


@router.get("/model-info")
async def get_model_info_endpoint():
    """
    Returns metadata about the active ML recovery prediction model.
    """
    return get_metadata()
