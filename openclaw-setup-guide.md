# 🦞 OpenClaw (小龙虾) 飞书 AI 插件 - 部署指南

## 什么是 OpenClaw？

OpenClaw 是飞书官方推出的 AI 插件系统，让 AI Agent 能够：
- 读取飞书文档、知识库
- 操作多维表格（Bitable）
- 发送/监听飞书消息
- 触发审批流程
- 调用开放平台 API

**一句话：** 让 AI 更懂你的工作、直接帮你干活。

---

## 部署前准备

在客户现场部署前，先在飞书开放平台完成以下配置：

```
1. 登录 https://open.feishu.cn/
2. 创建「企业自建应用」
3. 记录 App ID 和 App Secret
4. 开通必要权限
```

### 必要权限清单

| 权限代码 | 用途 |
|---------|------|
| `im:message` | 消息收发 |
| `docx:document` | 文档读写 |
| `bitable:app` | 多维表格操作 |
| `drive:drive` | 云盘文件访问 |
| `search:search` | 全局搜索 |

---

## 云端版部署（推荐）

无需自建服务，直接在飞书内配置：

```bash
# 1. 访问 OpenClaw 平台
open https://openclaw.feishu.cn/

# 2. 用飞书账号登录

# 3. 创建 Agent 团队
#    配置 Agent 名称、描述、头像

# 4. 安装插件（可选）
#    飞书应用目录中搜索「OpenClaw」安装

# 5. 配置 Agent 能力
```

### 配置示例

```yaml
agent:
  name: "制造助手"
  description: "飞书制造行业 AI Agent"
  capabilities:
    - type: bitable
      tables: ["生产台账", "设备巡检", "质量检测表"]
    - type: document
      scope: ["知识库/工艺规范"]
    - type: message
      features: ["群聊监听", "关键词告警", "定时推送"]
```

---

## 私有化部署（仅限有自建需求时使用）

```bash
# 1. 下载 CLI
curl -O https://openclaw.feishu.cn/cli/openclaw

# 2. 初始化
./openclaw init \
    --app-id=$FEISHU_APP_ID \
    --app-secret=$FEISHU_APP_SECRET

# 3. 配置监听事件
#    开放平台 → 应用 → 事件与回调
#    添加: im.message.receive_v1
#          drive.file.create_v1

# 4. 启动
./openclaw start
```

---

## 制造业典型场景

### 场景 1: 设备异常自动告警

```
传感器检测到温度异常
    ↓ 飞书群聊收到告警
    ↓ Agent 查询 Bitable 历史数据
    ↓ Agent 分析根因 + 生成处理建议
    ↓ 自动创建维修工单（飞书文档）
    ↓ @责任人 跟踪闭环
```

### 场景 2: 巡检记录自动化

```
巡检员群聊发送巡检照片
    ↓ Agent 识别图片内容
    ↓ Agent 填写 Bitable 巡检记录
    ↓ 异常项自动创建整改任务
    ↓ 临近到期自动催办
```

### 场景 3: 质量看板

```
质检员录入检测数据
    ↓ Bitable 仪表盘自动汇总
    ↓ Agent 分析良品率趋势
    ↓ 发现异常自动推送至质量群
    ↓ 生成改进报告
```

---

## 常见问题

**Q: 云端版和私有化部署有什么区别？**
A: 云端版开箱即用，无需自己维护服务。私有化部署适合有数据合规要求的客户。

**Q: OpenClaw 跟 Agent 平台什么关系？**
A: Agent 平台处理 AI 推理和逻辑，OpenClaw 负责连接飞书生态。两者配合使用。

**Q: 需要多少资源？**
A: 云端版零资源消耗。私有化部署建议 2核4G 以上。
