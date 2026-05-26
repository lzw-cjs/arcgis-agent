"""Dependency injection and arcpy thread-safety wrapper.

Provides _run_in_thread() for serialized arcpy calls and
ConversationStore for in-memory chat history.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

# ── arcpy Serialization Lock ──────────────────────────────────
# Same pattern as mcp_server.py:_ARC_LOCK. arcpy is COM-based and
# NOT thread-safe. All arcpy operations must be serialized through
# this lock. asyncio.to_thread() offloads the blocking call off the
# event loop; the lock ensures mutual exclusion.
_ARC_LOCK = threading.Lock()

# ── Conversation Store ────────────────────────────────────────


class ConversationStore:
    """Thread-safe in-memory conversation history store.

    Stores message lists keyed by session_id with LRU eviction.
    Messages are typed as list[BaseMessage] but stored as plain
    objects for lazy import flexibility.
    """

    def __init__(self, max_sessions: int = 100) -> None:
        self._store: OrderedDict[str, list[Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._max_sessions = max_sessions

    def get(self, session_id: str) -> list[Any]:
        """Return messages for a session, or empty list if not found."""
        with self._lock:
            return list(self._store.get(session_id, []))

    def update(self, session_id: str, messages: list[Any]) -> None:
        """Store or replace messages for a session.

        LRU eviction: when len >= max_sessions, the oldest session
        (first inserted, least recently used) is evicted.
        Existing sessions are moved to the end (most recently used).
        """
        with self._lock:
            if session_id in self._store:
                self._store[session_id] = list(messages)
                self._store.move_to_end(session_id)
                return

            if len(self._store) >= self._max_sessions:
                self._store.popitem(last=False)  # evict oldest

            self._store[session_id] = list(messages)

    def delete(self, session_id: str) -> None:
        """Remove a session and its messages."""
        with self._lock:
            self._store.pop(session_id, None)


# Global singleton, lazily initialized by lifespan
_conversation_store: ConversationStore | None = None


def get_conversation_store() -> ConversationStore:
    """Return the global ConversationStore singleton.

    Lazily initializes on first call. The FastAPI lifespan will
    call this during startup to ensure it exists before any
    request handler accesses it.
    """
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store


# ── Thread-safe arcpy Executor ────────────────────────────────


async def _run_in_thread(fn, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Execute a sync function in a thread with arcpy serialization.

    Uses asyncio.to_thread() to avoid blocking the event loop and
    threading.Lock (_ARC_LOCK) to serialize arcpy COM calls.

    Returns a dict (Result.model_dump() or raw dict). On exception,
    returns Result.from_exception(exc).model_dump().
    """

    def _sync() -> dict[str, Any]:
        """Closure executed in the thread pool under _ARC_LOCK."""
        try:
            with _ARC_LOCK:
                from arcgis_agent.models.result import Result

                result = fn(*args, **kwargs)
                if isinstance(result, Result):
                    return result.model_dump()
                return result  # type: ignore[return-value]
        except Exception as exc:
            from arcgis_agent.models.result import Result

            return Result.from_exception(exc).model_dump()

    return await asyncio.to_thread(_sync)
