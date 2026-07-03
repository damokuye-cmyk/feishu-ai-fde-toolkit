FROM python:3.12-slim

WORKDIR /app

# 安装依赖
RUN pip install --no-cache-dir \
    langgraph \
    langchain \
    langchain-community \
    httpx \
    fastapi \
    uvicorn \
    pydantic \
    redis \
    pyyaml \
    python-multipart

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
