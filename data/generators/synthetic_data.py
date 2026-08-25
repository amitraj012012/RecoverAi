import random
import math
import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Ensure reproducible deterministic generation
RANDOM_SEED = 42

PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]
FAILURE_REASONS = [
    "Card Declined (Insufficient Funds)",
    "UPI Network Timeout",
    "Card Expired",
    "Bank Server Unavailable",
    "Authentication Failed (OTP Timeout)",
    "Transaction Exceeded Limit",
]

# Base latent recoverability log-odds by failure reason
REASON_LOG_ODDS = {
    "UPI Network Timeout": 1.2,
    "Bank Server Unavailable": 1.0,
    "Card Expired": 0.8,
    "Authentication Failed (OTP Timeout)": 0.6,
    "Card Declined (Insufficient Funds)": 0.1,
    "Transaction Exceeded Limit": -0.5,
}

COMPANY_PREFIXES = [
    "Apex", "Cloud", "Streamline", "Nova", "GrowthPulse", "Nexus", "Vertex", "Quantum",
    "BlueSky", "Horizon", "Agile", "Elevate", "Prime", "Synapse", "Beacon", "Cobalt",
]

COMPANY_SUFFIXES = [
    "SaaS", "Technologies", "Pro", "Academy", "Lab", "Marketing", "Logistics", "Digital",
    "Ventures", "Analytics", "Solutions", "Platform", "Studios", "Software",
]


