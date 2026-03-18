from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class Task(BaseModel):
    name: str           # e.g. "cancel_order"
    args: dict          # e.g. {"order_id": "9921"}
    depends_on: List[str] = []  # task names this depends on

class Plan(BaseModel):
    tasks: List[Task]

class TaskResult(BaseModel):
    task_name: str
    status: TaskStatus
    output: Optional[str] = None
    error: Optional[str] = None

class AgentResponse(BaseModel):
    request: str
    plan: List[dict]
    results: List[TaskResult]
    final_status: TaskStatus
    summary: str