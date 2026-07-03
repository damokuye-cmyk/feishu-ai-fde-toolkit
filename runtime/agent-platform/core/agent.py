"""
🤖 Agent 核心执行引擎
- SSE 流式输出: reasoning_content 放思考过程, content 放最终回答
- 智能搜索判断: LLM 自己决定是否需要搜索
- 单轮搜索: 省成本
- 无状态: 会话存数据库
"""

import os
import json
import logging
import asyncio
from typing import AsyncGenerator, Optional, Any
from datetime import datetime

from core.config import AgentConfig
from core.tools import get_tools_schemas, execute_tool
from core.db import session_store, usage_logger

logger = logging.getLogger("agent-platform.agent")

LITELLM_API_BASE = os.getenv("LITELLM_API_BASE", "http://ai-gateway:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")
USE_REASONING = os.getenv("USE_REASONING", "true").lower() == "true"


class AgentRuntime:
    """
    Agent 运行时。
    每次对话启动一个新实例，处理单个请求。
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.tool_schemas = get_tools_schemas(config.tools)
        self.messages: list[dict] = []
        self.search_performed = False  # 确保只搜一次
        self.tool_call_count = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
    
    async def _call_llm_stream(
        self, messages: list[dict], tools: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式调用 LLM，逐 chunk 产出 SSE data 行。
        产出格式已经是 SSE 的 data: 行，但这里只产出 delta 内容，
        SSE 包装由外层处理。
        """
        import httpx
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LITELLM_API_KEY}",
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{LITELLM_API_BASE}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                ) as resp:
                    if resp.status_code != 200:
                        error_text = await resp.aread()
                        yield json.dumps({
                            "error": f"LLM API 错误 ({resp.status_code}): {error_text[:200]}"
                        })
                        return
                    
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        chunk = line[6:].strip()
                        if chunk == "[DONE]":
                            yield "[DONE]"
                            return
                        
                        try:
                            data = json.loads(chunk)
                            choices = data.get("choices", [])
                            if not choices:
                                continue
                            
                            delta = choices[0].get("delta", {})
                            finish_reason = choices[0].get("finish_reason")
                            
                            # 累计 token
                            usage = data.get("usage", {})
                            if usage:
                                self.prompt_tokens = usage.get("prompt_tokens", 0)
                                self.completion_tokens = usage.get("completion_tokens", 0)
                            
                            # 检查是否有 tool_calls
                            tool_calls_delta = delta.get("tool_calls")
                            if tool_calls_delta:
                                yield json.dumps({
                                    "tool_calls": tool_calls_delta
                                })
                                continue
                            
                            content = delta.get("content", "")
                            if content:
                                yield json.dumps({"content": content})
                            
                            if finish_reason:
                                yield json.dumps({"finish_reason": finish_reason})
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"LLM 流式调用失败: {e}")
                yield json.dumps({"error": str(e)})
    
    # --- 非流式 LLM 调用 (用于判断阶段) ---
    
    async def _call_llm_sync(self, messages: list[dict]) -> dict:
        """非流式调用，用于判断是否需要搜索"""
        import httpx
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.1,  # 低温度提高判断准确性
            "max_tokens": 512,
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LITELLM_API_KEY}",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{LITELLM_API_BASE}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                
                msg = data["choices"][0]["message"]
                self.prompt_tokens += data.get("usage", {}).get("prompt_tokens", 0)
                self.completion_tokens += data.get("usage", {}).get("completion_tokens", 0)
                
                # 检查 tool_calls
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    return {"role": "assistant", "tool_calls": tool_calls}
                
                return {"role": "assistant", "content": msg.get("content", "")}
                
        except Exception as e:
            logger.error(f"LLM 同步调用失败: {e}")
            return {"role": "assistant", "content": f"⚠️ 服务异常: {str(e)}"}
    
    # ============================================================
    # 主入口
    # ============================================================
    
    async def chat_stream(
        self, user_message: str, session_id: str
    ) -> AsyncGenerator[str, None]:
        """
        流式 Agent 对话。
        
        SSE 格式 (兼容 Chatbox 的 reasoning_content):
        ```
        data: {"choices":[{"delta":{"role":"assistant","reasoning_content":"思考过程"},"index":0}]}
        data: {"choices":[{"delta":{"content":"最终回答"},"index":0}]}
        data: [DONE]
        ```
        """
        
        # 1. 加载会话历史
        history = await session_store.get_messages(session_id)
        if not history:
            history = [{"role": "system", "content": self.config.system_prompt}]
        
        history.append({"role": "user", "content": user_message})
        self.messages = history
        
        # 2. 流式输出准备
        reasoning_messages = []
        
        # --- 阶段 A: 判断是否需要搜索 ---
        
        if self.tool_schemas and not self.search_performed:
            yield _sse_reasoning("🤔 分析是否需要搜索...")
            
            # 用低温度调 LLM 判断
            judge_msgs = [
                history[0],  # system prompt
                {"role": "user", "content": f"用户提问: {user_message}\n\n请判断：是否需要联网搜索来获取最新信息才能回答这个问题？如果是常识性问题、已有知识能回答的，不需要搜索。请用 tool_call 调用 tavily_search 或直接回答。"}
            ]
            
            judge_result = await self._call_llm_sync(judge_msgs)
            tool_calls = judge_result.get("tool_calls", [])
            
            if tool_calls:
                yield _sse_reasoning("🔍 需要联网搜索...")
                self.search_performed = True
                
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "")
                    args_str = tc.get("function", {}).get("arguments", "{}")
                    try:
                        args = json.loads(args_str)
                    except:
                        args = {}
                    
                    query = args.get("query", user_message)
                    yield _sse_reasoning(f"🔍 搜索: {query}")
                    
                    # 执行 Tavily 搜索
                    result = await execute_tool(
                        name, args,
                        tavily_key=self.config.tavily_key,
                    )
                    
                    yield _sse_reasoning(f"📥 获取到搜索结果")
                    
                    # 将搜索结果注入消息
                    self.messages.append({
                        "role": "assistant",
                        "content": f"我已搜索了相关信息",
                    })
                    self.messages.append({
                        "role": "user",
                        "content": f"基于以下搜索结果回答用户问题:\n\n{result}\n\n用户原问题: {user_message}",
                    })
            else:
                yield _sse_reasoning("✅ 无需搜索，直接回答")
        
        # --- 阶段 B: 流式生成最终回答 ---
        
        yield _sse_reasoning("✍️ 正在生成回答...")
        
        # 开始流式回答
        full_content = ""
        async for chunk in self._call_llm_stream(self.messages):
            if chunk == "[DONE]":
                break
            
            try:
                data = json.loads(chunk)
                
                # tool_calls 处理 (理论上不走了, 但保留防御)
                if "tool_calls" in data and not self.search_performed:
                    self.search_performed = True
                    # ... 简化处理, 同轮次不会再有 tool_call
                    continue
                
                if "content" in data:
                    text = data["content"]
                    full_content += text
                    yield _sse_content(text)
                    
                if "finish_reason" in data:
                    pass
                    
            except json.JSONDecodeError:
                continue
        
        # 3. 保存会话
        self.messages.append({"role": "assistant", "content": full_content})
        
        # 压缩: 保留 system + 最近 10 轮
        if len(self.messages) > 22:
            compressed = [self.messages[0]] + self.messages[-20:]
            self.messages = compressed
        
        await session_store.save_messages(session_id, self.messages)
        
        # 4. 记录用量
        await usage_logger.log(
            agent_name=self.config.name,
            session_id=session_id,
            model=self.config.model,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            tool_calls=self.tool_call_count,
            searched=self.search_performed,
        )
        
        # 5. DONE
        yield "[DONE]"


# ============================================================
# SSE 格式化辅助函数
# ============================================================

def _sse_reasoning(text: str) -> str:
    """输出 reasoning_content 的 SSE 行"""
    payload = {
        "choices": [{
            "delta": {
                "role": "assistant",
                "reasoning_content": text,
            },
            "index": 0,
        }]
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}"


def _sse_content(text: str) -> str:
    """输出 content 的 SSE 行"""
    payload = {
        "choices": [{
            "delta": {
                "content": text,
            },
            "index": 0,
        }]
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}"
