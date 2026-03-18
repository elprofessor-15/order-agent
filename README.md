# ⚡ Mini Agent Orchestrator

> An event-driven order processing agent that accepts natural language commands, plans tasks using Groq LLM, and executes them asynchronously with guardrails.

Built with **FastAPI + Groq (LLaMA-3.3-70b) + Python asyncio** — no LangChain, no heavy frameworks.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA3-orange)

---

## ✨ What it does

You send a natural language request like:

"Cancel my order #9921 and email me the confirmation at user@example.com"

The agent:
1. 🧠 **Plans** — Groq LLM parses the request into a structured JSON task DAG
2. ⚡ **Executes** — runs tools asynchronously with dependency awareness
3. 🛡️ **Guards** — if cancel_order fails, send_email is automatically skipped
4. 📊 **Reports** — returns full results via API and renders a beautiful UI

---

## 🏗️ Architecture
```
User Request (natural language)
         │
         ▼
   ┌─────────────┐
   │   PLANNER   │  ← Groq LLaMA3 generates a JSON task plan (DAG)
   └──────┬──────┘
          │
          ▼
   ┌─────────────────┐
   │  ORCHESTRATOR   │  ← Resolves dependencies, runs ready tasks concurrently
   └──────┬──────────┘
          │
    ┌─────┴──────┐
    ▼            ▼
cancel_order  send_email   ← Async mock tools (tool registry pattern)
    │
    └── if FAILED → send_email is SKIPPED (guardrail)
```

### Key Files

| File | Role |
|------|------|
| app/main.py | FastAPI server, /agent/run endpoint, serves UI |
| app/planner.py | Calls Groq API, converts natural language to JSON task plan |
| app/orchestrator.py | Async DAG executor with dependency and guardrail logic |
| app/tools.py | Mock cancel_order with 20% fail rate and send_email with 1s delay |
| app/models.py | Pydantic models for Plan, Task, TaskResult, AgentResponse |
| static/index.html | Full frontend UI |

---

## 🚀 Setup and Run

### 1. Clone the repo
```bash
git clone https://github.com/elprofessor-15/order-agent.git
cd order-agent
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key
```bash
cp .env.example .env
```

Open .env and replace the placeholder with your actual key.
Get a free API key at: https://console.groq.com

### 5. Start the server
```bash
uvicorn app.main:app --reload
```

### 6. Open the UI

Visit http://localhost:8000 in your browser.

### 7. Call the API directly
```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"request": "Cancel my order #9921 and email me the confirmation at user@example.com"}'
```

### 8. Swagger API docs

Visit http://localhost:8000/docs

---

## 🧪 Example Commands to Try
```
Cancel my order #9921 and email me the confirmation at user@example.com
Cancel order #4402 and notify admin@store.com with a confirmation
Cancel my order #1234 and send receipt to john@doe.com
```

---

## 🛡️ Guardrail in Action

cancel_order has a 20% random failure rate built in to simulate real-world failures.
Run the same command 5 to 6 times and you will see both scenarios:

- ✅ Success case — order cancelled and email sent
- ❌ Failure case — cancel_order fails and send_email is automatically skipped

This is the core guardrail. Downstream tasks never execute if their dependency failed.

---

## 🔧 Architectural Decisions

### 1. State Management

Each request is fully stateless. The orchestrator maintains a results dictionary of type Dict[str, TaskResult] scoped to a single request lifecycle. No database needed — state lives and dies within one execution cycle.

### 2. Async Execution

Uses Python's asyncio.gather() to run independent tasks concurrently. The orchestrator loops through all pending tasks each iteration, identifies which ones have all dependencies resolved as SUCCESS, and fires them in parallel. Tasks with unmet dependencies wait for the next iteration.

### 3. LLM Unreliability Handling

- All Groq API calls are wrapped in try/except — any LLM failure returns a clean HTTP 500 with a descriptive error message
- temperature=0.1 keeps the plan output deterministic and consistent across calls
- Pydantic validates the LLM's JSON output before any execution begins — malformed output fails fast with a clear error rather than crashing mid-workflow
- If the LLM hallucinates an unknown tool name, the orchestrator catches it via the tool registry lookup and marks that task as FAILED cleanly

### 4. Tool Registry Pattern

All tools live in a TOOL_REGISTRY dictionary mapping tool names to async functions. The orchestrator never imports tools directly — it looks them up by name from the LLM's plan at runtime. Adding a new tool requires only writing the function and registering it with one line.

### 5. DAG via depends_on

The LLM is prompted to express task dependencies using a depends_on list per task. The orchestrator resolves this at runtime with a simple iterative loop — no graph library needed. This keeps the system lightweight while still supporting multi-step dependent workflows.

---

## 📦 Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| FastAPI | Async web framework |
| Groq API LLaMA-3.3-70b-versatile | LLM planner |
| asyncio | Concurrent tool execution |
| Pydantic v2 | Schema validation |
| uvicorn | ASGI server |

---

## 📁 Project Structure
```
order-agent/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, endpoint, static file serving
│   ├── planner.py        # Groq LLM integration and plan parsing
│   ├── orchestrator.py   # Async DAG executor with guardrails
│   ├── tools.py          # Mock async tools with simulated failures
│   └── models.py         # Pydantic schemas
├── static/
│   └── index.html        # Frontend UI
├── .env.example          # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| GROQ_API_KEY | Your Groq API key from console.groq.com |

---

*Built as a Mini Agent Orchestrator engineering challenge submission.*