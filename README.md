# 🦞 Feishu AI FED Toolkit

## 飞书 AI 现场交付工程师工具链

> **一句话：到客户现场，一条命令拉起全套 AI 基础设施。**

---

## 📦 包含组件

| 组件 | 技术栈 | 用途 |
|------|--------|------|
| **🦞 OpenClaw** | 飞书官方插件 | 让 AI Agent 接入飞书生态 |
| **🤖 Agent Platform** | Langgraph + FastAPI | 编排 AI Agent 工作流 |
| **🌐 AI Gateway** | LiteLLM Proxy | 多模型路由、负载均衡、降级 |
| **📊 Monitoring** | Grafana + Prometheus | 日志、用量、性能监控 |
| **🎯 Demo Scenarios** | Python + YAML | 制造业开箱即用场景 |

---

## 🚀 快速启动

### 前置条件

- Docker & Docker Compose v2+
- 至少 8GB 内存
- Linux / macOS

### 一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

### 部署检查

```bash
./scripts/health-check.sh
```

---

## 📁 目录结构

```
feishu-ai-fed-toolkit/
├── deploy.sh                    # 主控部署脚本
├── config/                      # 全局配置
│   ├── .env.example
│   └── models.yaml              # AI 模型配置
│
├── agent-platform/              # AI Agent 平台
│   ├── docker-compose.yml
│   ├── agents/                  # 预置 Agent 示例
│   │   ├── manufacturing-agent/ # 制造业 Agent
│   │   └── rag-agent/           # 知识库问答 Agent
│   └── config/
│
├── ai-gateway/                  # AI 网关 (LiteLLM)
│   ├── docker-compose.yml
│   └── config.yaml
│
├── openclaw/                    # 小龙虾插件
│   ├── setup-guide.md
│   └── config-templates/
│
├── monitoring/                  # 可观测性
│   ├── docker-compose.yml
│   ├── prometheus.yml
│   └── grafana-dashboards/
│
├── demo-scenarios/              # 行业演示场景
│   └── manufacturing/
│       ├── quality-inspection/  # 质量检测
│       ├── equipment-alert/     # 设备告警
│       └── production-schedule/ # 生产排程
│
└── scripts/                     # 辅助脚本
    ├── health-check.sh
    ├── install-docker.sh
    └── demo-quickstart.sh
```

---

## 🔧 核心组件说明

### 1. 🦞 OpenClaw 小龙虾

飞书官方 AI 插件系统。部署后 AI Agent 能直接：
- 读取飞书文档、知识库
- 操作飞书多维表格
- 发送飞书消息通知
- 调用飞书审批流

### 2. 🤖 Agent Platform

基于 Langgraph 的 Agent 编排平台。预置：
- **联网搜索 Agent**（多语种意图判断）
- **RAG 知识库 Agent**（对接企业文档）
- **制造业异常告警 Agent**（示例）

### 3. 🌐 AI Gateway

基于 LiteLLM Proxy，提供：
- OpenAI 兼容 API
- 多模型负载均衡
- 故障自动降级
- Token 用量追踪
- API Key 管理

### 4. 📊 Monitoring

Grafana + Prometheus 看板：
- LLM 请求量 / 延迟 / 错误率
- Agent 执行链路追踪
- Token 消耗统计

---

## 🎯 制造业演示场景

| 场景 | 说明 | 涉及组件 |
|------|------|---------|
| 质量检测告警 | 生产缺陷实时通知+根因分析 | Agent + 飞书消息 |
| 设备巡检 | 巡检记录自动录入多维表格 | OpenClaw + Bitable |
| 生产排程 | AI 辅助排产建议 | Agent + AI Gateway |
| 知识库问答 | 工艺文档智能问答 | RAG Agent |

---

## 📋 客户现场检查清单

- [ ] Docker & Compose 就绪
- [ ] 客户网络可访问大模型 API
- [ ] 飞书开放平台已配置 App
- [ ] 至少 8GB 可用内存
- [ ] 演示数据已导入
