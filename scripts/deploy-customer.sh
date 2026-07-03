#!/bin/bash
# 🦞 Feishu AI FED Toolkit - 客户现场部署脚本
# 这个脚本会被打包到发布包中，在客户机器上运行
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn(){ echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERR]${NC} $1"; }

# === 前置检查 ===
check_prereqs() {
    log_info "检查前置条件..."

    if ! command -v docker &>/dev/null; then
        log_err "Docker 未安装！请先安装 Docker"
        echo "  快速安装: curl -fsSL https://get.docker.com | bash"
        exit 1
    fi
    log_ok "Docker: $(docker --version 2>/dev/null)"

    if ! docker compose version &>/dev/null; then
        log_err "需要 Docker Compose v2+"
        exit 1
    fi
    log_ok "Docker Compose: $(docker compose version 2>/dev/null)"

    # 检查镜像是否已加载
    local missing=false
    for img in ghcr.io/berriai/litellm:main-latest postgres:16-alpine redis:7-alpine feishu-agent-platform:latest; do
        if ! docker image inspect "$img" &>/dev/null 2>&1; then
            log_warn "镜像未加载: $img"
            missing=true
        fi
    done

    if $missing; then
        echo ""
        echo "   请先加载镜像:"
        echo "     cd images && for f in *.tar; do docker load -i \"\$f\"; done && cd .."
        echo ""
        read -p "   按回车继续，或 Ctrl+C 退出..."
    fi

    if [ ! -f config/.env ]; then
        cp config/.env.example config/.env
        log_warn "请编辑 config/.env 填入你的 API Key"
        echo "   vi config/.env"
        read -p "   按回车继续..."
    fi

    # 加载环境变量
    set -a; source config/.env 2>/dev/null || true; set +a
}

# === 启动组件 ===
start_component() {
    local name=$1
    local dir=$2
    log_info "启动 $name..."
    
    cd "$SCRIPT_DIR/$dir"
    docker compose up -d --remove-orphans 2>&1 | while IFS= read -r line; do echo "  $line"; done
    cd "$SCRIPT_DIR"
    
    if docker compose ps --status running --services 2>/dev/null | grep -q .; then
        log_ok "$name 已启动"
    else
        log_err "$name 启动异常"
    fi
}

# === 健康检查 ===
health_check() {
    log_info "健康检查..."
    cd "$SCRIPT_DIR"
    
    for compose_file in docker-compose.yml monitoring/docker-compose.yml; do
        [ ! -f "$compose_file" ] && continue
        local dir=$(dirname "$compose_file")
        dir=${dir:-.}
        local name=$(basename "$compose_file" .yml)
        cd "$SCRIPT_DIR/$dir"
        local running=$(docker compose ps --status running --services 2>/dev/null | wc -l)
        local total=$(docker compose ps --services 2>/dev/null | wc -l)
        [ "$total" -gt 0 ] && log_ok "  $dir: $running/$total 服务运行中" || true
        cd "$SCRIPT_DIR"
    done
}

# === 打印访问信息 ===
print_urls() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   🦞 Feishu AI FED Toolkit 已就绪        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo "  🌐 AI Gateway (LiteLLM):    http://$(hostname -I 2>/dev/null | awk '{print $1}'):4000"
    echo "  🤖 Agent Platform API:      http://localhost:8000"
    echo "  📊 Grafana Dashboard:       http://localhost:3000  (admin/admin)"
    echo ""
    echo "  📋 快速测试:"
    echo "    curl http://localhost:4000/v1/chat/completions \\"
    echo "      -H 'Content-Type: application/json' \\"
    echo "      -H 'Authorization: Bearer \$LITELLM_MASTER_KEY' \\"
    echo "      -d '{\"model\":\"deepseek-chat\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}'"
    echo ""
    echo "  🦞 OpenClaw 配置: 见 openclaw-setup-guide.md"
    echo ""
}

# === 主流程 ===
main() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   🦞 Feishu AI FED Toolkit v1.0     ║${NC}"
    echo -e "${GREEN}║   客户现场部署脚本                   ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
    echo ""

    check_prereqs

    local mode="${1:-all}"
    case "$mode" in
        all)
            start_component "AI Gateway" "."
            start_component "监控系统" "monitoring"
            ;;
        gateway)  start_component "AI Gateway" "." ;;
        monitor)  start_component "监控系统" "monitoring" ;;
        health)   health_check; exit 0 ;;
        *)
            log_err "未知模式: $mode"
            echo "用法: ./deploy.sh [all|gateway|monitor|health]"
            exit 1
            ;;
    esac

    health_check
    print_urls
}

main "$@"
