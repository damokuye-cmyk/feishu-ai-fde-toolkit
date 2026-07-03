"""
🗄️ 数据库层 - 使 Agent 平台无状态化
存储: 会话历史 / Agent 配置变更记录 / 用量统计

所有配置热更新走文件 (agents.yaml)
会话和日志走 PostgreSQL
"""

import os
import json
import logging
from typing import Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger("agent-platform.db")

DATABASE_URL = os.getenv("DATABASE_URL", "")

# 连接池
_pool = None


async def get_pool():
    """获取数据库连接池"""
    global _pool
    if _pool is None and DATABASE_URL:
        try:
            import asyncpg
            _pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            logger.info("🗄️ 数据库连接池已建立")
        except Exception as e:
            logger.warning(f"数据库连接失败, 使用内存模式: {e}")
    return _pool


# ============================================================
# 会话存储 - 支持多节点共享
# ============================================================

class SessionStore:
    """
    会话存储。
    有 DB: 存 PostgreSQL，多节点共享
    无 DB: 存内存（单节点降级模式）
    """
    
    def __init__(self):
        self._memory: dict[str, list[dict]] = {}
        self._memory_ttl: dict[str, datetime] = {}
        self.ttl = timedelta(hours=24)
    
    async def get_messages(self, session_id: str) -> list[dict]:
        """获取会话消息"""
        pool = await get_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT messages FROM sessions WHERE session_id = $1", session_id
                    )
                    if row:
                        return json.loads(row["messages"])
            except Exception as e:
                logger.warning(f"DB 读取会话失败: {e}")
        
        # 内存降级
        if session_id in self._memory:
            if datetime.now() - self._memory_ttl.get(session_id, datetime.min) < self.ttl:
                return self._memory[session_id]
            else:
                del self._memory[session_id]
        return []
    
    async def save_messages(self, session_id: str, messages: list[dict]):
        """保存会话消息"""
        pool = await get_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """INSERT INTO sessions (session_id, messages, updated_at)
                           VALUES ($1, $2, NOW())
                           ON CONFLICT (session_id) DO UPDATE
                           SET messages = $2, updated_at = NOW()""",
                        session_id, json.dumps(messages, ensure_ascii=False),
                    )
                return
            except Exception as e:
                logger.warning(f"DB 保存会话失败: {e}")
        
        # 内存降级
        self._memory[session_id] = messages
        self._memory_ttl[session_id] = datetime.now()
        
        # 清理过期会话
        self._cleanup_expired()
    
    def _cleanup_expired(self):
        now = datetime.now()
        expired = [
            k for k, v in self._memory_ttl.items()
            if now - v >= self.ttl
        ]
        for k in expired:
            del self._memory[k]
            del self._memory_ttl[k]


# ============================================================
# 用量日志 - 计费/审计
# ============================================================

class UsageLogger:
    """用量日志记录"""
    
    async def log(
        self,
        agent_name: str,
        session_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        tool_calls: int,
        searched: bool,
    ):
        """记录一次对话的用量"""
        pool = await get_pool()
        if not pool:
            return
        
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO usage_logs
                       (agent_name, session_id, model, prompt_tokens,
                        completion_tokens, tool_calls, searched, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())""",
                    agent_name, session_id, model,
                    prompt_tokens, completion_tokens,
                    tool_calls, searched,
                )
        except Exception as e:
            logger.warning(f"用量日志写入失败: {e}")


# ============================================================
# 数据库初始化 (用于 Helm chart 的 init container)
# ============================================================

INIT_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    messages JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_logs (
    id BIGSERIAL PRIMARY KEY,
    agent_name TEXT NOT NULL,
    session_id TEXT,
    model TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    tool_calls INTEGER DEFAULT 0,
    searched BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_agent ON usage_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);

-- 自动清理 7 天前的会话
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions WHERE updated_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;
"""

# ============================================================
# 全局实例
# ============================================================

session_store = SessionStore()
usage_logger = UsageLogger()
