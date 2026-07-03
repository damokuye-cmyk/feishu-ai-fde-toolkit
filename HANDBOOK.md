# 🦞 Feishu AI FED Toolkit - 现场交付操作手册

> 版本: 2.0 | 最后更新: 2026-07-03
> 作者: 黄龙 | 角色: 飞书解决方案专家（华南区）

---

## 一、架构总览

```
客户 Chatbox (OpenAI协议)
    │ POST /v1/chat/completions
    ▼
┌─────────────────────────────────────────────┐
│         Agent Platform (你的服务)             │
│                                              │
│  ① 匹配 Agent → 加载 Prompt + 配置            │
│  ② LLM 判断: 需要搜索? → Tavily 搜索 (1轮)    │
│  ③ SSE 流式返回: reasoning_content + content  │
│  ④ 会话存 PostgreSQL (无状态, 多节点共享)      │
└──────────┬──────────────────────────────────┘
           │
           ├──→ AI Gateway (LiteLLM) → DeepSeek / Qwen / GPT
           │
           └──→ (可选) 飞书 MCP → 飞书开放 API
```

### 管理后台

```
浏览器打开 http://<服务器IP>:8000/admin

功能:
├── 📋 Agent 列表 — 查看/选择
├── ✏️ 编辑 — 改 Prompt / 模型 / Temperature / 工具
├── 💬 在线测试 — 对话调试
├── 🔧 工具管理 — Tavily Key 热替换
└── 📊 统计 — 请求量 / Token 用量
```

---

## 二、部署流程（去客户现场）

### 阶段 1: 出发前（你电脑上）

```bash
# 克隆最新代码
git clone https://github.com/damokuye-cmyk/feishu-ai-fed-toolkit
cd feishu-ai-fed-toolkit

# 构建所有镜像 + 打包
bash build.sh

# → 产物: packages/feishu-ai-fed-toolkit_日期.tar.gz
# → 把这文件带走（U盘 / 网盘 / scp）
```

### 阶段 2: 到客户现场

```bash
# 把包传到客户服务器
scp packages/*.tar.gz your-user@客户服务器IP:~/

# 登录客户服务器
ssh your-user@客户服务器IP

# 解压
tar xzf feishu-ai-fed-toolkit_日期.tar.gz
cd build_日期

# 加载 Docker 镜像
cd images
for f in *.tar; do
    echo "加载 $f..."
    docker load -i "$f"
done
cd ..

# 创建配置
cp config/.env.example config/.env
vi config/.env   # 填入 API Key

# ====== 配置要点 ======
# DEEPSEEK_API_KEY=sk-xxx     ← 必填
# TAVILY_API_KEY=tvly-xxx     ← 选填，不填也能启动，搜索不能用
# FEISHU_APP_ID=cli_xxx       ← 选填，要用飞书 MCP 工具时填
# FEISHU_APP_SECRET=xxx       ← 选填
# LITELLM_MASTER_KEY=sk-xxx  ← 必填

# 启动（Docker Compose）
docker compose up -d

# 验证
curl http://localhost:8000/health
# → {"status":"ok","agents":3,"agent_list":["web-search","manufacturing","rag"]}

curl http://localhost:8000/v1/models
# → 返回所有 Agent 列表

# 测试对话
curl -X POST http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"web-search","messages":[{"role":"user","content":"你好"}],"stream":true}'
```

### 阶段 3: 管理后台配置

```
1. 浏览器打开 http://<客户服务器IP>:8000/admin
2. 编辑 Agent → 改 Prompt → 保存（即时生效）
3. 测试 Tab → 输入消息测试
4. 如需 Tavily → 编辑 Agent → 填入 Key → 保存
```

### 阶段 4: 对接客户 Chatbox

```
告诉客户 IT 人员:

Chatbox 配置:
  提供商: OpenAI 兼容
  API 地址: http://<服务器IP>:8000/v1
  API Key: 随便填（目前不校验）
  模型: web-search (或你在管理后台配的 Agent 名)
```

---

## 三、Agent 管理

### 管理后台能做的事

