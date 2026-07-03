"""
⚙️ Admin API - Agent 管理后台接口
"""

import logging
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import load_config, save_agent_config

logger = logging.getLogger("agent-platform.admin")
router = APIRouter(prefix="/admin")


# ============================================================
# 数据模型
# ============================================================

class AgentCreate(BaseModel):
    name: str
    display_name: str = ""
    description: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = ""
    tools: list[str] = []
    max_search_rounds: int = 1
    tavily_key: str = ""

class AgentUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    enabled: Optional[bool] = None
    system_prompt: Optional[str] = None
    tools: Optional[list[str]] = None
    max_search_rounds: Optional[int] = None
    tavily_key: Optional[str] = None


# ============================================================
# API 路由
# ============================================================

@router.get("/agents")
async def list_agents():
    """列出所有 Agent"""
    agents = load_config()
    return {
        "agents": [
            {
                "name": a.name,
                "display_name": a.display_name,
                "description": a.description,
                "model": a.model,
                "temperature": a.temperature,
                "max_tokens": a.max_tokens,
                "enabled": a.enabled,
                "tools": a.tools,
                "max_search_rounds": a.max_search_rounds,
                "has_tavily_key": bool(a.tavily_key),
                "prompt_preview": a.system_prompt[:100] + "..." if len(a.system_prompt) > 100 else a.system_prompt,
            }
            for a in agents.values()
        ]
    }


@router.get("/agents/{name}")
async def get_agent(name: str):
    """获取单个 Agent 详情"""
    agents = load_config()
    a = agents.get(name)
    if not a:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' 不存在")
    return {
        "name": a.name,
        "display_name": a.display_name,
        "description": a.description,
        "model": a.model,
        "temperature": a.temperature,
        "max_tokens": a.max_tokens,
        "enabled": a.enabled,
        "tools": a.tools,
        "max_search_rounds": a.max_search_rounds,
        "has_tavily_key": bool(a.tavily_key),
        "system_prompt": a.system_prompt,
    }


@router.post("/agents")
async def create_agent(agent: AgentCreate):
    """创建新 Agent"""
    if not agent.name.strip():
        raise HTTPException(status_code=400, detail="Agent 名称不能为空")
    if not agent.system_prompt.strip():
        raise HTTPException(status_code=400, detail="System Prompt 不能为空")
    
    success = save_agent_config(agent.name, {
        "name": agent.display_name or agent.name,
        "description": agent.description,
        "model": agent.model,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "enabled": True,
        "system_prompt": agent.system_prompt,
        "tools": agent.tools,
        "max_search_rounds": agent.max_search_rounds,
        "tavily_key": agent.tavily_key,
    })
    
    if not success:
        raise HTTPException(status_code=500, detail="保存失败")
    
    return {"status": "ok", "message": f"Agent '{agent.name}' 已创建"}


@router.put("/agents/{name}")
async def update_agent(name: str, update: AgentUpdate):
    """更新 Agent 配置（改 Prompt 即时生效）"""
    agents = load_config()
    existing = agents.get(name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' 不存在")
    
    # 读取当前 yaml
    import yaml
    with open("/app/config/agents.yaml", "r") as f:
        raw = yaml.safe_load(f)
    
    agent_data = raw["agents"][name]
    update_dict = update.model_dump(exclude_none=True)
    agent_data.update(update_dict)
    raw["agents"][name] = agent_data
    
    with open("/app/config/agents.yaml", "w") as f:
        yaml.dump(raw, f, default_flow_style=False, allow_unicode=True)
    
    # 强制重载
    from core.config import load_config as reload
    reload(force=True)
    
    logger.info(f"✅ Agent '{name}' 已更新: {list(update_dict.keys())}")
    return {"status": "ok", "message": f"Agent '{name}' 已更新", "updated_fields": list(update_dict.keys())}


@router.delete("/agents/{name}")
async def delete_agent(name: str):
    """删除 Agent"""
    import yaml
    with open("/app/config/agents.yaml", "r") as f:
        raw = yaml.safe_load(f)
    
    if name not in raw.get("agents", {}):
        raise HTTPException(status_code=404, detail=f"Agent '{name}' 不存在")
    
    del raw["agents"][name]
    
    with open("/app/config/agents.yaml", "w") as f:
        yaml.dump(raw, f, default_flow_style=False, allow_unicode=True)
    
    from core.config import load_config as reload
    reload(force=True)
    
    return {"status": "ok", "message": f"Agent '{name}' 已删除"}


@router.get("/tools")
async def list_tools():
    """列出可用工具"""
    from core.tools import AVAILABLE_TOOLS
    return {
        "tools": [
            {"name": k, "name_cn": v["name"], "description": v["description"]}
            for k, v in AVAILABLE_TOOLS.items()
        ]
    }


@router.get("/stats")
async def get_stats():
    """获取用量统计"""
    from core.db import get_pool
    
    pool = await get_pool()
    if not pool:
        return {
            "mode": "单节点 (无数据库)",
            "sessions": "内存",
            "message": "配置 DATABASE_URL 启用持久化",
        }
    
    try:
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM usage_logs")
            today = await conn.fetchval(
                "SELECT COUNT(*) FROM usage_logs WHERE created_at > NOW() - INTERVAL '24 hours'"
            )
            top_agents = await conn.fetch(
                "SELECT agent_name, COUNT(*) as cnt FROM usage_logs "
                "GROUP BY agent_name ORDER BY cnt DESC LIMIT 5"
            )
        
        return {
            "mode": "PostgreSQL (多节点共享)",
            "total_requests": total,
            "last_24h": today,
            "top_agents": [{"name": r["agent_name"], "count": r["cnt"]} for r in top_agents],
        }
    except Exception as e:
        return {"mode": "数据库错误", "error": str(e)}
