#!/bin/bash
# 🦞 Feishu AI FED Toolkit - 构建 & 打包脚本
# 用法: ./build.sh [all|gateway|agent|clean]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info() { echo -e "${BLUE}[BUILD]${NC} $1"; }
log_ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
log_err() { echo -e "${RED}[ERR]${NC} $1"; }

BUILD_DATE=$(date +%Y%m%d_%H%M%S)
PACKAGE_DIR="$SCRIPT_DIR/packages/build_$BUILD_DATE"

# 确保 Docker 在运行
check_docker() {
    if ! docker info &>/dev/null; then
        log_err "Docker 未运行，请先启动 Docker"
        exit 1
    fi
    log_ok "Docker 运行中"
}

# === 构建组件镜像 ===

build_gateway() {
    log_info "构建 AI Gateway 镜像 (LiteLLM)..."
    # 拉取官方的 LiteLLM 镜像（后续可保存为 tar）
    docker pull ghcr.io/berriai/litellm:main-latest 2>&1 | tail -1
    docker pull postgres:16-alpine 2>&1 | tail -1
    docker pull redis:7-alpine 2>&1 | tail -1
    log_ok "AI Gateway 镜像就绪"
}

build_agent_platform() {
    log_info "构建 Agent Platform 镜像..."
    cd "$SCRIPT_DIR/agent-platform"
    docker build -t feishu-agent-platform:latest . 2>&1 | tail -1
    cd "$SCRIPT_DIR"
    log_ok "Agent Platform 镜像构建完成"
}

build_monitoring() {
    log_info "拉取监控组件镜像..."
    docker pull prom/prometheus:latest 2>&1 | tail -1
    docker pull grafana/grafana:latest 2>&1 | tail -1
    docker pull prom/node-exporter:latest 2>&1 | tail -1
    log_ok "监控组件镜像就绪"
}

# === 打包 ===

