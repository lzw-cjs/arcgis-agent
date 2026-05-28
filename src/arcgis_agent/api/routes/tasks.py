"""异步任务管理 REST API 端点

POST /api/v1/tasks       ： create a new task
GET  /api/v1/tasks/{id}  ： get task status/result
GET  /api/v1/tasks       ： list recent tasks
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from arcgis_agent.api.schemas.tasks import TaskCreate, TaskResult
from arcgis_agent.services.task_service import Task, TaskStore

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])
_task_store: TaskStore | None = None


def get_task_store() -> TaskStore:
    """Lazy-init TaskStore singleton."""
    global _task_store
    if _task_store is None:
        _task_store = TaskStore()
    return _task_store


def _task_to_result(task: Task) -> dict:
    """Convert Task dataclass to a dict compatible with TaskResult schema."""
    return {
        "task_id": task.task_id,
        "tool_name": task.tool_name,
        "status": task.status,
        "result": task.result,
        "error": task.error,
        "progress": task.progress,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


@router.post("", status_code=201)
async def create_task(body: TaskCreate):
    """创建新的异步任务"""
    store = get_task_store()
    task = store.create(body.tool_name, body.arguments)
    return {"task_id": task.task_id, "status": task.status}


@router.get("/{task_id}")
async def get_task(task_id: str):
    """按 ID 查询任务状态和结果"""
    store = get_task_store()
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_result(task)


@router.get("")
async def list_tasks(limit: int = 20):
    """列出最近任务，按时间倒序"""
    store = get_task_store()
    tasks = store.list_recent(limit)
    return {"tasks": [_task_to_result(t) for t in tasks], "count": len(tasks)}
