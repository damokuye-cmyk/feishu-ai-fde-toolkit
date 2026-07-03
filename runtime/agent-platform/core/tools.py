"""
🔧 工具层 - Tavily 搜索引擎 (主) + 联网搜索判断
"""

import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("agent-platform.tools")


async def tavily_search(query: str, api_key: str = "", max_results: int = 3) -> str:
    """
    Tavily 搜索引擎 (主搜索工具)
    费用: ~$1/1000次查询
    
    Args:
        query: 搜索关键词
        api_key: Tavily API Key (支持热替换)
        max_results: 返回结果数 (1-5)
    """
    import httpx
    
    key = api_key or os.getenv("TAVILY_API_KEY", "")
    if not key:
        return "⚠️ Tavily API Key 未配置。请在管理后台 → 工具配置 中填入 Tavily Key，或联系管理员。"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": key,
                    "query": query,
                    "max_results": min(max_results, 5),
                    "include_answer": "basic",  # 附带 AI 摘要
                    "include_raw_content": False,
                    "search_depth": "basic",     # basic 更便宜
                },
            )
            resp.raise_for_status()
            data = resp.json()
        
        results = data.get("results", [])
        answer = data.get("answer", "")
        
        if not results:
            return f"🔍 搜索 '{query}' 暂无结果。"
        
        lines = [f"🔍 搜索 '{query}' 结果:\n"]
        
        # Tavily AI 摘要
        if answer:
            lines.append(f"📝 AI 摘要: {answer}\n")
        
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            snippet = r.get("content", "")[:200]
            url = r.get("url", "")
            score = r.get("score", 0)
            lines.append(f"{i}. {title}")
            lines.append(f"   {snippet}{'...' if len(r.get('content', '')) > 200 else ''}")
            lines.append(f"   来源: {url}")
            lines.append("")
        
        return "\n".join(lines).strip()
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "⚠️ Tavily API Key 无效，请在管理后台更新。"
        return f"⚠️ 搜索服务暂时不可用 (HTTP {e.response.status_code})"
    except Exception as e:
        logger.error(f"Tavily 搜索失败: {e}")
        return f"⚠️ 搜索服务异常: {str(e)}"


# ============================================================
# 工具注册表
# ============================================================

AVAILABLE_TOOLS = {
    "tavily_search": {
        "name": "Tavily 搜索",
        "description": "联网搜索 (推荐), 支持 AI 摘要, 单次查询约 $0.001",
        "func": tavily_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "tavily_search",
                "description": "搜索互联网获取最新实时信息。当你需要查询新闻、技术动态、行业数据等实时内容时调用此工具。常识性问题无需调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词，尽量精确"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "返回结果数，最多 5 条",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    },
}


def get_tools_schemas(tool_names: list[str]) -> list[dict]:
    """获取工具的 OpenAI function calling schema"""
    return [
        AVAILABLE_TOOLS[n]["schema"]
        for n in tool_names
        if n in AVAILABLE_TOOLS
    ]


async def execute_tool(name: str, args: dict[str, Any],
                       tavily_key: str = "") -> str:
    """执行指定工具"""
    if name == "tavily_search":
        return await tavily_search(
            query=args.get("query", ""),
            api_key=tavily_key,
            max_results=args.get("max_results", 3),
        )
    return f"❌ 未知工具: {name}"
