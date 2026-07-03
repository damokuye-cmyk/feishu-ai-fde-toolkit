FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建非 root 用户运行
RUN useradd -m -u 1000 agent && chown -R agent:agent /app
USER agent

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
