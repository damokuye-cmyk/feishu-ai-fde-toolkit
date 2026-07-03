FROM python:3.12-slim

WORKDIR /app

# 安全配置: 非 root 运行
RUN groupadd -r agent && useradd -r -g agent -m -u 1000 agent

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# 复制代码
COPY . .

# 创建配置目录
RUN mkdir -p /app/config && chown -R agent:agent /app

# 安全: 只读根文件系统兼容
RUN chmod 755 /app && chmod 644 /app/requirements.txt

# 复制默认配置
COPY templates/agents.yaml /app/config/agents.yaml
RUN chown agent:agent /app/config/agents.yaml

EXPOSE 8000

USER agent

# 安全: 禁止容器内提权
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
