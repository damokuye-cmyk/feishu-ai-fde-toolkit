"""
🦞 Feishu AI Agent Platform - Main API Server
基于 Langgraph 的多 Agent 编排平台，支持工具调用 + 联网搜索
"""

import os
import json
import logging
from typing import Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.agent_base import BaseAgent

# === 自动发现所有 Agent ===
def discover_agents() -> dict[str, BaseAgent]:
    """
    自动扫描 agents/ 目录下所有 Agent 类并实例化
    新增 Agent 只需在 agents/ 下新建文件，继承 BaseAgent 即可
    """
    import importlib
    import pkgutil
    import agents

    found: dict[str, BaseAgent] = {}
    for importer, modname, ispkg in pkgutil.iter_modules(agents.__path__):
        if ispkg:
            continue
        module = importlib.import_module(f"agents.{modname}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseAgent) and attr is not BaseAgent:
                instance = attr()
                found[instance.name] = instance
                logging.getLogger("agent-platform").info(
                    f"🧬 加载 Agent: {instance.name} ({instance.description})"
                )
    return found


# === 配置 ===
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("agent-platform")

# === FastAPI ===
app = FastAPI(title="Feishu AI Agent Platform", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 加载所有 Agent ===
AGENTS: dict[str, BaseAgent] = discover_agents()


# === 数据模型 ===

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    show_thinking: bool = False

class ChatResponse(BaseModel):
    reply: str
    agent_name: str
    session_id: str
    thinking: Optional[str] = None

class AgentModel(BaseModel):
    name: str
    description: str
    tools: list[str]
    capabilities: list[str]


# === API 路由 ===

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agents": len(AGENTS),
        "agent_list": list(AGENTS.keys()),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/agents")
async def list_agents():
    return {
        "agents": [a.to_dict() for a in AGENTS.values()]
    }


@app.get("/agents/{agent_name}")
async def get_agent(agent_name: str):
    agent = AGENTS.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")
    return agent.to_dict()


@app.post("/agents/{agent_name}/chat")
async def agent_chat(agent_name: str, req: ChatRequest):
    agent = AGENTS.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")

    reply, session_id, thinking = await agent.chat(
        message=req.message,
        session_id=req.session_id,
        context=req.context,
    )

    return ChatResponse(
        reply=reply,
        agent_name=agent_name,
        session_id=session_id,
        thinking=thinking if req.show_thinking else None,
    )


@app.post("/v1/chat/completions")
async def openai_compatible_chat(payload: dict):
    """OpenAI 兼容接口"""
    messages = payload.get("messages", [])
    model = payload.get("model", "general")
    stream = payload.get("stream", False)

    # 查找匹配的 Agent
    agent = AGENTS.get(model) or AGENTS.get("general")
    if not agent:
        # 直接用 LLM 调用
        from core.llm import chat_completion
        result = await chat_completion(messages)
        return {
            "id": f"chatcmpl-{datetime.now().timestamp()}",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": result["content"]},
                "finish_reason": "stop"
            }]
        }

    # 使用 Agent 处理
    user_msg = messages[-1]["content"] if messages else ""
    reply, session_id, _ = await agent.chat(message=user_msg)

    return {
        "id": f"chatcmpl-{datetime.now().timestamp()}",
        "object": "chat.completion",
        "model": agent.name,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop"
        }]
    }


# === 启动 ===
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🦞 Agent Platform 启动: http://{host}:{port}")
    logger.info(f"📋 已加载 {len(AGENTS)} 个 Agent: {', '.join(AGENTS.keys())}")
    
    uvicorn.run(app, host=host, port=port)
