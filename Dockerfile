# ============================================================
# 图书借阅管理系统 Dockerfile
# python:3.11-alpine + 国内镜像源
# ============================================================
FROM python:3.11-alpine

ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app
ENV PYTHONPATH=/app

# 换阿里云 apk 源，安装编译依赖
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add --no-cache gcc musl-dev libffi-dev openssl-dev zlib-dev jpeg-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL}

COPY . .

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/auth/me')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]
