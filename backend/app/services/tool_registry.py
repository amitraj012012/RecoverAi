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


def execute_payment_retry_simulator(
    case_id: str,
    payment_id: str,
    amount_paise: int,
    ml_probability: float,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates automated payment retry against simulated payment gateway.
    Outcome directly reflects the ML probability and gateway state.
    """
    # Strict probability-based resolution (no artificial floor)
    is_success = random.random() < ml_probability
    result_status = "SUCCESS" if is_success else "FAILED"

    metadata = {
        "simulator": "payment_retry_simulator",
        "simulated_gateway_ref": f"sim_tx_{case_id}_{random.randint(1000, 9999)}",
        "attempt_timestamp": datetime.now(timezone.utc).isoformat(),
        "amount_paise": amount_paise,
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
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates generating a secure simulated payment link dispatched to the customer.
    """
    link_id = f"plink_sim_{case_id.replace('rec_', '')}"
    simulated_url = f"https://pay.recoverai.demo/link/{link_id}"

    # Link conversion depends on customer recoverability probability
    is_success = random.random() < ml_probability
    result_status = "SUCCESS" if is_success else "PENDING_CUSTOMER_ACTION"

    metadata = {
        "simulator": "payment_link_simulator",
        "simulated_payment_link": simulated_url,
        "dispatched_channel": "WhatsApp + Email (Simulated)",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "demo": True,
    }
    return result_status, metadata, is_success


def execute_payment_method_update_simulator(
    case_id: str,
    customer_id: str,
    amount_paise: int,
    ml_probability: float,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates prompting customer to provide alternate payment method (e.g. UPI / Netbanking).
    """
    is_success = random.random() < ml_probability
    result_status = "SUCCESS" if is_success else "PENDING_CUSTOMER_ACTION"

    metadata = {
        "simulator": "payment_method_update_simulator",
        "alternate_method_requested": "UPI / AutoPay",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "demo": True,
    }
    return result_status, metadata, is_success


def execute_customer_notification_simulator(
    case_id: str,
    customer_id: str,
    amount_paise: int,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates sending friendly personalized reminder notification.
    """
    metadata = {
        "simulator": "customer_notification_simulator",
        "channel": "SMS / In-App Banner",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "demo": True,
    }
    # Reminder leaves case in actionable state pending customer payment
    return "NOTIFICATION_DISPATCHED", metadata, False


def execute_incentive_offer_simulator(
    case_id: str,
    customer_id: str,
    amount_paise: int,
    ml_probability: float,
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Simulates applying dynamic incentive (e.g., 10% discount on renewal).
    """
    is_success = random.random() < ml_probability
    metadata = {
        "simulator": "incentive_offer_simulator",
        "discount_applied": "10% Renewal Grace Credit",
        "customer_id": customer_id,
        "amount_paise": amount_paise,
        "demo": True,
    }
    return "SUCCESS" if is_success else "PENDING_CUSTOMER_ACTION", metadata, is_success


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
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Strict allowlisted tool dispatcher. Rejects any tool not in ALLOWED_TOOLS.
    """
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError(f"Tool '{tool_name}' is not in the allowlisted tool registry.")

    if tool_name == "payment_retry_simulator":
        return execute_payment_retry_simulator(case_id, payment_id, amount_paise, ml_probability)
    elif tool_name == "payment_link_simulator":
        return execute_payment_link_simulator(case_id, payment_id, customer_id, amount_paise, ml_probability)
    elif tool_name == "payment_method_update_simulator":
        return execute_payment_method_update_simulator(case_id, customer_id, amount_paise, ml_probability)
    elif tool_name == "customer_notification_simulator":
        return execute_customer_notification_simulator(case_id, customer_id, amount_paise)
    elif tool_name == "incentive_offer_simulator":
        return execute_incentive_offer_simulator(case_id, customer_id, amount_paise, ml_probability)
    elif tool_name == "human_escalation_tool":
        return execute_human_escalation_tool(case_id, reason)
    else:
        raise ValueError(f"Unhandled allowlisted tool: {tool_name}")
