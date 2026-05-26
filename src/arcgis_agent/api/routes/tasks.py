"""Task management REST API endpoints (Phase 7).

POST /api/v1/tasks — create a new task
GET  /api/v1/tasks/{task_id} — get task status/result
GET  /api/v1/tasks — list recent tasks
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["tasks"])

# In-memory task store for the API layer
_task_store = None


def get_task_store():
    """Lazy-import TaskStore singleton."""
    global _task_store
    if _task_store is None:
        from arcgis_agent.services.task_service import TaskStore
        _task_store = TaskStore()
    return _task_store


class CreateTaskRequest(BaseModel):
    tool_name: str
    arguments: dict = {}


class TaskResponse(BaseModel):
    task_id: str
    tool_name: str
    status: str
    arguments: dict
    result: dict | None = None
    progress: float = 0.0


@router.post("/tasks", status_code=201)
def create_task(req: CreateTaskRequest) -> dict:
    store = get_task_store()
    task = store.create(req.tool_name, req.arguments)
    return {
        "task_id": task.task_id,
        "tool_name": task.tool_name,
        "status": task.status,
        "arguments": task.arguments,
        "progress": task.progress,
    }


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    store = get_task_store()
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.task_id,
        "tool_name": task.tool_name,
        "status": task.status,
        "arguments": task.arguments,
        "result": task.result,
        "progress": task.progress,
    }


@router.get("/tasks")
def list_tasks(limit: int = 20) -> dict:
    store = get_task_store()
    tasks = store.list_recent(limit=limit)
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "tool_name": t.tool_name,
                "status": t.status,
                "progress": t.progress,
            }
            for t in tasks
        ],
        "count": len(tasks),
    }
