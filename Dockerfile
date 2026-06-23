# ============================================================
# 优化版 Dockerfile — python:3.11-alpine (体积 ~18MB, 比 slim 小 67%)
# ============================================================
FROM python:3.11-alpine

# 定义国内阿里云pip镜像源
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# 设置工作目录
WORKDIR /app

# 先复制依赖文件（利用 Docker 层缓存：源码变动不会导致 pip install 重跑）
COPY requirements.txt .

# 关键：带上 -i ${PIP_INDEX_URL} 使用国内源，避免超时
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL}

# 复制全部项目代码
COPY . .

# 创建非 root 用户并切换（安全加固）
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露服务端口
EXPOSE 5000

# 健康检查（每 30s 探测一次）
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:5000/').raise_for_status()" || exit 1

# 使用 uvicorn 启动 FastAPI（进入/app根目录确保模块路径正确）
CMD ["sh", "-c", "cd /app && uvicorn src.main:app --host 0.0.0.0 --port 5000"]