#!/usr/bin/env bash
# 🦞 Feishu AI FED Toolkit - 一键部署脚本
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err()  { echo -e "${RED}[ERR]${NC} $1"; }

# === 检查前置条件 ===
check_prereqs() {
    log_info "检查前置条件..."

    if ! command -v docker &>/dev/null; then
        log_warn "Docker 未安装，尝试自动安装..."
        bash "$SCRIPT_DIR/scripts/install-docker.sh" || {
            log_err "请手动安装 Docker: https://docs.docker.com/engine/install/"
            exit 1
        }
    fi
    log_ok "Docker: $(docker --version)"

    if ! docker compose version &>/dev/null; then
        log_err "需要 Docker Compose v2+"
        exit 1
    fi
    log_ok "Docker Compose: $(docker compose version)"

    # 检查配置
    if [ ! -f config/.env ]; then
        log_info "创建 config/.env 配置模板..."
        cp config/.env.example config/.env
        log_warn "请编辑 config/.env 填入你的 API Key 等配置"
    fi
}

# === 加载环境变量 ===
load_env() {
    set -a
    source config/.env 2>/dev/null || true
    set +a
}

# === 部署组件 ===
deploy_component() {
    local name=$1
    local dir=$2
    log_info "部署 $name..."
    cd "$SCRIPT_DIR/$dir"
    docker compose up -d --remove-orphans 2>&1 | while IFS= read -r line; do
        echo "  $line"
    done
    cd "$SCRIPT_DIR"
    log_ok "$name 部署完成"
}

# === 检查组件健康 ===
health_check() {
    log_info "检查各组件健康状态..."
    local all_ok=true

    for compose_file in $(find . -name "docker-compose.yml" -not -path "./archive/*"); do
        local dir=$(dirname "$compose_file")
        local name=$(basename "$dir")
        cd "$SCRIPT_DIR/$dir"
        local running=$(docker compose ps --status running --services 2>/dev/null | wc -l)
        local total=$(docker compose ps --services 2>/dev/null | wc -l)
        if [ "$running" -eq "$total" ] && [ "$total" -gt 0 ]; then
            log_ok "  $name: $running/$total 服务运行中"
        elif [ "$total" -gt 0 ]; then
            log_warn "  $name: $running/$total 服务运行中"
            all_ok=false
        fi
        cd "$SCRIPT_DIR"
    done

    $all_ok && log_ok "✅ 全部组件健康" || log_warn "⚠️ 部分组件异常，请检查"
}

# === 打印访问地址 ===
print_urls() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}  🦞  Feishu AI FED Toolkit 已部署${NC}"
    echo "=========================================="
    echo ""
    echo "  AI Gateway (LiteLLM):  http://localhost:4000"
    echo "  Agent Platform API:     http://localhost:8000"
    echo "  Grafana Dashboard:      http://localhost:3000  (admin/admin)"
    echo "  Prometheus:             http://localhost:9090"
    echo ""
    echo "  示例 Agent API:"
    echo "    POST http://localhost:8000/agents/manufacturing/chat"
    echo "    POST http://localhost:8000/agents/rag/query"
    echo ""
    echo "  LiteLLM (OpenAI 兼容):"
    echo "    curl http://localhost:4000/v1/chat/completions"
    echo ""
    echo "=========================================="
}

# === 主流程 ===
main() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   🦞 Feishu AI FED Toolkit v1.0     ║${NC}"
    echo -e "${GREEN}║   飞书 AI 现场交付工具链             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
    echo ""

    check_prereqs
    load_env

    # 选择部署模式
    local mode="${1:-all}"
    case "$mode" in
        all)
            deploy_component "AI 网关 (LiteLLM)"     "ai-gateway"
            deploy_component "Agent 平台"             "agent-platform"
            deploy_component "监控系统"               "monitoring"
            ;;
        gateway)
            deploy_component "AI 网关 (LiteLLM)"     "ai-gateway"
            ;;
        agent)
            deploy_component "Agent 平台"             "agent-platform"
            ;;
        monitor)
            deploy_component "监控系统"               "monitoring"
            ;;
        health)
            health_check
            exit 0
            ;;
        *)
            log_err "未知模式: $mode"
            echo "用法: ./deploy.sh [all|gateway|agent|monitor|health]"
            exit 1
            ;;
    esac

    health_check
    print_urls
}

main "$@"