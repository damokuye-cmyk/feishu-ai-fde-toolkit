#!/bin/bash
# 📦 K3s 离线包下载脚本
# 在有网络的机器上运行，下载 K3s 二进制和镜像，带到客户现场
set -euo pipefail

VERSION=${1:-"v1.31.2+k3s1"}
ARCH="amd64"
OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/images" && pwd)"

echo "📦 下载 K3s ${VERSION} 离线部署包"
echo "═══ 输出目录: ${OUTPUT_DIR}"

mkdir -p "${OUTPUT_DIR}"

# 1. K3s 二进制
echo "├── 下载 K3s 二进制..."
curl -L -o "${OUTPUT_DIR}/k3s" \
  "https://github.com/k3s-io/k3s/releases/download/${VERSION}/k3s"
chmod +x "${OUTPUT_DIR}/k3s"
echo "│   ✅ k3s ($(du -h "${OUTPUT_DIR}/k3s" | cut -f1))"

# 2. K3s airgap 镜像
echo "├── 下载 K3s airgap 镜像..."
curl -L -o "${OUTPUT_DIR}/k3s-airgap-images-${ARCH}.tar" \
  "https://github.com/k3s-io/k3s/releases/download/${VERSION}/k3s-airgap-images-${ARCH}.tar"
echo "│   ✅ images.tar ($(du -h "${OUTPUT_DIR}/k3s-airgap-images-${ARCH}.tar" | cut -f1))"

# 3. 安装脚本
echo "├── 安装脚本..."
cat > "${OUTPUT_DIR}/install-k3s-master.sh" << 'INSTALL_MASTER'
#!/bin/bash
# K3s Master 节点安装脚本 (离线)
set -euo pipefail

NODE_IP=$(ip route get 1 | awk '{print $7;exit}')
echo "本机 IP: ${NODE_IP}"

# 复制二进制和镜像
sudo cp k3s /usr/local/bin/
sudo chmod +x /usr/local/bin/k3s
sudo mkdir -p /var/lib/rancher/k3s/agent/images/
sudo cp k3s-airgap-images-*.tar /var/lib/rancher/k3s/agent/images/

# 安装 Master
curl -sfL https://get.k3s.io | \
  INSTALL_K3S_SKIP_DOWNLOAD=true \
  K3S_TOKEN="feishu-agent-secret" \
  INSTALL_K3S_EXEC="server \
    --cluster-init \
    --node-ip=${NODE_IP} \
    --advertise-address=${NODE_IP} \
    --disable=traefik \
    --write-kubeconfig-mode=644 \
    --kubelet-arg=--max-pods=50 \
    --etcd-expose-metrics=true \
  " sh -

echo "✅ Master 安装完成"
echo "   kubectl: /usr/local/bin/k3s kubectl"
echo "   Token: feishu-agent-secret"
echo "   Kubeconfig: /etc/rancher/k3s/k3s.yaml"
INSTALL_MASTER
chmod +x "${OUTPUT_DIR}/install-k3s-master.sh"

cat > "${OUTPUT_DIR}/install-k3s-worker.sh" << 'INSTALL_WORKER'
#!/bin/bash
# K3s Worker 节点安装脚本 (离线)
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法: $0 <MASTER_IP>"
  echo "示例: $0 192.168.1.100"
  exit 1
fi

MASTER_IP=$1
echo "Master IP: ${MASTER_IP}"

# 复制二进制和镜像
sudo cp k3s /usr/local/bin/
sudo chmod +x /usr/local/bin/k3s
sudo mkdir -p /var/lib/rancher/k3s/agent/images/
sudo cp k3s-airgap-images-*.tar /var/lib/rancher/k3s/agent/images/

# 加入集群
curl -sfL https://get.k3s.io | \
  INSTALL_K3S_SKIP_DOWNLOAD=true \
  K3S_URL="https://${MASTER_IP}:6443" \
  K3S_TOKEN="feishu-agent-secret" \
  sh -

echo "✅ Worker 节点已加入集群"
INSTALL_WORKER
chmod +x "${OUTPUT_DIR}/install-k3s-worker.sh"

echo "└── ✅ 全部下载完成"
echo ""
echo "📋 客户现场部署:"
echo "   1. scp images/* 到客户所有节点"
echo "   2. Master 节点: bash install-k3s-master.sh"
echo "   3. Worker 节点: bash install-k3s-worker.sh <MASTER_IP>"
echo "   4. 部署 Helm: kubectl apply -f helm/feishu-agent/"
echo ""
echo "   文件清单:"
ls -lh "${OUTPUT_DIR}/"
