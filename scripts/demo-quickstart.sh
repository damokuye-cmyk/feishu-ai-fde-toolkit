#!/usr/bin/env bash
# 演示场景快速启动 - 5 分钟拉起 Demo
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🎯 准备制造业 Demo 数据..."

# 1. 生成演示数据
cd "$TOOLKIT_DIR/demo-scenarios/manufacturing"
python3 demo_data_generator.py

# 2. 检查 Gateway 状态
echo ""
echo "🔍 检查 AI Gateway..."
curl -s --connect-timeout 5 http://localhost:4000/health > /dev/null 2>&1 && \
    echo "  ✅ AI Gateway 正常" || \
    echo "  ⚠️  AI Gateway 未运行，请先执行 ./deploy.sh"

# 3. 检查 Agent Platform
echo ""
echo "🔍 检查 Agent Platform..."
curl -s --connect-timeout 5 http://localhost:8000/health > /dev/null 2>&1 && \
    echo "  ✅ Agent Platform 正常" || \
    echo "  ⚠️  Agent Platform 未运行，请先执行 ./deploy.sh"

# 4. 测试 AI 对话
echo ""
echo "🤖 测试 AI Gateway 对话..."
if curl -s --connect-timeout 10 http://localhost:4000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-litellm-master-key-123456}" \
    -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"你好，请用一句话介绍自己"}]}' > /dev/null 2>&1; then
    echo "  ✅ AI 对话正常"
else
    echo "  ⚠️  AI 对话测试失败（可能 API Key 未配置）"
fi

echo ""
echo "=========================================="
echo "  🎯 Demo 就绪！"
echo "=========================================="
echo ""
echo "  可演示场景："
echo "    1. 生产异常告警 Agent"
echo "        curl -X POST http://localhost:8000/agents/manufacturing/chat \\"
echo "          -H 'Content-Type: application/json' \\"
echo "          -d '{\"message\":\"注塑机A3温度异常，请分析可能原因\"}'"
echo ""
echo "    2. 质量数据分析"
echo "        curl -X POST http://localhost:8000/agents/manufacturing/chat \\"
echo "          -H 'Content-Type: application/json' \\"
echo "          -d '{\"message\":\"上个月良品率下降趋势，帮我做个根因分析\"}'"
echo ""
echo "    3. Bitable Demo 数据已生成："
echo "        - demo_alert_data.json"
echo "        - demo_quality_data.json"
echo ""
echo "=========================================="
