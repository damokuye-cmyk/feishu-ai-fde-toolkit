"""
🤖 LLM 客户端 - 通过 AI Gateway 调用大模型，支持工具调用
"""

import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("agent-platform.llm")

LITELLM_API_BASE = os.getenv("LITELLM_API_BASE", "http://ai-gateway:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "deepseek-chat")


async def chat_completion(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    tools: Optional[list[dict]] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """
    调用 LLM，支持工具调用 (function calling)
    
    Returns:
        {"role": "assistant", "content": "...", "tool_calls": [...]}
    """
    import httpx

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LITELLM_API_KEY}",
    }

    # 先尝试 AI Gateway
    for attempt, api_base in enumerate([
        LITELLM_API_BASE,
        "https://api.deepseek.com" if os.getenv("DEEPSEEK_API_KEY") else None,
    ]):
        if not api_base:
            continue
        
        # 如果用 DeepSeek 原生 API，需要替换 model 名并走原生格式
        is_fallback = "deepseek" in api_base and "gateway" not in api_base
        if is_fallback:
            payload["model"] = "deepseek-chat"
            headers["Authorization"] = f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
            # DeepSeek 原生支持 function calling
            if tools:
                payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{api_base}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                
                msg = data["choices"][0]["message"]
                result = {
                    "role": "assistant",
                    "content": msg.get("content", ""),
                    "tool_calls": [],
                }
                
                # 解析工具调用
                if "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        try:
                            args = json.loads(func.get("arguments", "{}"))
                        except json.JSONDecodeError:
                            args = {}
                        result["tool_calls"].append({
                            "id": tc.get("id", ""),
                            "name": func.get("name", ""),
                            "args": args,
                        })
                
                if is_fallback:
                    logger.info(f"🔄 已降级到 DeepSeek 原生 API (尝试 {attempt+1})")
                
                return result

        except Exception as e:
            logger.warning(f"API 调用失败 ({api_base}): {e}")
            continue
    
    return {
        "role": "assistant",
        "content": "⚠️ AI 服务暂不可用，请检查网关配置或 API Key。",
        "tool_calls": [],
    }
