"""
🤖 Agent 基类 - 基于 Langgraph 的工具调用 Agent
"""

import json
import logging
import hashlib
from typing import Any, Optional
from datetime import datetime

from core.llm import chat_completion
from core.tools import get_tools_schemas, execute_tool

logger = logging.getLogger("agent-platform.agents")

# Langgraph 类型注解 (运行时不需要实际导入，保持轻量)
# 实际使用 TypedDict 模拟 State


class AgentState(dict):
    """Agent 状态"""
    messages: list[dict]
    next_action: str  # "call_llm" | "execute_tool" | "respond"
    pending_tool_calls: list[dict]
    tool_results: list[dict]
    context: dict[str, Any]


def make_default_state() -> AgentState:
    return {
        "messages": [],
        "next_action": "call_llm",
        "pending_tool_calls": [],
        "tool_results": [],
        "context": {},
    }


class BaseAgent:
    """
    Agent 基类
    
    子类只需实现:
    - name: str
    - description: str
    - system_prompt: str
    - tools: list[str]  # 工具名列表
    """

    name: str = "base"
    description: str = "Base Agent"
    system_prompt: str = "You are a helpful AI assistant."
    tools: list[str] = []

    def __init__(self):
        self.sessions: dict[str, AgentState] = {}
        self.tool_schemas = get_tools_schemas(self.tools)

    def _session_id(self, session_id: Optional[str] = None) -> str:
        if not session_id:
            raw = f"{self.name}_{datetime.now().timestamp()}_{id(self)}"
            session_id = hashlib.md5(raw.encode()).hexdigest()[:16]
        return session_id

    def _get_or_create_state(self, session_id: str, context: Optional[dict] = None) -> AgentState:
        if session_id not in self.sessions:
            state = make_default_state()
            state["messages"] = [{"role": "system", "content": self.system_prompt}]
            if context:
                state["context"] = context
            self.sessions[session_id] = state
        return self.sessions[session_id]

    def _compress_session(self, state: AgentState):
        """压缩会话，保留 system prompt + 最近 20 轮"""
        msgs = state["messages"]
        if len(msgs) > 40:
            state["messages"] = [msgs[0]] + msgs[-20:]

    async def chat(self, message: str, session_id: Optional[str] = None,
                   context: Optional[dict] = None) -> tuple[str, str, Optional[str]]:
        """
        处理用户消息，返回 (回复内容, session_id, 思考过程)
        """
        sid = self._session_id(session_id)
        state = self._get_or_create_state(sid, context)

        # 添加用户消息
        state["messages"].append({"role": "user", "content": message})

        thinking_log = []
        max_rounds = 5  # 最多 5 轮工具调用

        for round_idx in range(max_rounds):
            thinking_log.append(f"\n--- 第 {round_idx+1} 轮 LLM 调用 ---")

            # 调用 LLM
            result = await chat_completion(
                messages=state["messages"],
                tools=self.tool_schemas if self.tool_schemas else None,
            )

            state["messages"].append({
                "role": result["role"],
                "content": result["content"] or "",
            })

            # 记录思考
            if result["content"]:
                thinking_log.append(f"🤔 思考: {result['content'][:200]}")

            # 检查是否有工具调用
            tool_calls = result.get("tool_calls", [])
            if not tool_calls:
                thinking_log.append("✅ 无需工具调用，直接回复")
                break

            # 执行工具
            thinking_log.append(f"🔧 需要执行 {len(tool_calls)} 个工具:")
            for tc in tool_calls:
                thinking_log.append(f"  -> {tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})")
                
                tool_result = await execute_tool(tc["name"], tc["args"])
                
                # 将工具结果作为 function call 结果追加
                state["messages"].append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result,
                })
                thinking_log.append(f"  ✅ 结果: {tool_result[:150]}...")
        else:
            thinking_log.append("\n⚠️ 达到最大工具调用轮数")

        # 获取最终回复
        reply = state["messages"][-1]["content"] if state["messages"] else ""
        
        # 压缩会话
        self._compress_session(state)
        
        thinking_text = "\n".join(thinking_log)
        logger.info(f"Agent {self.name} 回复完成, session={sid}")
        
        return reply, sid, thinking_text

    def list_capabilities(self) -> list[str]:
        """返回能力列表"""
        return [t["name"] for t in get_tools_schemas(self.tools)]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "capabilities": self.list_capabilities(),
        }
