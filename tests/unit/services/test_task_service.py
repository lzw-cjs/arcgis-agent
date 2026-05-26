"""Unit tests for TaskStore (SQLite persistence)."""
import pytest
from arcgis_agent.services.task_service import TaskStore, Task


class TestTaskStore:
    def test_create_task(self, task_store):
        task = task_store.create("gp_buffer", {"distance": 100})
        assert task.task_id is not None
        assert task.tool_name == "gp_buffer"
        assert task.status == "pending"
        assert task.arguments == {"distance": 100}

    def test_get_task(self, task_store):
        created = task_store.create("test", {})
        found = task_store.get(created.task_id)
        assert found is not None
        assert found.task_id == created.task_id
        assert found.tool_name == "test"

    def test_get_nonexistent(self, task_store):
        assert task_store.get("nonexistent-uuid") is None

    def test_update_task(self, task_store):
        task = task_store.create("test", {})
        task_store.update(task.task_id, status="running", progress=50.0)
        updated = task_store.get(task.task_id)
        assert updated is not None
        assert updated.status == "running"
        assert updated.progress == 50.0

    def test_update_to_completed(self, task_store):
        task = task_store.create("test", {})
        task_store.update(task.task_id, status="completed",
                         result={"output": "test.shp"}, progress=100.0)
        updated = task_store.get(task.task_id)
        assert updated is not None
        assert updated.status == "completed"
        assert updated.result == {"output": "test.shp"}
        assert updated.progress == 100.0

    def test_list_recent(self, task_store):
        for i in range(5):
            task_store.create(f"tool_{i}", {"i": i})
        tasks = task_store.list_recent(limit=3)
        assert len(tasks) == 3
        # Most recent first
        assert tasks[0].tool_name == "tool_4"

    def test_persistence(self, tmp_path):
        """Data persists across TaskStore instances."""
        db_path = tmp_path / "persist.db"
        store1 = TaskStore(db_path=db_path)
        task = store1.create("persist_test", {"x": 1})
        store1.update(task.task_id, status="running")
        store1._conn.close()

        store2 = TaskStore(db_path=db_path)
        found = store2.get(task.task_id)
        assert found is not None
        assert found.status == "running"
        assert found.arguments == {"x": 1}
        store2._conn.close()

    def test_create_task_auto_generates_id(self, task_store):
        task = task_store.create("auto_id", {})
        assert len(task.task_id) >= 32  # UUID standard length

    def test_list_empty(self, task_store):
        tasks = task_store.list_recent()
        assert tasks == []
