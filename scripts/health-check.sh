#!/usr/bin/env bash
# 健康检查脚本 - 检查所有组件状态
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_port() {
    local port=$1
    local name=$2
    if command -v curl &>/dev/null; then
        if curl -s --connect-timeout 3 "http://localhost:$port" &>/dev/null; then
            echo -e "  ${GREEN}✅${NC} $name :$port"
            return 0
        fi
    fi
    echo -e "  ${YELLOW}⚠️${NC} $name :$port (未响应)"
    return 1
}

echo ""
echo "=========================================="
echo "   🦞 Feishu AI FED Toolkit 健康检查"
echo "=========================================="
echo ""

# 检查 Docker
echo "📦 Docker:"
if docker info &>/dev/null; then
    echo -e "  ${GREEN}✅${NC} Docker 运行中"
else
    echo -e "  ${RED}❌${NC} Docker 未运行"
fi

# 检查各组件端口
echo ""
echo "🔌 端口检查:"
check_port 4000 "AI Gateway (LiteLLM)"
check_port 8000 "Agent Platform"
check_port 3000 "Grafana"
check_port 9090 "Prometheus"
check_port 6379 "Redis"

# 检查 Docker 容器
echo ""
echo "🐳 容器状态:"
for compose_file in $(find "$TOOLKIT_DIR" -name "docker-compose.yml" -not -path "*/archive/*"); do
    local_dir=$(dirname "$compose_file")
    name=$(basename "$local_dir")
    
    if command -v docker &>/dev/null; then
        running=$(cd "$local_dir" && docker compose ps --status running --services 2>/dev/null | wc -l)
        total=$(cd "$local_dir" && docker compose ps --services 2>/dev/null | wc -l)
        
        if [ "$total" -eq 0 ]; then
            echo -e "  ${YELLOW}⚠️${NC} $name: 未部署"
        elif [ "$running" -eq "$total" ]; then
            echo -e "  ${GREEN}✅${NC} $name: $running/$total 服务运行中"
        else
            echo -e "  ${YELLOW}⚠️${NC} $name: $running/$total 服务运行中"
        fi
    fi
done

# 检查 AI Gateway API 是否可用
echo ""
echo "🤖 AI Gateway API:"
if command -v curl &>/dev/null; then
    if curl -s --connect-timeout 5 "http://localhost:4000/health" &>/dev/null; then
        echo -e "  ${GREEN}✅${NC} LiteLLM API 正常"
    else
        echo -e "  ${YELLOW}⚠️${NC} LiteLLM API 不可用"
    fi
    
    if curl -s --connect-timeout 5 "http://localhost:8000/health" &>/dev/null; then
        echo -e "  ${GREEN}✅${NC} Agent Platform API 正常"
    else
        echo -e "  ${YELLOW}⚠️${NC} Agent Platform API 不可用"
    fi
fi

# 系统资源
echo ""
echo "💻 系统资源:"
total_ram=$(free -m | awk '/^Mem:/{print $2}')
used_ram=$(free -m | awk '/^Mem:/{print $3}')
echo "  内存: ${used_ram}MB / ${total_ram}MB"
df -h / | awk 'NR==2{printf "  磁盘: %s / %s (%s)\n", $3, $2, $5}'

echo ""
echo "=========================================="
echo ""
