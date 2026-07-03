"""
🦞 Feishu Agent Platform - main
OpenAI 兼容 API + SSE 流式 + 管理后台
"""

import os
import json
import logging
import uuid
from typing import Optional, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import load_config
from core.agent import AgentRuntime
from core.db import session_store
from admin.api import router as admin_router

# === 配置 ===
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("agent-platform")

# === FastAPI ===
app = FastAPI(title="Feishu Agent Platform", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 Admin API
app.include_router(admin_router)


# ============================================================
# OpenAI 兼容 API
# ============================================================

class ChatRequest(BaseModel):
    model: str = "web-search"
    messages: list[dict] = []
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """
    OpenAI 兼容接口。
    核心入口：客户 Chatbox 直接调这里。
    """
    agents = load_config()
    
    # 按 model 名匹配 Agent
    agent_config = agents.get(req.model)
    
    # 如果没有精确匹配，用第一个启用的
    if not agent_config and agents:
        agent_config = list(agents.values())[0]
        logger.info(f"model='{req.model}' 未精确匹配, 使用默认 Agent: {agent_config.name}")
    
    if not agent_config:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{req.model}' 不存在，且无可用 Agent"
        )
    
    # 提取用户消息
    user_msg = req.messages[-1]["content"] if req.messages else ""
    if not user_msg:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    # 生成/使用 session_id
    session_id = str(uuid.uuid4())
    # 尝试从已有消息恢复 session（后续可优化）
    
    # 创建运行时
    runtime = AgentRuntime(agent_config)
    
    # === 流式模式 ===
    if req.stream:
        return StreamingResponse(
            _stream_response(runtime, user_msg, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    # === 非流式模式 ===
    full_reply = ""
    reasoning_parts = []
    async for chunk in runtime.chat_stream(user_msg, session_id):
        if chunk == "[DONE]":
            break
        if chunk.startswith("data: "):
            data = json.loads(chunk[6:])
            delta = data.get("choices", [{}])[0].get("delta", {})
            if "reasoning_content" in delta:
                reasoning_parts.append(delta["reasoning_content"])
            if "content" in delta:
                full_reply += delta["content"]
    
    # 构建 OpenAI 格式响应
    response_data = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": agent_config.name,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": full_reply,
            },
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": runtime.prompt_tokens,
            "completion_tokens": runtime.completion_tokens,
            "total_tokens": runtime.prompt_tokens + runtime.completion_tokens,
        },
    }
    
    # 如果有 reasoning，放在 message 里
    if reasoning_parts:
        response_data["choices"][0]["message"]["reasoning_content"] = "\n".join(reasoning_parts)
    
    return response_data


async def _stream_response(runtime: AgentRuntime, user_msg: str, session_id: str) -> AsyncGenerator[str, None]:
    """流式 SSE 响应生成器"""
    try:
        yield 'data: {"choices":[{"delta":{"role":"assistant"},"index":0}]}\n\n'
        
        async for chunk in runtime.chat_stream(user_msg, session_id):
            if chunk == "[DONE]":
                yield 'data: [DONE]\n\n'
                return
            yield f"{chunk}\n\n"
            
    except Exception as e:
        logger.error(f"流式响应异常: {e}")
        err_data = {
            "choices": [{
                "delta": {"content": f"⚠️ 服务异常: {str(e)}"},
                "index": 0,
            }]
        }
        yield f"data: {json.dumps(err_data, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"


# ============================================================
# Model List API (Chatbox 发现 Agent)
# ============================================================

@app.get("/v1/models")
async def list_models():
    """返回所有可用 Agent 作为 model 列表"""
    agents = load_config()
    models = []
    for name, config in agents.items():
        models.append({
            "id": name,
            "object": "model",
            "created": int(datetime.now().timestamp()),
            "owned_by": "feishu-agent-platform",
            "permission": [],
            "root": name,
            "parent": None,
        })
    return {"object": "list", "data": models}


# ============================================================
# 管理后台 HTML (内嵌)
# ============================================================

@app.get("/admin", response_class=HTMLResponse)
async def admin_ui():
    """管理后台页面"""
    with open("/app/admin/webui/index.html", "r") as f:
        return HTMLResponse(f.read())


@app.get("/")
async def root():
    return {
        "service": "🦞 Feishu Agent Platform",
        "version": "2.0.0",
        "docs": "/docs",
        "admin": "/admin",
        "models": "/v1/models",
        "chat": "/v1/chat/completions",
    }


# === 启动 ===
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # 启动时加载配置
    agents = load_config()
    
    logger.info(f"🦞 Feishu Agent Platform v2.0.0")
    logger.info(f"🌐 http://{host}:{port}")
    logger.info(f"📋 {len(agents)} Agent(s) loaded: {list(agents.keys())}")
    logger.info(f"🔌 OpenAI API: POST /v1/chat/completions")
    logger.info(f"🖥️  Admin UI:  /admin")
    
    uvicorn.run(app, host=host, port=port)
