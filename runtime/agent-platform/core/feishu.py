"""
🦞 飞书 MCP 工具集成 - 连接 Feishu Skills 到 Agent Platform

通过 MCP 协议调用飞书开放 API，让 Agent 能直接操作飞书。
"""

import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("agent-platform.feishu")

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

# Token 缓存
_token_cache: dict[str, Any] = {}


async def _get_tenant_token() -> str:
    """获取飞书 tenant_access_token"""
    global _token_cache
    
    import httpx
    from datetime import datetime
    
    # 检查缓存
    if _token_cache.get("expire_at", 0) > datetime.now().timestamp():
        return _token_cache["token"]
    
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        return ""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": FEISHU_APP_ID,
                    "app_secret": FEISHU_APP_SECRET,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            
            _token_cache = {
                "token": data.get("tenant_access_token", ""),
                "expire_at": datetime.now().timestamp() + data.get("expire", 7200) - 300,
            }
            return _token_cache["token"]
    except Exception as e:
        logger.error(f"飞书认证失败: {e}")
        return ""


# ============================================================
# 飞书工具定义
# ============================================================

FEISHU_TOOLS = {}

# 动态注册飞书工具的辅助函数
def register_feishu_tool(name: str, description: str, api_path: str, method: str = "GET"):
    """注册一个飞书 API 调用工具"""
    
    async def tool_func(**kwargs) -> str:
        token = await _get_tenant_token()
        if not token:
            return "⚠️ 飞书未认证，请在配置中设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET"
        
        import httpx
        
        url = f"https://open.feishu.cn/open-apis{api_path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=kwargs)
                else:
                    resp = await client.post(url, headers=headers, json=kwargs)
                resp.raise_for_status()
                data = resp.json()
                
                if data.get("code") != 0:
                    return f"⚠️ 飞书 API 错误: {data.get('msg', '未知错误')}"
                
                return json.dumps(data.get("data", {}), ensure_ascii=False, indent=2)
        except Exception as e:
            return f"⚠️ 飞书 API 调用失败: {str(e)}"
    
    # 注册到全局
    FEISHU_TOOLS[name] = {
        "name": name,
        "description": description,
        "func": tool_func,
        "schema": {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
    }


# ============================================================
# 注册常用飞书工具（按需扩展）
# ============================================================

# 文档
register_feishu_tool(
    "feishu_create_doc",
    "创建飞书文档",
    "/docx/v1/documents",
    "POST",
)

register_feishu_tool(
    "feishu_get_doc_content",
    "读取飞书文档内容",
    "/docx/v1/documents/{document_id}/raw_content",
    "GET",
)

# 多维表格
register_feishu_tool(
    "feishu_list_bitable_fields",
    "列出多维表格的字段",
    "/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
    "GET",
)

register_feishu_tool(
    "feishu_add_bitable_record",
    "向多维表格添加记录",
    "/bitable/v1/apps/{app_token}/tables/{table_id}/records",
    "POST",
)

# 消息
register_feishu_tool(
    "feishu_send_message",
    "发送飞书消息",
    "/im/v1/messages",
    "POST",
)

# 日历
register_feishu_tool(
    "feishu_create_event",
    "创建飞书日历日程",
    "/calendar/v4/calendars/{calendar_id}/events",
    "POST",
)

# 通讯录
register_feishu_tool(
    "feishu_search_user",
    "搜索飞书用户",
    "/search/v1/user",
    "POST",
)

# 审批
register_feishu_tool(
    "feishu_create_approval",
    "创建飞书审批实例",
    "/approval/v4/instances",
    "POST",
)


def get_feishu_tools() -> dict:
    """获取所有飞书工具"""
    return FEISHU_TOOLS


def get_feishu_schemas() -> list[dict]:
    """获取飞书工具的 OpenAI function calling schema"""
    return [t["schema"] for t in FEISHU_TOOLS.values()]
