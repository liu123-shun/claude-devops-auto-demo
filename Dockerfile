# ============================================================
# 图书借阅管理系统 Dockerfile
# python:3.11-alpine 轻量镜像 + MySQL 客户端依赖
# ============================================================
FROM python:3.11-alpine

# 定义国内阿里云pip镜像源
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# 安装编译依赖（pymysql + Pillow 需要）
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev zlib-dev jpeg-dev

# 设置工作目录
WORKDIR /app

# 设置 PYTHONPATH 彻底解决模块找不到报错
ENV PYTHONPATH=/app

# 先复制依赖文件（利用 Docker 层缓存）
COPY requirements.txt .

# pip 安装全部依赖，使用国内源
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL}

# 复制全部项目代码
COPY . .

# 创建非 root 用户并切换（安全加固）
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露服务端口
EXPOSE 5000

# 健康检查（每 30s 探测一次根路径）
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/auth/me')" || exit 1

# uvicorn 标准启动命令，监听 0.0.0.0:5000
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 5000"]
