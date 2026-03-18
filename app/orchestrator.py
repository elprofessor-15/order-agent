import asyncio
import logging
from typing import Dict, List
from app.models import Plan, TaskResult, TaskStatus
from app.tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)


async def execute_plan(plan: Plan) -> List[TaskResult]:
    """
    Executes the plan respecting dependencies.
    
    Architecture:
    - Maintains a results map: task_name -> TaskResult
    - Repeatedly scans for tasks whose dependencies are all SUCCESS
    - If any dependency FAILED, marks the task as FAILED (skipped)
    - Runs tasks whose deps are met concurrently using asyncio.gather
    - Stops when all tasks are settled
    """
    results: Dict[str, TaskResult] = {}
    pending = {task.name: task for task in plan.tasks}

    while pending:
        # Find tasks ready to run (all dependencies resolved as SUCCESS)
        ready = []
        failed_due_to_dep = []

        for name, task in pending.items():
            dep_statuses = [results[dep].status for dep in task.depends_on if dep in results]
            unresolved_deps = [dep for dep in task.depends_on if dep not in results]

            if unresolved_deps:
                # Still waiting on dependencies
                continue

            # Check if any resolved dep failed
            if any(s == TaskStatus.FAILED for s in dep_statuses):
                failed_due_to_dep.append(name)
            else:
                ready.append(name)

        # Mark tasks with failed dependencies as FAILED (skipped)
        for name in failed_due_to_dep:
            task = pending.pop(name)
            logger.warning(f"[ORCHESTRATOR] Skipping '{name}' due to failed dependency")
            results[name] = TaskResult(
                task_name=name,
                status=TaskStatus.FAILED,
                error=f"Skipped because a dependency failed."
            )

        if not ready and not failed_due_to_dep:
            # Nothing progressed — possible circular dep or all waiting
            logger.error("[ORCHESTRATOR] Deadlock detected or no progress possible.")
            break

        # Execute ready tasks concurrently
        async def run_task(name: str):
            task = pending.pop(name)
            tool_fn = TOOL_REGISTRY.get(task.name)

            if not tool_fn:
                logger.error(f"[ORCHESTRATOR] Unknown tool: {task.name}")
                results[name] = TaskResult(
                    task_name=name,
                    status=TaskStatus.FAILED,
                    error=f"Tool '{task.name}' not found in registry."
                )
                return

            logger.info(f"[ORCHESTRATOR] Executing '{name}' with args={task.args}")
            try:
                output = await tool_fn(**task.args)
                if output.get("success"):
                    results[name] = TaskResult(
                        task_name=name,
                        status=TaskStatus.SUCCESS,
                        output=output["message"]
                    )
                    logger.info(f"[ORCHESTRATOR] '{name}' SUCCESS")
                else:
                    results[name] = TaskResult(
                        task_name=name,
                        status=TaskStatus.FAILED,
                        error=output["message"]
                    )
                    logger.warning(f"[ORCHESTRATOR] '{name}' FAILED: {output['message']}")
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] '{name}' raised exception: {e}")
                results[name] = TaskResult(
                    task_name=name,
                    status=TaskStatus.FAILED,
                    error=str(e)
                )

        await asyncio.gather(*[run_task(name) for name in ready])

    return list(results.values())