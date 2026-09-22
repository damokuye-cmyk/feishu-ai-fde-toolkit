# 🦞 Feishu AI FDE Toolkit

飞书 AI 现场交付工程师工具链 — Agent 开发 + 部署平台

## 架构

```
客户 Chatbox → OpenAI API → Agent Platform → AI Gateway → LLM
                               │
                          ┌────┴────┐
                     Admin API   PostgreSQL
                          │       (无状态)
                     Admin Web UI
```

## 快速开始

```bash
# 1. 构建
bash build.sh

# 2. 部署 (Docker)
docker compose -f deploy/docker-compose.yml up -d

# 3. 部署 (K3s, 2节点)
#    Master: bash deploy/k3s/images/install-k3s-master.sh
#    Worker: bash deploy/k3s/images/install-k3s-worker.sh <MASTER_IP>
#    kubectl apply -f deploy/helm/feishu-agent/templates/
```

## 访问地址

| 服务 | 地址 |
|------|------|
| OpenAI API | `POST /v1/chat/completions` |
| Model List | `GET /v1/models` |
| 管理后台 | `/admin` |
| API 文档 | `/docs` |

## 核心特性

- ✅ **OpenAI 兼容** — 客户 Chatbox 直接对接
- ✅ **SSE 流式** — reasoning_content + content 分段输出
- ✅ **智能搜索** — LLM 判断是否需要搜索，Tavily 引擎
- ✅ **热配置** — 改 Prompt/Tavily Key 即时生效
- ✅ **无状态** — PostgreSQL 会话存储，多节点共享
- ✅ **K3s 部署** — 2 节点离线部署，安全基线内置
- ✅ **省钱** — 最多 1 轮搜索，智能触发，结果限 3 条