| 操作 | 路径 | 生效方式 |
|------|------|---------|
| 改 Prompt | Admin → 编辑 → 修改 → 保存 | ✅ 即时生效 |
| 改 Temperature | Admin → 编辑 → 修改 → 保存 | ✅ 即时生效 |
| 改模型 (deepseek-chat/gpt-4o) | Admin → 编辑 → 修改 → 保存 | ✅ 即时生效 |
| 开/关搜索工具 | Admin → 编辑 → 勾选 → 保存 | ✅ 即时生效 |
| 填 Tavily Key | Admin → 编辑 → 填入 → 保存 | ✅ 即时生效 |
| 新建 Agent | 左侧 → +新建 → 填名称/Prompt | ✅ 即时生效 |
| 删除 Agent | 编辑 → 删除 | ✅ 即时生效 |
| 在线测试 | Admin → 测试 Tab → 输入消息 | ✅ 实时 |

### 文件配置方式（紧急时用）

```yaml
# config/agents.yaml - 修改后即时生效
agents:
  web-search:
    name: "联网搜索助手"
    enabled: true
    model: "deepseek-chat"
    temperature: 0.7
    max_search_rounds: 1     # 省钱: 最多搜1轮
    tavily_key: ""           # 支持热替换
    tools: ["tavily_search"]
    system_prompt: |
      你是专业的联网搜索 AI 助手...
```

---

## 四、省钱策略（内置）

| 策略 | 说明 |
|------|------|
| 最多搜 1 轮 | 一次对话最多一次 Tavily 调用 |
| 智能触发 | LLM 自己判断值不值得搜，常识不搜 |
| 结果限 3 条 | 一次搜索只取前 3 条，减少 token 消耗 |
| Tavily basic 模式 | 选 basic depth，比 deep 便宜 5 倍 |
| 缓存 | 相同 query 24h 内直接命中（待实现） |

---

## 五、K3s 集群部署（客户要求高可用时）

### 安装

```bash
# 在客户服务器上
# 先下载 K3s 离线包（有网的机器）
bash deploy/k3s/download.sh

# Master 节点
bash deploy/k3s/images/install-k3s-master.sh

# Worker 节点（填 Master IP）
bash deploy/k3s/images/install-k3s-worker.sh <MASTER_IP>

# 部署应用
kubectl apply -f deploy/helm/feishu-agent/templates/

# 查看状态
kubectl -n feishu-agent get pods -o wide
# → feishu-agent-xxx   1/1   Running   Node1
# → feishu-agent-yyy   1/1   Running   Node2  ← 2副本分布在不同节点
```

### 安全基线

详见 `deploy/security/baseline.md`

主要配置:
- 容器以非 root 用户运行 (UID 1000)
- 只读根文件系统 (readOnlyRootFilesystem: true)
- 禁止提权 (allowPrivilegeEscalation: false)
- 删除所有 Linux 能力 (drop: ["ALL"])
- 默认 seccomp 配置
- 资源限制 (CPU/Memory)

---

## 六、飞书 Skills（开发工具用）

```bash
# 在你的开发电脑上安装
npx skills add https://open.feishu.cn

# 然后 Claude Code / Cursor 就能操作飞书了
# 用于你开发 Demo、写集成脚本时用
```

28 个 Skill 详见 `docs/feishu-skills-integration.md`

---

## 七、常见问题

### Q: 客户说没有网络，怎么部署？
A: 用 build.sh 在有网的机器上打包，把 tar.gz 带到客户环境。所有镜像都已打包在 images/ 里。

### Q: Tavily Key 没配置会怎样？
A: Agent 启动正常，搜索功能不可用。LLM 判断需要搜索时会返回提示。客户可以在管理后台热填 Key。

### Q: 客户想把 Agent 部署到 K8s，不用 Docker Compose？
A: 用 deploy/helm/feishu-agent/templates/，支持 2 副本、反亲和、安全上下文。

### Q: 想加一个新的自定义 Agent？
A: 两种方式:
1. 管理后台 → +新建 Agent → 填 Prompt → 保存（不需要写代码）
2. 直接编辑 config/agents.yaml → 添加一段配置 → 保存

### Q: 客户 Chatbox 支持流式输出吗？
A: 支持。SSE 流式，reasoning_content 放思考过程，content 放最终回答。

---

## 八、联系方式 & 备注

```
姓名: 黄龙
手机: 18907186930
邮箱: kumcy@qq.com
GitHub: github.com/damokuye-cmyk/feishu-ai-fed-toolkit

薪资目标: 总包 156~169 万 (20~30% 增幅)
对标职级: 字节 2-2 (对应阿里 P8)
年龄: 1985年生
```
