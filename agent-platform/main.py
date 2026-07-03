"""
🦞 Feishu AI Agent Platform - Main API
基于 Langgraph 的 Agent 编排平台
"""

import os
import json
import logging
from typing import Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("agent-platform")

app = FastAPI(title="Feishu AI Agent Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 配置 ===
LITELLM_API_BASE = os.getenv("LITELLM_API_BASE", "http://localhost:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "deepseek-chat")

# === 数据模型 ===

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    agent_name: str
    session_id: str
    thinking: Optional[str] = None

class AgentInfo(BaseModel):
    name: str
    description: str
    capabilities: list[str]
    is_ready: bool

# === Agent 引擎 ===

class AgentEngine:
    """轻量级 Agent 引擎，通过 AI Gateway 调用 LLM"""

    def __init__(self):
        self.sessions: dict[str, list[dict]] = {}
        self.agents = self._register_agents()

    def _register_agents(self) -> dict:
        return {
            "manufacturing": {
                "name": "制造业助手",
                "description": "生产管理、设备巡检、质量告警、供应链协同",
                "system_prompt": """你是飞书制造行业 AI 助手，擅长：
1. 生产异常告警分析与根因推荐
2. 设备巡检记录与排程优化
3. 质量数据管理与趋势分析
4. 供应链物料跟踪与库存预警

请用中文回答问题，基于制造业最佳实践给出建议。""",
                "capabilities": ["异常告警", "设备管理", "质量管控", "供应链"]
            },
            "rag": {
                "name": "知识库问答",
                "description": "基于企业文档的知识库智能问答",
                "system_prompt": """你是企业知识库 AI 助手。
基于提供的上下文信息，准确回答用户问题。
如果不知道答案，请明确告知，不要编造。""",
                "capabilities": ["文档问答", "知识检索"]
            },
            "general": {
                "name": "通用助手",
                "description": "通用 AI 对话助手",
                "system_prompt": """你是有帮助的 AI 助手。
回答问题准确、简洁、有条理。""",
                "capabilities": ["通用对话"]
            }
        }

    async def call_llm(self, messages: list[dict], model: str = DEFAULT_MODEL) -> str:
        """通过 AI Gateway 调用 LLM"""
        import httpx

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LITELLM_API_KEY}",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{LITELLM_API_BASE}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # 降级到原生 API
            return await self._fallback_llm(messages, model)

    async def _fallback_llm(self, messages: list[dict], model: str) -> str:
        """AI Gateway 不可用时降级到原生 API"""
        import httpx

        # DeepSeek 原生 API 作为降级
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        if deepseek_key:
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        json={"model": "deepseek-chat", "messages": messages},
                        headers={"Authorization": f"Bearer {deepseek_key}"},
                    )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Fallback also failed: {e}")

        return "⚠️ AI 服务暂不可用，请检查网关配置。"

    async def chat(self, agent_name: str, message: str, session_id: str = None) -> tuple[str, str]:
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"未知 Agent: {agent_name}")

        if not session_id:
            session_id = f"{agent_name}_{datetime.now().timestamp()}"

        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": agent["system_prompt"]}
            ]

        self.sessions[session_id].append({"role": "user", "content": message})

        # 保留最近 20 条消息作为上下文
        messages = self.sessions[session_id][-20:]

        reply = await self.call_llm(messages)

        self.sessions[session_id].append({"role": "assistant", "content": reply})

        # 压缩过长会话
        if len(self.sessions[session_id]) > 30:
            self.sessions[session_id] = (
                [messages[0]] +  # system prompt
                self.sessions[session_id][-20:]
            )

        return reply, session_id

    def list_agents(self) -> list[dict]:
        return [
            {"name": k, **v}
            for k, v in self.agents.items()
        ]


engine = AgentEngine()

# === API 路由 ===

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/agents")
async def list_agents():
    return {"agents": engine.list_agents()}

@app.post("/agents/{agent_name}/chat")
async def agent_chat(agent_name: str, req: ChatRequest):
    if agent_name not in engine.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")

    reply, session_id = await engine.chat(
        agent_name, req.message, req.session_id
    )

    return ChatResponse(
        reply=reply,
        agent_name=agent_name,
        session_id=session_id,
    )

@app.post("/v1/chat/completions")
async def openai_compatible_chat(payload: dict):
    """OpenAI 兼容接口"""
    messages = payload.get("messages", [])
    model = payload.get("model", DEFAULT_MODEL)

    reply = await engine.call_llm(messages, model)

    return {
        "id": f"chatcmpl-{datetime.now().timestamp()}",
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop"
        }]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
