# 🦞 飞书 Skills 集成指南
# skills.sh 上的 28 个飞书官方 Skill 一键安装

## 一句话用法

```bash
# 安装全部飞书 Skill（AI 编码 Agent 用）
npx skills add https://open.feishu.cn

# 或指定 Claude Code
npx skills add https://open.feishu.cn --agent claude-code
```

---

## 28 个飞书 Skill 全览

### 📝 文档 & 内容创作

| Skill | 用途 | 场景示例 |
|-------|------|---------|
| **lark-doc** | 飞书文档读写、编辑、管理 | "帮我写一份项目周报并分享给团队" |
| **lark-sheets** | 电子表格操作 | "在表格 Sheet1 的 A 列求和" |
| **lark-slides** | 幻灯片制作 | "基于这份文档生成 10 页 PPT" |
| **lark-base** | 多维表格 (Bitable) 全操作 | "创建一个生产缺陷跟踪表，包含关联字段" |
| **lark-wiki** | 知识库管理 | "把这份文档发布到知识库的'工艺规范'目录" |
| **lark-whiteboard** | 白板创建和管理 | "创建一个产品架构图白板" |
| **lark-whiteboard-cli** | 白板 CLI 操作 | 自动批量生成白板 |
| **lark-note** | 笔记管理 | "整理今天的会议笔记" |
| **lark-markdown** | Markdown 导入导出 | "把这个 Markdown 文件导入飞书文档" |

### 💬 沟通 & 协作

| Skill | 用途 | 场景示例 |
|-------|------|---------|
| **lark-im** | 即时消息收发 | "给张三发消息说方案已通过" |
| **lark-calendar** | 日历管理 | "在周五下午 3 点创建评审会议" |
| **lark-vc** | 视频会议 | "创建一场飞书会议并邀请所有人" |
| **lark-vc-agent** | 会议 AI Agent | "帮我总结昨天会议的行动项" |
| **lark-mail** | 邮箱操作 | "发送邮件给客户确认方案" |

### 🏢 组织管理

| Skill | 用途 | 场景示例 |
|-------|------|---------|
| **lark-contact** | 通讯录管理 | "查找王经理的组织架构" |
| **lark-approval** | 审批流程 | "提交一份出差审批单" |
| **lark-attendance** | 考勤管理 | "查一下张三本月的出勤情况" |
| **lark-task** | 任务管理 | "创建一个任务分配给李四，明天截止" |
| **lark-okr** | OKR 管理 | "帮我对齐本季度的 OKR" |

### 🗄️ 存储 & 开发

| Skill | 用途 | 场景示例 |
|-------|------|---------|
| **lark-drive** | 云盘文件管理 | "把这份合同移到'已签署'目录" |
| **lark-event** | 事件订阅与回调 | "配置当文档更新时自动通知" |
| **lark-openapi-explorer** | OpenAPI 接口探索 | "查一下飞书文档的创建接口" |
| **lark-apps** | 应用管理 | "发布应用到飞书应用目录" |

### ⚡ 工作流 & 效率

| Skill | 用途 | 场景示例 |
|-------|------|---------|
| **lark-shared** | 共享/认证/权限 | "给外部伙伴分享这个文件夹" |
| **lark-skill-maker** | 自定义 Skill 创建 | "把我这个工作流变成 Skill" |
| **lark-workflow-meeting-summary** | 会议纪要自动总结 | "自动总结本周所有会议" |
| **lark-workflow-standup-report** | 站会报告自动生成 | "生成今日站会报告" |

### 🎙️ 会议

| Skill | 用途 |
|-------|------|
| **lark-minutes** | 妙记（会议录制与转录） |

---

## 客户现场演示场景

### 场景 1: "5 分钟搭建生产缺陷跟踪系统"

```bash
# 安装飞书 Skills
npx skills add https://open.feishu.cn

# AI 编码 Agent 就能直接对飞书操作了
# 在 Claude Code / Cursor 中：
```

```
用户: "在飞书创建一个多维表格，叫'生产缺陷跟踪'，
      包含字段：缺陷编号、产品名称、发现日期、严重程度、状态、责任人。
      然后创建一个仪表盘展示各状态的缺陷数量。"
Agent: ✅ 已创建多维表格，字段已配置，仪表盘已生成。
```

### 场景 2: "自动生成周报并推送"

```
用户: "读取本周所有会议纪要，
      汇总成一份周报发布到知识库，
      然后发消息通知团队查看。"
Agent: ✅ 已读取 5 份会议纪要，生成周报已发布到知识库，已通知 12 人。
```

### 场景 3: "审批流程自动化"

```
用户: "帮我创建一个设备采购审批流，
      金额小于 1 万的部门经理审批，
      1-10 万的 VP 审批，
      大于 10 万的 CEO 审批。"
Agent: ✅ 审批流程已创建，规则已配置。
```

---

## 在你的管理后台配置

你也可以把这些 Skill 作为 **工具** 注册到你的 Agent Platform：

```yaml
# agents.yaml 扩展
agents:
  feishu-helper:
    name: "飞书助手"
    description: "通过飞书开放 API 操作飞书"
    tools:
      - lark_doc
      - lark_base
      - lark_im
      - lark_calendar
    system_prompt: |
      你是飞书 AI 助手，可以操作飞书的文档、表格、消息、日历等。
```

---

## 安装方法

```bash
# 方法 1: 手动安装（推荐，在客户现场演示用）
npx skills add https://open.feishu.cn

# 方法 2: 通过本工具链的脚本
bash scripts/install-feishu-skills.sh

# 验证安装
npx skills list
```
