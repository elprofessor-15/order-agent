import json
import logging
from groq import AsyncGroq
from app.models import Plan, Task
import os

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an order-processing planner agent. Your job is to parse a user's natural language
request and produce a structured JSON execution plan.

You have access to exactly two tools:
1. cancel_order(order_id: str) — cancels an order by ID
2. send_email(email: str, message: str) — sends an email to a given address

Rules:
- Output ONLY a valid JSON object. No explanation, no markdown fences.
- The JSON must match this schema exactly:
{
  "tasks": [
    {
      "name": "<tool_name>",
      "args": { <key>: <value> },
      "depends_on": ["<task_name_that_must_succeed_first>"]
    }
  ]
}
- Use "depends_on" to express dependencies. For example, send_email should depend on cancel_order if both are needed.
- If a step doesn't depend on anything, use an empty list [].
- Keep task names unique (e.g. "cancel_order", "send_email").
- For send_email, craft a professional, concise message relevant to the user's request.
"""

async def create_plan(user_request: str) -> Plan:
    """
    Calls Groq LLM to parse the natural language request into a task plan.
    Returns a validated Plan object.
    """
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    logger.info(f"[PLANNER] Sending request to Groq: {user_request}")

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_request}
        ],
        temperature=0.1,  # low temp for deterministic planning
        max_tokens=512,
    )

    raw = response.choices[0].message.content.strip()
    logger.info(f"[PLANNER] Raw LLM response: {raw}")

    # Parse and validate
    data = json.loads(raw)
    plan = Plan(tasks=[Task(**t) for t in data["tasks"]])

    logger.info(f"[PLANNER] Plan created with {len(plan.tasks)} tasks")
    return plan