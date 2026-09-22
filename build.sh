#!/bin/bash
# 🦞 Feishu AI FDE Toolkit - 一键构建 & 打包
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_DATE=$(date +%Y%m%d_%H%M%S)
PACKAGE_DIR="$SCRIPT_DIR/packages/build_$BUILD_DATE"

echo "╔══════════════════════════════════════╗"
echo "║   🦞 Feishu AI FDE Toolkit Build    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. 构建 Agent Platform 镜像
echo "🔨 构建 Agent Platform 镜像..."
docker build -t feishu-agent-platform:latest runtime/agent-platform/

# 2. 拉取依赖镜像
echo "📦 拉取依赖镜像..."
for img in postgres:16-alpine redis:7-alpine; do
  docker pull $img &
done
wait

# 3. 准备发布目录
echo "📁 准备发布包..."
mkdir -p "$PACKAGE_DIR"/{images,config,deploy}

# 4. 导出 Docker 镜像
echo "💾 导出 Docker 镜像..."
for pair in "feishu-agent-platform:latest:agent-platform.tar" \
            "postgres:16-alpine:postgres16.tar" \
            "redis:7-alpine:redis7.tar"; do
  name="${pair%%:*}"
  tag="${pair#*:}"; tag="${tag%:*}"
  file="${pair##*:}"
  docker save "$name:$tag" -o "$PACKAGE_DIR/images/$file" 2>/dev/null
  echo "   $file ($(du -h "$PACKAGE_DIR/images/$file" | cut -f1))"
done

# 5. 复制配置和部署文件
echo "📋 复制配置文件..."
cp runtime/agent-platform/templates/agents.yaml "$PACKAGE_DIR/config/"
cp config/.env.example "$PACKAGE_DIR/config/"
cp -r deploy/* "$PACKAGE_DIR/deploy/"

# 6. 创建客户部署说明
cat > "$PACKAGE_DIR/README.md" << 'EOF'
# 🦞 Feishu AI Agent Platform - 部署包

## 快速部署 (K3s)

```bash
# 所有节点执行
cd deploy/k3s/images
sudo bash install-k3s-master.sh   # Master 节点
sudo bash install-k3s-worker.sh <MASTER_IP>  # Worker 节点

# Master 节点执行
kubectl apply -f deploy/helm/feishu-agent/templates/

# 查看状态
kubectl -n feishu-agent get pods
```

## 快速部署 (Docker Compose)

```bash
# 加载镜像
cd images && for f in *.tar; do docker load -i "$f"; done

# 启动
docker compose up -d

# 访问
# Agent API: http://localhost:8000/v1/chat/completions
# Admin UI:  http://localhost:8000/admin
# Models:    http://localhost:8000/v1/models
```

## 配置

```bash
cp config/.env.example config/.env
# 编辑 .env 填入 API Key
# 管理后台也可在线配置 /admin
```
EOF

# 7. 打包
echo "📦 打包..."
cd packages
tar czf "feishu-ai-fde-toolkit_$BUILD_DATE.tar.gz" "build_$BUILD_DATE"
cd ..

echo ""
echo "✅ 构建完成！"
echo "   发布包: packages/feishu-ai-fde-toolkit_$BUILD_DATE.tar.gz"
echo "   大小: $(du -h "packages/feishu-ai-fde-toolkit_$BUILD_DATE.tar.gz" | cut -f1)"
echo ""
echo "   客户现场:"
echo "     tar xzf feishu-ai-fde-toolkit_*.tar.gz"
echo "     cd build_*/deploy/k3s/images"
echo "     bash install-k3s-master.sh"
