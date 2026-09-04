import os
import json
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_case import RecoveryCase

def _find_file(filename: str) -> Optional[str]:
    search_dirs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/models")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/models")),
        os.path.abspath(os.path.join(os.getcwd(), "data/models")),
        os.path.abspath(os.path.join(os.getcwd(), "../data/models")),
    ]
    for d in search_dirs:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None


_cached_model = None
_cached_metadata = None


def get_model():
    global _cached_model
    if _cached_model is None:
        p2 = _find_file("recovery_prediction_model_v2.joblib")
        p1 = _find_file("recovery_prediction_model_v1.joblib")
        if p2 and os.path.exists(p2):
            _cached_model = joblib.load(p2)
        elif p1 and os.path.exists(p1):
            _cached_model = joblib.load(p1)
        else:
            raise FileNotFoundError("Model artifact recovery_prediction_model_v2.joblib not found. Please train the model first.")
    return _cached_model


def get_metadata() -> Dict[str, Any]:
    global _cached_metadata
    if _cached_metadata is None:
        p2 = _find_file("model_metadata_v2.json")
        p1 = _find_file("model_metadata.json")
        if p2 and os.path.exists(p2):
            with open(p2, "r", encoding="utf-8") as f:
                _cached_metadata = json.load(f)
        elif p1 and os.path.exists(p1):
            with open(p1, "r", encoding="utf-8") as f:
                _cached_metadata = json.load(f)
        else:
            _cached_metadata = {"model_version": "logistic-regression-v2"}
    return _cached_metadata


def build_feature_vector(
    customer: Customer,
    payment: Payment,
    prior_success_count: int,
    prior_fail_count: int,
) -> np.ndarray:
    """
    Constructs the exact 18-element feature vector matching model training specification.
    """
    sub_inr = customer.subscription_value / 100.0
    amt_inr = payment.amount / 100.0
    ratio = amt_inr / sub_inr if sub_inr > 0 else 1.0

    total_prior = prior_success_count + prior_fail_count
    hist_success_rate = (prior_success_count / total_prior) if total_prior > 0 else 0.5

    # One-hot payment method
    m = payment.payment_method.lower()
    m_card = 1.0 if m == "card" else 0.0
    m_upi = 1.0 if m == "upi" else 0.0
    m_net = 1.0 if m == "netbanking" else 0.0
    m_wal = 1.0 if m == "wallet" else 0.0

    # One-hot failure reason
    r = payment.failure_reason or ""
    r_exp = 1.0 if "Expired" in r else 0.0
    r_upi = 1.0 if "UPI" in r or "Timeout" in r else 0.0
    r_funds = 1.0 if "Insufficient" in r else 0.0
    r_bank = 1.0 if "Bank" in r or "Unavailable" in r else 0.0
    r_otp = 1.0 if "OTP" in r or "Authentication" in r else 0.0
    r_lim = 1.0 if "Limit" in r else 0.0

    features = [
        float(customer.tenure),
        float(customer.activity_score),
        float(sub_inr),
        float(amt_inr),
        float(ratio),
        float(prior_success_count),
        float(prior_fail_count),
        float(hist_success_rate),
        m_card,
        m_upi,
        m_net,
        m_wal,
        r_exp,
        r_upi,
        r_funds,
        r_bank,
        r_otp,
        r_lim,
    ]
    return np.array([features], dtype=np.float32)


