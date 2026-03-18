import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from app.planner import create_plan
from app.orchestrator import execute_plan
from app.models import AgentResponse, TaskStatus

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mini Agent Orchestrator",
    description="Event-driven order processing agent using Groq LLM + FastAPI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (the UI)
app.mount("/static", StaticFiles(directory="static"), name="static")


class UserRequest(BaseModel):
    request: str


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/agent/run", response_model=AgentResponse)
async def run_agent(body: UserRequest):
    logger.info(f"[API] Received request: {body.request}")

    try:
        plan = await create_plan(body.request)
    except Exception as e:
        logger.error(f"[API] Planner failed: {e}")
        raise HTTPException(status_code=500, detail=f"Planner error: {str(e)}")

    try:
        results = await execute_plan(plan)
    except Exception as e:
        logger.error(f"[API] Orchestrator failed: {e}")
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")

    failed = [r for r in results if r.status == TaskStatus.FAILED]
    final_status = TaskStatus.FAILED if failed else TaskStatus.SUCCESS

    summary_parts = []
    for r in results:
        if r.status == TaskStatus.SUCCESS:
            summary_parts.append(f"✅ {r.task_name}: {r.output}")
        else:
            summary_parts.append(f"❌ {r.task_name}: {r.error}")

    summary = " | ".join(summary_parts)

    return AgentResponse(
        request=body.request,
        plan=[t.dict() for t in plan.tasks],
        results=results,
        final_status=final_status,
        summary=summary
    )