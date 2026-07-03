#!/bin/bash
# 🦞 一键安装飞书全部 28 个 Skill
set -euo pipefail

echo "╔══════════════════════════════════════╗"
echo "║   🦞 Install Feishu Skills          ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 检查 Node.js
if ! command -v node &>/dev/null; then
    echo "❌ 需要 Node.js 18+"
    echo "   安装: https://nodejs.org/"
    echo "   或: nvm install 18"
    exit 1
fi

echo "✅ Node.js $(node -v)"

# 检查 npx
if ! command -v npx &>/dev/null; then
    echo "❌ 需要 npx (通常随 Node.js 一起安装)"
    exit 1
fi

echo ""
echo "📦 正在安装飞书 Skills..."
echo "   来源: https://open.feishu.cn"
echo "   Skills: 28 个 (文档/表格/消息/日历/审批/考勤...)"
echo "   总安装量: 830 万+"
echo ""

# 安装
npx skills add https://open.feishu.cn 2>&1

echo ""
echo "✅ 飞书 Skills 安装完成！"
echo ""
echo "   你可以用以下 Agent 使用这些 Skill:"
echo "   - Claude Code:  npx skills add https://open.feishu.cn --agent claude-code"
echo "   - Cursor:       npx skills add https://open.feishu.cn --agent cursor"
echo "   - Codex:        npx skills add https://open.feishu.cn --agent codex"
echo ""
echo "   在 AI 编码 Agent 中，直接说:"
echo "   '在飞书创建一个多维表格...'"
echo "   '帮我查一下张三的组织架构...'"
echo "   '给项目群发一条消息...'"
echo ""
