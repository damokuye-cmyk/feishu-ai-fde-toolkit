"""
🤖 Agent 配置模型 - 支持热加载，修改即时生效
"""

import os
import yaml
import hashlib
import logging
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger("agent-platform.config")

CONFIG_PATH = os.getenv("AGENT_CONFIG_PATH", "/app/config/agents.yaml")

# 全局缓存
_loaded_config: dict[str, Any] = {}
_config_mtime: float = 0
_config_hash: str = ""


class AgentConfig:
    """单个 Agent 的配置"""
    
    def __init__(self, name: str, data: dict):
        self.name = name
        self.display_name = data.get("name", name)
        self.description = data.get("description", "")
        self.model = data.get("model", "deepseek-chat")
        self.temperature = data.get("temperature", 0.7)
        self.max_tokens = data.get("max_tokens", 4096)
        self.enabled = data.get("enabled", True)
        self.system_prompt = data.get("system_prompt", "")
        self.tools = data.get("tools", [])
        self.max_search_rounds = data.get("max_search_rounds", 1)
        self.tavily_key = data.get("tavily_key", "")


def load_config(force: bool = False) -> dict[str, AgentConfig]:
    """
    加载 Agent 配置，支持热更新。
    检测文件变更自动重载，无需重启。
    
    Args:
        force: 强制重新加载
        
    Returns:
        {agent_name: AgentConfig}
    """
    global _loaded_config, _config_mtime, _config_hash
    
    try:
        current_mtime = os.path.getmtime(CONFIG_PATH)
        current_hash = _file_hash(CONFIG_PATH)
        
        if not force and current_mtime <= _config_mtime and current_hash == _config_hash:
            return _loaded_config
        
        with open(CONFIG_PATH, "r") as f:
            raw = yaml.safe_load(f)
        
        agents_config = raw.get("agents", {})
        result = {}
        for name, data in agents_config.items():
            if data.get("enabled", True):
                result[name] = AgentConfig(name, data)
        
        _loaded_config = result
        _config_mtime = current_mtime
        _config_hash = current_hash
        
        logger.info(f"📋 已加载 {len(result)} 个 Agent: {list(result.keys())}")
        
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        if not _loaded_config:
            _loaded_config = {}
    
    return _loaded_config


def save_agent_config(name: str, data: dict) -> bool:
    """
    保存单个 Agent 配置，立即生效。
    这是 Admin API 调用的入口。
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            raw = yaml.safe_load(f) or {}
        
        if "agents" not in raw:
            raw["agents"] = {}
        
        raw["agents"][name] = data
        
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(raw, f, default_flow_style=False, allow_unicode=True)
        
        # 强制重载
        load_config(force=True)
        logger.info(f"✅ Agent '{name}' 配置已更新")
        return True
        
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False


def _file_hash(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return ""
