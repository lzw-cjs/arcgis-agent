"""对话 REST API 端点

POST /api/v1/chat ： Chat with LLM (streaming SSE or non-streaming JSON)
DELETE /api/v1/chat/{session_id} ： Clear a conversation session
GET  /api/v1/chat/providers ： List available LLM providers

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
    """返回全局 ChatService 单例，首次调用时初始化

    未配置 API 密钥时使用 MockLLMProvider（开发安全）
    LLM API 密钥仅从环境变量加载，绝不暴露给前端
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
    """主对话端点

    stream=true（默认）返回 SSE 流式响应 (text/event-stream)
    stream=false 返回 JSON 格式

    SSE 事件类型:
        token       ： LLM 生成的文本内容块
        tool_start  ： 工具开始执行（名称, 参数）
        tool_end    ： 工具执行完成（名称, 成功/失败, 结果）
        suggestions ： 后续建议模板
        done        ： 流结束（工具调用计数, 消息ID）
        error       ： 发生错误（错误码, 错误消息）
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
    """清除会话及其全部历史记录

    用于开启全新对话，不保留任何上下文
    """
    store = get_conversation_store()
    store.delete(session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/chat/providers")
async def list_providers():
    """查看可用 LLM 提供商及其配置状态

    返回默认提供商、已配置（已设置 API 密钥）的提供商及活跃模型
    API 密钥值绝不包含在响应中
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
