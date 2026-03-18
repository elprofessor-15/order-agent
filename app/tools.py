import asyncio
import random
import logging

logger = logging.getLogger(__name__)

async def cancel_order(order_id: str) -> dict:
    """
    Mock cancel_order tool.
    Simulates a 20% random failure rate.
    """
    logger.info(f"[TOOL] cancel_order called with order_id={order_id}")
    await asyncio.sleep(0.5)  # simulate network latency

    # 20% chance of failure
    if random.random() < 0.20:
        logger.warning(f"[TOOL] cancel_order FAILED for order_id={order_id}")
        return {
            "success": False,
            "message": f"Order #{order_id} cancellation failed: order already shipped or does not exist."
        }

    logger.info(f"[TOOL] cancel_order SUCCESS for order_id={order_id}")
    return {
        "success": True,
        "message": f"Order #{order_id} has been successfully cancelled."
    }


async def send_email(email: str, message: str) -> dict:
    """
    Mock send_email tool.
    Simulates sending an email with a 1-second delay.
    """
    logger.info(f"[TOOL] send_email called to={email}")
    await asyncio.sleep(1.0)  # simulate email sending delay

    logger.info(f"[TOOL] send_email SUCCESS to={email}")
    return {
        "success": True,
        "message": f"Email successfully sent to {email}."
    }


# Tool registry — maps LLM tool names to actual functions
TOOL_REGISTRY = {
    "cancel_order": cancel_order,
    "send_email": send_email,
}