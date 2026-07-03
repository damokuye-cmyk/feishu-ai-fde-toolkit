# 🔒 安全配置基线 - Feishu Agent Platform

## 1. 容器安全

### 1.1 镜像安全

```dockerfile
# 基础镜像: 选择官方最小化镜像
FROM python:3.12-slim

# 非 root 用户
RUN groupadd -r agent && useradd -r -g agent -m -u 1000 agent
USER agent
```

### 1.2 运行时安全 (Kubernetes)

```yaml
securityContext:
  runAsUser: 1000            # 非 root
  runAsGroup: 1000
  readOnlyRootFilesystem: true   # 只读根文件系统
  allowPrivilegeEscalation: false # 禁止提权
  capabilities:
    drop: ["ALL"]                # 删除所有 Linux 能力
  seccompProfile:
    type: RuntimeDefault         # 默认 seccomp 配置
```

### 1.3 资源限制

```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

## 2. 集群安全

### 2.1 K3s 安全配置

```bash
# 安装时启用安全选项
curl -sfL https://get.k3s.io | \
  INSTALL_K3S_EXEC="server \
    --disable=traefik \
    --kube-apiserver-arg=--anonymous-auth=false \
    --kube-apiserver-arg=--authorization-mode=Node,RBAC \
    --kube-controller-arg=--terminated-pod-gc-threshold=100 \
    --kubelet-arg=--read-only-port=0 \
    --kubelet-arg=--protect-kernel-defaults=true \
    --etcd-expose-metrics=true \
  " sh -
```

### 2.2 Pod 安全标准

```yaml
# Pod Security Admission (K3s >= 1.25)
apiVersion: v1
kind: Namespace
metadata:
  name: feishu-agent
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
```

### 2.3 网络策略

限制 Pod 间通信，仅允许必要流量：
- Agent Pod ↔ PostgreSQL: 5432
- Agent Pod → 外部 LLM API: 443
- Ingress → Agent Pod: 8000
- 禁止 Pod → 内网其他服务

## 3. 密钥管理

### 3.1 Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: feishu-agent-secrets
  namespace: feishu-agent
type: Opaque
stringData:
  DEEPSEEK_API_KEY: ""       # 生产环境用 sealed-secrets
  TAVILY_API_KEY: ""
  LITELLM_API_KEY: ""
```

生产环境建议使用 `sealed-secrets` 或 `external-secrets`。

### 3.2 API Key 热替换

管理后台支持在线更新 Tavily API Key：
```
管理后台 → 编辑 Agent → 填入新 Key → 保存
立即生效，不需重启 Pod
```

## 4. 数据安全

### 4.1 PostgreSQL 加密

```yaml
# 启用 TLS
POSTGRES_SSL: "on"
POSTGRES_SSL_CERT: "/certs/server.crt"
```

### 4.2 会话数据

- 会话自动清理（7 天 TTL）
- 敏感数据不记录日志
- 数据库连接加密

## 5. 审计日志

所有管理操作记录：
- Agent 创建/修改/删除
- API Key 更新
- 配置变更

## 6. 节点安全

### 6.1 操作系统基线

```bash
# 关闭非必要端口
ufw default deny incoming
ufw allow 6443/tcp   # K3s API
ufw allow 22/tcp     # SSH
ufw allow 80,443/tcp # Ingress

# 内核参数
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.ip_forward=0
sysctl -w kernel.randomize_va_space=2
```

### 6.2 节点间通信

- K3s 节点间通过 WireGuard 或专线通信
- etcd 通信启用 TLS

## 7. 供应链安全

### 7.1 镜像签名

```bash
# 使用 cosign 签名
cosign sign --key cosign.key feishu-agent-platform:latest
```

### 7.2 SBOM

```bash
# 生成软件物料清单
syft feishu-agent-platform:latest -o spdx-json > sbom.json
```

## 8. 运行时监控

| 指标 | 告警阈值 |
|------|---------|
| CPU 使用率 | > 80% 持续 5min |
| 内存使用率 | > 85% |
| Pod 重启次数 | > 3 次/小时 |
| API 错误率 | > 5% |
| LLM 调用延迟 | > 30s p99 |
