#!/usr/bin/env bash
# 快速安装 Docker 和 Docker Compose
set -euo pipefail

echo "🔧 安装 Docker..."

# 检测系统
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    sudo apt-get update -qq
    sudo apt-get install -y -qq ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/debian $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
elif [ "$(uname)" == "Darwin" ]; then
    echo "macOS detected. Please install Docker Desktop from:"
    echo "  https://docs.docker.com/desktop/install/mac-install/"
    exit 0
else
    echo "Unknown OS. Please install Docker manually."
    exit 1
fi

# 启动 Docker
sudo systemctl enable docker 2>/dev/null || true
sudo systemctl start docker 2>/dev/null || true

# 将当前用户加入 docker 组
sudo usermod -aG docker $USER 2>/dev/null || true

echo "✅ Docker 安装完成！"
echo "请重新登录终端以生效 docker 组权限。"
echo "或直接执行: newgrp docker"
