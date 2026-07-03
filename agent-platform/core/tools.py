"""
🤖 工具定义 - 所有 Agent 可用的工具
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger("agent-platform.tools")


# ============================================================
# 1. 联网搜索工具
# ============================================================

async def web_search(query: str, max_results: int = 5) -> str:
    """
    通过 DuckDuckGo 搜索互联网，获取最新信息。
    适用于: 实时新闻、技术文档、产品信息、行业动态等需要联网获取的场景。
    
    Args:
        query: 搜索关键词
        max_results: 返回结果数量 (1-10)
    
    Returns:
        搜索结果摘要，包含标题、摘要和来源
    """
    try:
        from duckduckgo_search import DDGS
        
        logger.info(f"🌐 搜索: {query}")
        results = []
        
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=min(max_results, 10))):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                })
        
        if not results:
            return f"🔍 搜索 \"{query}\" 未找到结果，请尝试更换关键词。"
        
        output = f"🔍 搜索 \"{query}\" 共 {len(results)} 条结果:\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r['title']}\n"
            output += f"   {r['snippet'][:200]}{'...' if len(r['snippet']) > 200 else ''}\n"
            output += f"   来源: {r['url']}\n\n"
        
        return output.strip()
    
    except ImportError:
        return "❌ 搜索依赖未安装: pip install duckduckgo-search"
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return f"⚠️ 搜索暂时不可用: {str(e)}"


# ============================================================
# 2. 网页内容提取工具
# ============================================================

async def web_fetch(url: str) -> str:
    """
    抓取指定 URL 的网页内容并提取正文文本。
    适用于: 阅读新闻全文、技术文章、产品详情页等。
    
    Args:
        url: 要抓取的网页 URL
    
    Returns:
        网页正文文本内容
    """
    import httpx
    from bs4 import BeautifulSoup
    
    try:
        logger.info(f"📄 抓取: {url}")
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "lxml")
        
        # 移除无用元素
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        text = soup.get_text(separator="\n", strip=True)
        # 清理多余空行
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines[:200])  # 最多 200 行
        
        if len(text) > 8000:
            text = text[:8000] + "\n\n... (内容已截断)"
        
        return f"📄 {url} 的内容:\n\n{text}"
    
    except Exception as e:
        return f"⚠️ 抓取失败: {str(e)}"


# ============================================================
# 3. 工具注册表
# ============================================================

AVAILABLE_TOOLS = {
    "web_search": {
        "name": "联网搜索",
        "description": "搜索互联网获取最新信息，支持新闻、技术文档、行业动态等",
        "func": web_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "搜索互联网，获取最新信息。当你需要实时/最新数据时调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词，尽量精确"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "返回结果数量，默认 5",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    },
    "web_fetch": {
        "name": "网页抓取",
        "description": "抓取指定 URL 的网页正文内容",
        "func": web_fetch,
        "schema": {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "抓取网页全文内容。当你需要阅读完整文章或技术文档时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "网页 URL"
                        }
                    },
                    "required": ["url"]
                }
            }
        }
    }
}


def get_tools_schemas(tool_names: list[str]) -> list[dict]:
    """根据工具名列表返回 OpenAI 工具 schema"""
    schemas = []
    for name in tool_names:
        if name in AVAILABLE_TOOLS:
            schemas.append(AVAILABLE_TOOLS[name]["schema"])
    return schemas


async def execute_tool(name: str, args: dict[str, Any]) -> str:
    """执行指定工具"""
    tool = AVAILABLE_TOOLS.get(name)
    if not tool:
        return f"❌ 未知工具: {name}"
    return await tool["func"](**args)