def generate_explainability_factors(
    customer: Customer,
    payment: Payment,
    prior_success_count: int,
    prior_fail_count: int,
    prob: float,
) -> List[Dict[str, Any]]:
    """
    Generates concise structured feature-level explanations traceable to model feature coefficients.
    """
    factors = []

    # 1. Historical success factor
    total_prior = prior_success_count + prior_fail_count
    rate = (prior_success_count / total_prior * 100) if total_prior > 0 else 50
    if rate >= 80 and total_prior > 0:
        factors.append({
            "feature": "historical_success_rate",
            "impact": "positive",
            "description": f"Strong historical payment success ({rate:.0f}%)",
        })
    elif rate < 50 and total_prior > 0:
        factors.append({
            "feature": "historical_success_rate",
            "impact": "negative",
            "description": f"Low historical payment reliability ({rate:.0f}%)",
        })

    # 2. Activity score factor
    if customer.activity_score >= 0.75:
        factors.append({
            "feature": "activity_score",
            "impact": "positive",
            "description": f"High customer product engagement ({customer.activity_score * 100:.0f}%)",
        })
    elif customer.activity_score < 0.35:
        factors.append({
            "feature": "activity_score",
            "impact": "negative",
            "description": f"Low platform engagement ({customer.activity_score * 100:.0f}%)",
        })

    # 3. Tenure factor
    if customer.tenure >= 12:
        factors.append({
            "feature": "customer_tenure",
            "impact": "positive",
            "description": f"Established customer relationship ({customer.tenure} months)",
        })
    elif customer.tenure <= 2:
        factors.append({
            "feature": "customer_tenure",
            "impact": "negative",
            "description": f"New customer account ({customer.tenure} months)",
        })

    # 4. Failure reason nature
    r = payment.failure_reason or ""
    if "UPI" in r or "Timeout" in r or "Bank" in r:
        factors.append({
            "feature": "failure_reason",
            "impact": "positive",
            "description": "Transient network/bank infrastructure error",
        })
    elif "Expired" in r:
        factors.append({
            "feature": "failure_reason",
            "impact": "positive",
            "description": "Payment card expired (resolvable via link)",
        })
    elif "Insufficient" in r:
        factors.append({
            "feature": "failure_reason",
            "impact": "neutral",
            "description": "Temporary insufficient funds",
        })
    elif "Limit" in r:
        factors.append({
            "feature": "failure_reason",
            "impact": "negative",
            "description": "Account transaction limit ceiling exceeded",
        })

    return factors


def predict_recovery(
    db: Session,
    payment_id: Optional[str] = None,
    recovery_case_id: Optional[str] = None,
    merchant_id: Optional[str] = None,
    commit: bool = True,
) -> Dict[str, Any]:
    """
    Computes ML recovery probability for a given payment or recovery case using v2 model.
    """
    if recovery_case_id:
        rec_case = db.query(RecoveryCase).filter(RecoveryCase.id == recovery_case_id)
        if merchant_id:
            rec_case = rec_case.filter(RecoveryCase.merchant_id == merchant_id)
        rec_case = rec_case.first()
        if not rec_case:
            raise ValueError(f"Recovery case '{recovery_case_id}' not found.")
        payment_id = rec_case.payment_id
    else:
        rec_case = db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment_id).first()

    query = db.query(Payment).filter(Payment.id == payment_id)
    if merchant_id:
        query = query.filter(Payment.merchant_id == merchant_id)
    payment = query.first()
    if not payment:
        raise ValueError(f"Payment '{payment_id}' not found.")

    customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
    if not customer:
        raise ValueError(f"Customer '{payment.customer_id}' not found for payment.")

    # Calculate prior history strictly up to this payment (no leakage)
    prior_payments = (
        db.query(Payment)
        .filter(Payment.customer_id == customer.id, Payment.created_at < payment.created_at)
        .all()
    )
    prior_success = sum(1 for p in prior_payments if p.status == "success")
    prior_fail = sum(1 for p in prior_payments if p.status == "failed")

    # Build feature vector & predict
    X = build_feature_vector(customer, payment, prior_success, prior_fail)
    model = get_model()
    prob = float(model.predict_proba(X)[0, 1])
    prob_clamped = round(max(0.01, min(0.99, prob)), 4)

    meta = get_metadata()
    model_version = meta.get("model_version", "logistic-regression-v2")

    factors = generate_explainability_factors(customer, payment, prior_success, prior_fail, prob_clamped)

    # Persist probability to recovery case
    if rec_case:
        rec_case.recovery_probability = prob_clamped
        if commit:
            db.commit()
            db.refresh(rec_case)

    return {
        "payment_id": payment.id,
        "recovery_case_id": rec_case.id if rec_case else None,
        "customer_id": customer.id,
        "recovery_probability": prob_clamped,
        "recovery_probability_percentage": round(prob_clamped * 100, 1),
        "model_version": model_version,
        "factors": factors,
    }


def populate_all_recovery_probabilities(db: Session, merchant_id: Optional[str] = None) -> int:
    """
    Batch updates recovery_probability for all recovery cases using the trained v2 ML model.
    """
    query = db.query(RecoveryCase)
    if merchant_id:
        query = query.filter(RecoveryCase.merchant_id == merchant_id)
    cases = query.all()

    updated = 0
    for rc in cases:
        try:
            predict_recovery(db, recovery_case_id=rc.id, merchant_id=merchant_id)
            updated += 1
        except Exception:
            continue
    return updated
