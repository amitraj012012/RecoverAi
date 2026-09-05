import random
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

# Explicit Allowlisted Tool Registry (Strictly 6 Tools)
ALLOWED_TOOLS = [
    "payment_retry_simulator",
    "payment_link_simulator",
    "payment_method_update_simulator",
    "customer_notification_simulator",
    "incentive_offer_simulator",
    "human_escalation_tool",
]

# Synthetic simulator calibration parameters
# Maps active recovery strategies to baseline action-channel efficacy coefficients.
STRATEGY_EFFICACY = {
    "RETRY_PAYMENT": 0.70,
    "CREATE_PAYMENT_LINK": 0.55,
    "ALTERNATE_PAYMENT_METHOD": 0.45,
    "OFFER_INCENTIVE": 0.40,
    "SEND_REMINDER": 0.35,
}
# Note: ESCALATE_TO_HUMAN is intentionally excluded from STRATEGY_EFFICACY as it never simulates recovery.


def calculate_effective_recovery_probability(
    ml_probability: float,
    strategy: str,
    attempt_count: int = 0,
) -> float:
    """
    Computes bounded effective single-attempt conversion probability:
    Peff = ML_probability * strategy_efficacy * attempt_decay
    Where attempt_decay = 0.85 ** attempt_count
    Clamped strictly to [0.0, 1.0].
    """
    if strategy not in STRATEGY_EFFICACY or strategy == "ESCALATE_TO_HUMAN":
        return 0.0

    efficacy = STRATEGY_EFFICACY[strategy]
    decay = 0.85 ** max(0, attempt_count)
    peff = ml_probability * efficacy * decay
    return float(max(0.0, min(1.0, peff)))


