# Mini Agent Orchestrator

A lightweight, event-driven order processing agent built with FastAPI + Groq LLM.

## Architecture

### 1. Planner (LLM Layer)
The `/agent/run` endpoint passes the user's natural language request to **Groq (LLaMA3-8b)** via a structured system prompt. The LLM returns a JSON plan — a list of tasks with dependencies (`depends_on`), forming a lightweight DAG.

### 2. Tool Registry
Two async mock tools are implemented:
- `cancel_order(order_id)` — 20% random failure rate, 0.5s latency
- `send_email(email, message)` — always succeeds, 1s latency

### 3. Orchestrator (Async Execution Engine)
The orchestrator:
- Scans for tasks whose dependencies are all resolved as SUCCESS
- Runs ready tasks **concurrently** via `asyncio.gather`
- If a dependency fails, downstream tasks are automatically marked FAILED (skipped)
- Loops until all tasks are settled

### 4. Guardrails
- If `cancel_order` fails, `send_email` (which depends on it) is **never called**
- LLM JSON is validated with Pydantic before execution
- All errors are caught and surfaced cleanly in the response

## Running Locally
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit: http://localhost:8000/docs

## Example Request
```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"request": "Cancel my order #9921 and email me the confirmation at user@example.com"}'
```