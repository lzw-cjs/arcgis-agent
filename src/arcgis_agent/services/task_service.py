"""Task storage with SQLite persistence (Phase 7).

Thread-safe task CRUD operations for async background task tracking.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Task:
    """A single task record stored in SQLite."""

    task_id: str
    tool_name: str
    status: str = "pending"
    arguments: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    progress: float = 0.0
    created_at: str = ""
    updated_at: str = ""


class TaskStore:
    """SQLite-backed task storage with thread-safe operations."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = Path("tasks.db")
        self._db_path = Path(db_path)
        self._local = threading.local()
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        conn = self._conn
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                arguments TEXT NOT NULL DEFAULT '{}',
                result TEXT,
                progress REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()

    def create(self, tool_name: str, arguments: dict[str, Any]) -> Task:
        """Create a new task with auto-generated UUID."""
        task_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn
        conn.execute(
            """INSERT INTO tasks (task_id, tool_name, status, arguments, progress, created_at, updated_at)
               VALUES (?, ?, 'pending', ?, 0.0, ?, ?)""",
            (task_id, tool_name, json.dumps(arguments), now, now),
        )
        conn.commit()
        return Task(
            task_id=task_id,
            tool_name=tool_name,
            status="pending",
            arguments=arguments,
            created_at=now,
            updated_at=now,
        )

    def get(self, task_id: str) -> Task | None:
        """Get a task by ID, or None if not found."""
        conn = self._conn
        row = conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    def update(
        self,
        task_id: str,
        status: str | None = None,
        result: dict[str, Any] | None = None,
        progress: float | None = None,
    ) -> None:
        """Update task fields. Only non-None values are updated."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn
        updates: list[str] = ["updated_at = ?"]
        params: list[Any] = [now]

        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if result is not None:
            updates.append("result = ?")
            params.append(json.dumps(result))
        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)

        params.append(task_id)
        conn.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?",
            params,
        )
        conn.commit()

    def list_recent(self, limit: int = 20) -> list[Task]:
        """List most recent tasks, newest first."""
        conn = self._conn
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            task_id=row["task_id"],
            tool_name=row["tool_name"],
            status=row["status"],
            arguments=json.loads(row["arguments"]),
            result=json.loads(row["result"]) if row["result"] else None,
            progress=row["progress"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