def execute_payment_retry_simulator(
    case_id: str,
    payment_id: str,
    amount_paise: int,
    ml_probability: float,
    attempt_count: int = 0,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates automated payment retry against simulated payment gateway.
    Outcome reflects effective probability (ML propensity * gateway efficacy * decay).
    """
    peff = calculate_effective_recovery_probability(ml_probability, "RETRY_PAYMENT", attempt_count)
    is_success = random.random() < peff
    result_status = "SUCCESS" if is_success else "FAILED"

    metadata = {
        "simulator": "payment_retry_simulator",
        "simulated_gateway_ref": f"sim_tx_{case_id}_{random.randint(1000, 9999)}",
        "attempt_timestamp": datetime.now(timezone.utc).isoformat(),
        "amount_paise": amount_paise,
        "ml_probability": round(ml_probability, 4),
        "effective_probability": round(peff, 4),
        "attempt_count": attempt_count,
        "gateway_response": "200_OK_CHARGED" if is_success else "DECLINED_GATEWAY_REJECT",
        "demo": True,
    }
    return result_status, metadata, is_success


def execute_payment_link_simulator(
    case_id: str,
    payment_id: str,
    customer_id: str,
    amount_paise: int,
    ml_probability: float,
    attempt_count: int = 0,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates generating a secure simulated payment link dispatched to the customer.
    Conversion reflects effective probability (ML propensity * link efficacy * decay).
    """
    link_id = f"plink_sim_{case_id.replace('rec_', '')}"
    simulated_url = f"https://pay.recoverai.demo/link/{link_id}"

    peff = calculate_effective_recovery_probability(ml_probability, "CREATE_PAYMENT_LINK", attempt_count)
    is_success = random.random() < peff
    result_status = "SUCCESS" if is_success else "PENDING_CUSTOMER_ACTION"

    metadata = {
        "simulator": "payment_link_simulator",
        "simulated_payment_link": simulated_url,
        "dispatched_channel": "WhatsApp + Email (Simulated)",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "ml_probability": round(ml_probability, 4),
        "effective_probability": round(peff, 4),
        "attempt_count": attempt_count,
        "demo": True,
    }
    return result_status, metadata, is_success


def execute_payment_method_update_simulator(
    case_id: str,
    customer_id: str,
    amount_paise: int,
    ml_probability: float,
    attempt_count: int = 0,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates prompting customer to provide alternate payment method (e.g. UPI / Netbanking).
    """
    peff = calculate_effective_recovery_probability(ml_probability, "ALTERNATE_PAYMENT_METHOD", attempt_count)
    is_success = random.random() < peff
    result_status = "SUCCESS" if is_success else "PENDING_CUSTOMER_ACTION"

    metadata = {
        "simulator": "payment_method_update_simulator",
        "alternate_method_requested": "UPI / AutoPay",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "ml_probability": round(ml_probability, 4),
        "effective_probability": round(peff, 4),
        "attempt_count": attempt_count,
        "demo": True,
    }
    return result_status, metadata, is_success


def execute_customer_notification_simulator(
    case_id: str,
    customer_id: str,
    amount_paise: int,
    ml_probability: float = 0.0,
    attempt_count: int = 0,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates sending friendly personalized reminder notification (SMS / In-App Banner).
    Dispatching a reminder informs the customer and leaves the case in an actionable,
    pending state (ACTION_EXECUTED) awaiting customer payment. It does not mark immediate recovery.
    """
    metadata = {
        "simulator": "customer_notification_simulator",
        "channel": "SMS / In-App Banner",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "ml_probability": round(ml_probability, 4),
        "effective_probability": 0.0,  # Notification dispatch is informational, not immediate settlement
        "attempt_count": attempt_count,
        "demo": True,
    }
    return "NOTIFICATION_DISPATCHED", metadata, False


def execute_incentive_offer_simulator(
    case_id: str,
    customer_id: str,
    amount_paise: int,
    ml_probability: float,
    attempt_count: int = 0,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates applying dynamic incentive (e.g., 10% discount on renewal).
    """
    peff = calculate_effective_recovery_probability(ml_probability, "OFFER_INCENTIVE", attempt_count)
    is_success = random.random() < peff
    result_status = "SUCCESS" if is_success else "PENDING_CUSTOMER_ACTION"

    metadata = {
        "simulator": "incentive_offer_simulator",
        "discount_applied": "10% Renewal Grace Credit",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "ml_probability": round(ml_probability, 4),
        "effective_probability": round(peff, 4),
        "attempt_count": attempt_count,
        "demo": True,
    }
    return result_status, metadata, is_success


def execute_human_escalation_tool(
    case_id: str,
    reason: str,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Flags case for Human Ops escalation.
    """
    metadata = {
        "simulator": "human_escalation_tool",
        "escalation_queue": "High-Touch Merchant Ops",
        "reason": reason,
        "effective_probability": 0.0,
        "demo": True,
    }
    return "ESCALATED", metadata, False


def dispatch_tool(
    tool_name: str,
    case_id: str,
    payment_id: str,
    customer_id: str,
    amount_paise: int,
    ml_probability: float,
    reason: str = "",
    attempt_count: int = 0,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Strict allowlisted tool dispatcher. Rejects any tool not in ALLOWED_TOOLS.
    """
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError(f"Tool '{tool_name}' is not in the allowlisted tool registry.")

    if tool_name == "payment_retry_simulator":
        return execute_payment_retry_simulator(case_id, payment_id, amount_paise, ml_probability, attempt_count)
    elif tool_name == "payment_link_simulator":
        return execute_payment_link_simulator(case_id, payment_id, customer_id, amount_paise, ml_probability, attempt_count)
    elif tool_name == "payment_method_update_simulator":
        return execute_payment_method_update_simulator(case_id, customer_id, amount_paise, ml_probability, attempt_count)
    elif tool_name == "customer_notification_simulator":
        return execute_customer_notification_simulator(case_id, customer_id, amount_paise, ml_probability, attempt_count)
    elif tool_name == "incentive_offer_simulator":
        return execute_incentive_offer_simulator(case_id, customer_id, amount_paise, ml_probability, attempt_count)
    elif tool_name == "human_escalation_tool":
        return execute_human_escalation_tool(case_id, reason)
    else:
        raise ValueError(f"Unhandled allowlisted tool: {tool_name}")