def generate_company_name(idx: int) -> str:
    p = COMPANY_PREFIXES[idx % len(COMPANY_PREFIXES)]
    s = COMPANY_SUFFIXES[(idx // len(COMPANY_PREFIXES)) % len(COMPANY_SUFFIXES)]
    return f"{p} {s}"


def simulate_stochastic_recovery_outcome(
    activity_score: float,
    tenure: int,
    prior_success_count: int,
    prior_fail_count: int,
    failure_reason: str,
    payment_method: str,
) -> int:
    """
    Simulates an independent, stochastic recovery outcome after a payment failure.
    Uses continuous latent log-odds + Gaussian noise + Bernoulli sampling.
    No hard-coded deterministic threshold rules.
    """
    total_prior = prior_success_count + prior_fail_count
    hist_rate = (prior_success_count / total_prior) if total_prior > 0 else 0.5

    # Continuous latent logit
    z = 0.2  # baseline intercept
    z += 1.5 * (activity_score - 0.5)  # engagement effect
    z += 0.4 * math.log(max(1, tenure))  # tenure log-effect
    z += 1.2 * (hist_rate - 0.5)  # historical payment reliability
    z -= 0.3 * min(5, prior_fail_count)  # cumulative prior failure penalty
    z += REASON_LOG_ODDS.get(failure_reason, 0.0)  # failure type effect

    # Method effect
    if payment_method == "upi":
        z += 0.2
    elif payment_method == "card":
        z += 0.1

    # Add unobserved stochastic consumer friction (Gaussian noise)
    noise = random.gauss(0.0, 0.85)
    z += noise

    # Logistic transformation
    p_latent = 1.0 / (1.0 + math.exp(-z))

    # Bernoulli sample
    return 1 if random.random() < p_latent else 0


def generate_synthetic_dataset(
    num_customers: int = 1200,
    target_min_payments: int = 10000,
    merchant_id: str = "merchant_default",
    seed: int = RANDOM_SEED,
) -> Dict[str, Any]:
    """
    Generates a realistic, deterministic synthetic dataset with stochastic recovery outcomes.
    """
    random.seed(seed)
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    customers: List[Dict[str, Any]] = []
    payments: List[Dict[str, Any]] = []
    recovery_cases: List[Dict[str, Any]] = []
    seen_customer_ids = set()

    # 1. Guarantee Hackathon Demo Case: C1024
    # Customer C1024: 18 attempts, 17 successful, 1 failed (Card declined), high activity (0.88), tenure 18mo, ₹1,999
    c1024 = {
        "id": "C1024",
        "merchant_id": merchant_id,
        "demo_name": "Enterprise Cloud SaaS (C1024)",
        "subscription_value": 199900,  # ₹1,999
        "tenure": 18,
        "activity_score": 0.88,
        "created_at": (base_time - timedelta(days=18 * 30)).isoformat(),
    }
    customers.append(c1024)
    seen_customer_ids.add("C1024")

    # Generate 17 successful historical monthly payments for C1024
    for m in range(17):
        pay_time = base_time - timedelta(days=(17 - m) * 30 + random.randint(1, 3))
        payments.append({
            "id": f"pay_c1024_hist_{m+1}",
            "merchant_id": merchant_id,
            "customer_id": "C1024",
            "amount": 199900,
            "currency": "INR",
            "payment_method": "card",
            "status": "success",
            "failure_reason": None,
            "created_at": pay_time.isoformat(),
        })

    # Generate the 18th payment: Failed card renewal
    fail_time_c1024 = base_time + timedelta(hours=random.randint(1, 24))
    outcome_c1024 = simulate_stochastic_recovery_outcome(
        activity_score=0.88,
        tenure=18,
        prior_success_count=17,
        prior_fail_count=0,
        failure_reason="Card Declined (Insufficient Funds)",
        payment_method="card",
    )

    payments.append({
        "id": "pay_c1024_fail",
        "merchant_id": merchant_id,
        "customer_id": "C1024",
        "amount": 199900,
        "currency": "INR",
        "payment_method": "card",
        "status": "failed",
        "failure_reason": "Card Declined (Insufficient Funds)",
        "created_at": fail_time_c1024.isoformat(),
    })

    recovery_cases.append({
        "id": "rec_c1024_fail",
        "merchant_id": merchant_id,
        "payment_id": "pay_c1024_fail",
        "status": "FAILED",
        "attempt_count": 0,
        "expected_revenue": 199900,
        "recovered_amount": 0,
        "simulated_recovery_outcome": outcome_c1024,
        "created_at": fail_time_c1024.isoformat(),
    })

    # 2. Generate remaining customer personas
    subscription_plans = [99900, 199900, 499900, 999900, 2499900, 4999900]

    cust_index = 1
    while len(customers) < num_customers:
        cust_index += 1
        cid = f"C{1000 + cust_index}"
        if cid in seen_customer_ids:
            continue
        seen_customer_ids.add(cid)

        persona_type = random.choices(
            ["high_loyalty", "upi_user", "expired_card", "high_value", "churn_risk", "standard"],
            weights=[0.35, 0.25, 0.15, 0.10, 0.08, 0.07],
            k=1,
        )[0]

        if persona_type == "high_loyalty":
            tenure = random.randint(12, 36)
            sub_val = random.choice([99900, 199900, 499900])
            activity = round(random.uniform(0.75, 0.98), 2)
            failure_rate = 0.04
        elif persona_type == "upi_user":
            tenure = random.randint(6, 24)
            sub_val = random.choice([99900, 199900])
            activity = round(random.uniform(0.60, 0.90), 2)
            failure_rate = 0.08
        elif persona_type == "expired_card":
            tenure = random.randint(12, 24)
            sub_val = random.choice([199900, 499900, 999900])
            activity = round(random.uniform(0.50, 0.80), 2)
            failure_rate = 0.15
        elif persona_type == "high_value":
            tenure = random.randint(8, 30)
            sub_val = random.choice([2499900, 4999900])
            activity = round(random.uniform(0.70, 0.95), 2)
            failure_rate = 0.06
        elif persona_type == "churn_risk":
            tenure = random.randint(1, 4)
            sub_val = random.choice([99900, 199900])
            activity = round(random.uniform(0.10, 0.35), 2)
            failure_rate = 0.45
        else:
            tenure = random.randint(3, 15)
            sub_val = random.choice(subscription_plans)
            activity = round(random.uniform(0.40, 0.70), 2)
            failure_rate = 0.10

        cust_created = base_time - timedelta(days=tenure * 30 + random.randint(1, 20))
        cust = {
            "id": cid,
            "merchant_id": merchant_id,
            "demo_name": f"{generate_company_name(cust_index)} ({cid})",
            "subscription_value": sub_val,
            "tenure": tenure,
            "activity_score": activity,
            "created_at": cust_created.isoformat(),
        }
        customers.append(cust)

        # Track rolling historical counts for this customer
        prior_success = 0
        prior_fail = 0

        # Generate payment history for this customer
        num_attempts = max(tenure, random.randint(8, 14))
        for a in range(num_attempts):
            pay_date = cust_created + timedelta(days=(a + 1) * 30 + random.randint(-2, 2))
            if pay_date > base_time + timedelta(days=30):
                continue

            is_failed = random.random() < failure_rate
            pid = f"pay_{cid.lower()}_{a+1}"

            if persona_type == "upi_user":
                method = "upi"
            elif persona_type == "high_value":
                method = "card" if random.random() < 0.8 else "netbanking"
            else:
                method = random.choice(PAYMENT_METHODS)

            if is_failed:
                if persona_type == "upi_user":
                    reason = "UPI Network Timeout"
                elif persona_type == "expired_card":
                    reason = "Card Expired"
                else:
                    reason = random.choice(FAILURE_REASONS)

                status = "failed"
                rec_case_id = f"rec_{cid.lower()}_{a+1}"

                # Stochastic outcome simulation
                outcome = simulate_stochastic_recovery_outcome(
                    activity_score=activity,
                    tenure=tenure,
                    prior_success_count=prior_success,
                    prior_fail_count=prior_fail,
                    failure_reason=reason,
                    payment_method=method,
                )

                recovery_cases.append({
                    "id": rec_case_id,
                    "merchant_id": merchant_id,
                    "payment_id": pid,
                    "status": "FAILED",
                    "attempt_count": 0,
                    "expected_revenue": sub_val,
                    "recovered_amount": 0,
                    "simulated_recovery_outcome": outcome,
                    "created_at": pay_date.isoformat(),
                })
                prior_fail += 1
            else:
                reason = None
                status = "success"
                prior_success += 1

            payments.append({
                "id": pid,
                "merchant_id": merchant_id,
                "customer_id": cid,
                "amount": sub_val,
                "currency": "INR",
                "payment_method": method,
                "status": status,
                "failure_reason": reason,
                "created_at": pay_date.isoformat(),
            })

    # Ensure we have >= target_min_payments
    extra_count = 0
    while len(payments) < target_min_payments:
        extra_count += 1
        cust = random.choice(customers)
        cid = cust["id"]
        pid = f"pay_{cid.lower()}_extra_{extra_count}"
        method = random.choice(PAYMENT_METHODS)
        is_failed = random.random() < 0.08
        sub_val = cust["subscription_value"]
        pay_date = base_time - timedelta(days=random.randint(1, 180))

        if is_failed:
            status = "failed"
            reason = random.choice(FAILURE_REASONS)
            rec_case_id = f"rec_{cid.lower()}_extra_{extra_count}"
            outcome = simulate_stochastic_recovery_outcome(
                activity_score=cust["activity_score"],
                tenure=cust["tenure"],
                prior_success_count=5,
                prior_fail_count=1,
                failure_reason=reason,
                payment_method=method,
            )
            recovery_cases.append({
                "id": rec_case_id,
                "merchant_id": merchant_id,
                "payment_id": pid,
                "status": "FAILED",
                "attempt_count": 0,
                "expected_revenue": sub_val,
                "recovered_amount": 0,
                "simulated_recovery_outcome": outcome,
                "created_at": pay_date.isoformat(),
            })
        else:
            status = "success"
            reason = None

        payments.append({
            "id": pid,
            "merchant_id": merchant_id,
            "customer_id": cid,
            "amount": sub_val,
            "currency": "INR",
            "payment_method": method,
            "status": status,
            "failure_reason": reason,
            "created_at": pay_date.isoformat(),
        })

    total_recovered_outcomes = sum(rc["simulated_recovery_outcome"] for rc in recovery_cases)

    return {
        "metadata": {
            "seed": seed,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_customers": len(customers),
            "total_payments": len(payments),
            "total_failed_payments": len(recovery_cases),
            "total_recovery_outcomes_positive": total_recovered_outcomes,
            "total_recovery_outcomes_negative": len(recovery_cases) - total_recovered_outcomes,
            "total_revenue_at_risk_paise": sum(p["amount"] for p in payments if p["status"] == "failed"),
        },
        "customers": customers,
        "payments": payments,
        "recovery_cases": recovery_cases,
    }


def save_dataset_to_disk(dataset: Dict[str, Any], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"Dataset successfully saved to {output_path}")


if __name__ == "__main__":
    dataset = generate_synthetic_dataset(num_customers=1200, target_min_payments=10000)
    meta = dataset["metadata"]
    print(f"Generated {meta['total_customers']} customers, {meta['total_payments']} payments ({meta['total_failed_payments']} failed).")
    print(f"Recovery outcomes: {meta['total_recovery_outcomes_positive']} Recovered, {meta['total_recovery_outcomes_negative']} Unrecovered.")
    save_dataset_to_disk(dataset, "data/seed/payments_seed.json")
