"""FastAPI dependency injection (Phase 7).

Provides singletons shared across route handlers.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


class ConversationStore:
    """In-memory conversation history store (per-session).

    Stores conversation messages keyed by session_id.
    """

    def __init__(self) -> None:
        self._store: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self._store[session_id].append({"role": role, "content": content})

    def get(self, session_id: str) -> list[dict[str, Any]]:
        """Get all messages for a session."""
        return list(self._store.get(session_id, []))

    def clear(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        self._store.pop(session_id, None)