package_all() {
    log_info "开始打包..."
    mkdir -p "$PACKAGE_DIR/images" "$PACKAGE_DIR/config" "$PACKAGE_DIR/scripts" "$PACKAGE_DIR/demo"

    # 1. 保存 Docker 镜像为 tar
    log_info "导出 Docker 镜像..."
    IMAGES=(
        "ghcr.io/berriai/litellm:main-latest:litellm.tar"
        "postgres:16-alpine:postgres16.tar"
        "redis:7-alpine:redis7.tar"
        "prom/prometheus:latest:prometheus.tar"
        "grafana/grafana:latest:grafana.tar"
        "prom/node-exporter:latest:node-exporter.tar"
        "feishu-agent-platform:latest:agent-platform.tar"
    )
    for entry in "${IMAGES[@]}"; do
        local name="${entry%%:*}"
        local tag="${entry#*:}"; tag="${tag%:*}"
        local filename="${entry##*:}"
        log_info "  打包 $name ..."
        docker save "$name:$tag" -o "$PACKAGE_DIR/images/$filename" 2>/dev/null && \
            log_ok "    $filename ($(du -h "$PACKAGE_DIR/images/$filename" | cut -f1))" || \
            log_err "    打包失败: $name:$tag"
    done

    # 2. 复制 docker-compose 和配置
    cp ai-gateway/docker-compose.yml "$PACKAGE_DIR/"
    cp ai-gateway/config.yaml "$PACKAGE_DIR/config/"
    cp agent-platform/docker-compose.yml "$PACKAGE_DIR/"
    cp config/.env.example "$PACKAGE_DIR/config/"

    # 3. 复制监控配置
    mkdir -p "$PACKAGE_DIR/monitoring"
    cp monitoring/docker-compose.yml "$PACKAGE_DIR/monitoring/"
    cp monitoring/prometheus.yml "$PACKAGE_DIR/monitoring/"

    # 4. 复制部署脚本（客户现场用）
    cp scripts/deploy-customer.sh "$PACKAGE_DIR/deploy.sh"
    chmod +x "$PACKAGE_DIR/deploy.sh"

    # 5. 复制健康检查脚本
    cp scripts/health-check.sh "$PACKAGE_DIR/scripts/"
    chmod +x "$PACKAGE_DIR/scripts/health-check.sh"

    # 6. 复制 Demo 数据
    cp demo-scenarios/manufacturing/demo_data_generator.py "$PACKAGE_DIR/demo/"

    # 7. 复制 OpenClaw 指南
    cp openclaw-setup-guide.md "$PACKAGE_DIR/"

    # 8. 创建客户现场 README
    cat > "$PACKAGE_DIR/README.md" << 'PKG_README'
# 🦞 Feishu AI FED Toolkit - 客户部署包

## 快速启动

```bash
# 1. 加载所有镜像
cd images && for f in *.tar; do docker load -i "$f"; done && cd ..

# 2. 编辑配置
cp config/.env.example config/.env
# 填入 API Key

# 3. 一键部署
./deploy.sh all

# 4. 验证
./scripts/health-check.sh
```

## 访问地址

| 服务 | 地址 |
|------|------|
| AI Gateway | http://localhost:4000 |
| Agent API | http://localhost:8000 |
| Agent: 制造业助手 | POST http://localhost:8000/agents/manufacturing/chat |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |

## 组件

| 组件 | 用途 |
|------|------|
| AI Gateway (LiteLLM) | 多模型路由、负载均衡、故障降级 |
| Agent Platform (Langgraph) | Agent 编排，预置制造业、RAG、通用助手 |
| OpenClaw (小龙虾) | 飞书 AI 插件，连接飞书生态 |
| Monitoring (Grafana + Prometheus) | 用量、性能、错误监控 |
| Demo Scenarios | 制造业生产告警、巡检、质量 Demo |

## 快速测试

```bash
# 测试 AI Gateway
curl http://localhost:4000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-litellm-master-key-123456' \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"你好"}]}'

# 测试制造业 Agent
curl -X POST http://localhost:8000/agents/manufacturing/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"注塑机温度异常，分析可能原因"}'
```
PKG_README

    # 8. 最终压缩
    cd "$SCRIPT_DIR/packages"
    tar czf "feishu-ai-fed-toolkit_$BUILD_DATE.tar.gz" "build_$BUILD_DATE"
    cd "$SCRIPT_DIR"

    echo ""
    log_ok "✅ 打包完成！"
    echo ""
    echo "   包位置: packages/feishu-ai-fed-toolkit_$BUILD_DATE.tar.gz"
    echo "   大小: $(du -h "packages/feishu-ai-fed-toolkit_$BUILD_DATE.tar.gz" | cut -f1)"
    echo "   内容:"
    echo "     - Docker 镜像 $(ls "$PACKAGE_DIR/images/"*.tar 2>/dev/null | wc -l) 个"
    echo "     - docker-compose 配置"
    echo "     - 部署脚本 deploy.sh"
    echo "     - 制造业 Demo 数据"
    echo "     - OpenClaw 部署指南"
    echo ""
    echo "   客户现场操作:"
    echo "     tar xzf feishu-ai-fed-toolkit_$BUILD_DATE.tar.gz"
    echo "     cd build_$BUILD_DATE"
    echo "     ./deploy.sh all"
    echo ""
}

# === 清理 ===

clean_all() {
    log_info "清理构建产物..."
    rm -rf packages/build_*
    log_ok "清理完成"
}

# === 主流程 ===

main() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   🦞 Feishu AI FED Toolkit Build    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
    echo ""

    check_docker

    local mode="${1:-all}"
    case "$mode" in
        all)
            build_gateway
            build_agent_platform
            build_monitoring
            package_all
            ;;
        gateway)
            build_gateway
            ;;
        agent)
            build_agent_platform
            ;;
        clean)
            clean_all
            exit 0
            ;;
        *)
            log_err "未知参数: $mode"
            echo "用法: ./build.sh [all|gateway|agent|clean]"
            exit 1
            ;;
    esac
}

main "$@"
