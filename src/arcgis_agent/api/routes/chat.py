"""Chat REST API endpoints (Phase 7, Plan 07-04).

POST /api/v1/chat — Chat with LLM (streaming SSE or non-streaming JSON)
DELETE /api/v1/chat/{session_id} — Clear a conversation session
GET  /api/v1/chat/providers — List available LLM providers

Key design decisions:
- SSE streaming uses sse-starlette EventSourceResponse for proper event format
- MockLLMProvider fallback when no API key configured (dev safety)
- Lazy singleton ChatService shared across all requests
- API Key only held in backend (D-25), never exposed to frontend
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from arcgis_agent.api.schemas.chat import ChatRequest
from arcgis_agent.api.dependencies import get_conversation_store
from arcgis_agent.config import LLMConfig
from arcgis_agent.adapters.llm import OpenAICompatibleProvider
from arcgis_agent.adapters.mock_llm import MockLLMProvider
from arcgis_agent.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chat"])

_chat_service: Optional[ChatService] = None
_llm_config: Optional[LLMConfig] = None


def get_chat_service() -> ChatService:
    """Return the global ChatService singleton, initializing on first call.

    Uses MockLLMProvider if no API key is configured (dev safety, D-25).
    The LLM API key is loaded from environment variables only and is never
    exposed to the frontend.
    """
    global _chat_service, _llm_config
    if _chat_service is None:
        _llm_config = LLMConfig.from_env()
        provider_config = _llm_config.get_provider_config()

        # Use MockLLMProvider if no API key configured (dev safety)
        if not provider_config.api_key:
            logger.warning("No LLM API key configured. Using MockLLMProvider.")
            provider = MockLLMProvider()
        else:
            provider = OpenAICompatibleProvider(provider_config)

        _chat_service = ChatService(
            llm_provider=provider,
            store=get_conversation_store(),
            llm_config=_llm_config,
        )
    return _chat_service


@router.post("/chat")
async def chat_endpoint(body: ChatRequest):
    """Main chat endpoint.

    Returns SSE stream (text/event-stream) when stream=true (default).
    Returns JSON when stream=false.

    SSE event types:
        token       — Text content chunks from the LLM response
        tool_start  — Tool execution started (name, args)
        tool_end    — Tool execution completed (name, success, result)
        suggestions — Follow-up template suggestions (D-27)
        done        — Stream complete (tool_calls count, message_id)
        error       — An error occurred (code, message)
    """
    service = get_chat_service()

    if not body.stream:
        # Non-streaming: collect all events and return JSON
        events = []
        async for event in service.stream_chat(body.session_id, body.message):
            events.append(event)
        final_text = ""
        for evt in events:
            if evt["event"] == "token":
                final_text += evt["data"]["content"]
        return {
            "session_id": body.session_id,
            "response": final_text,
            "events": [
                e
                for e in events
                if e["event"] in ("tool_start", "tool_end")
            ],
        }

    # Streaming: SSE response via sse-starlette
    async def event_generator():
        async for event in service.stream_chat(body.session_id, body.message):
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())


@router.delete("/chat/{session_id}")
async def clear_chat(session_id: str):
    """Clear a conversation session and its full history.

    Use this when the user wants to start a fresh conversation
    without any prior context.
    """
    store = get_conversation_store()
    store.delete(session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/chat/providers")
async def list_providers():
    """List available LLM providers and their configuration status.

    Returns which provider is the default, which are configured
    (have API keys set), and the active models. The API key values
    are NEVER included in the response (D-25).
    """
    config = LLMConfig.from_env()
    providers_info = {}
    for name, pc in config.providers.items():
        providers_info[name] = {
            "model": pc.model,
            "configured": bool(pc.api_key),
            "is_default": name == config.default,
        }
    return {
        "default": config.default,
        "providers": providers_info,
    }
