"""Chat REST API endpoints (Phase 7).

POST /api/v1/chat — chat with LLM (streaming or non-streaming)
GET  /api/v1/chat/providers — list available LLM providers
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["chat"])


# ── Provider configuration ──

_PROVIDERS = {
    "default": "mock",
    "providers": [
        {"id": "mock", "name": "Mock (离线)", "models": ["mock-gis-v1"]},
        {"id": "openai", "name": "OpenAI", "models": ["gpt-4o", "gpt-4o-mini"]},
    ],
}


@router.get("/chat/providers")
def list_providers() -> dict:
    return _PROVIDERS


# ── Chat ──

class ChatRequest(BaseModel):
    session_id: str
    message: str
    stream: bool = False


async def _generate_sse(session_id: str, message: str):
    from arcgis_agent.adapters.mock_llm import MockLLMProvider
    llm = MockLLMProvider()
    result = llm.chat(message)
    response_text = getattr(result, "content", str(result))
    for word in response_text.split():
        yield f"data: {word}\n\n"
    yield f"data: [DONE]\n\n"


@router.post("/chat")
async def chat(req: ChatRequest):
    from arcgis_agent.adapters.mock_llm import MockLLMProvider
    llm = MockLLMProvider()
    result = llm.chat(req.message)
    response_text = getattr(result, "content", str(result))

    if req.stream:
        return StreamingResponse(
            _generate_sse(req.session_id, req.message),
            media_type="text/event-stream",
        )

    return {
        "session_id": req.session_id,
        "response": response_text,
    }
