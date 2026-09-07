# 多阶段构建 - 用户服务 Dockerfile
# Stage 1: 构建阶段
# 固定到 bookworm，避免 rolling 标签切换到新发行版导致 APT 源不稳定
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# 安装构建依赖
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i \
        -e 's|http://deb.debian.org|https://deb.debian.org|g' \
        -e 's|http://security.debian.org|https://security.debian.org|g' \
        /etc/apt/sources.list; \
    fi; \
    apt-get update -o Acquire::Retries=5 -o Acquire::https::Timeout=30; \
    apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev; \
    rm -rf /var/lib/apt/lists/*

# 配置 pip 使用阿里云镜像
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.aliyun.com

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Proto 编译阶段
FROM builder AS proto-builder

WORKDIR /app

# 复制 proto 定义文件
COPY protos/ ./protos/

# 创建输出目录并编译 proto 文件
RUN mkdir -p app/protos && \
    python -m grpc_tools.protoc \
        -I ./protos \
        --python_out=./app/protos \
        --grpc_python_out=./app/protos \
        ./protos/user.proto && \
    echo '"""gRPC 自动生成的 protobuf Python 代码"""' > app/protos/__init__.py && \
    sed -i 's/import user_pb2/from app.protos import user_pb2/' app/protos/user_pb2_grpc.py

# Stage 3: 运行阶段
FROM python:3.11-slim-bookworm

WORKDIR /app

# 安装运行时依赖
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i \
        -e 's|http://deb.debian.org|https://deb.debian.org|g' \
        -e 's|http://security.debian.org|https://security.debian.org|g' \
        /etc/apt/sources.list; \
    fi; \
    apt-get update -o Acquire::Retries=5 -o Acquire::https::Timeout=30; \
    apt-get install -y --no-install-recommends \
      libpq5 \
      curl; \
    rm -rf /var/lib/apt/lists/*; \
    apt-get clean

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 从构建阶段复制已安装的依赖
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY ./app ./app

# 从 proto-builder 中复制编译后的 gRPC 代码
COPY --from=proto-builder /app/app/protos ./app/protos

# 设置 Python 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 暴露端口：HTTP + gRPC
EXPOSE 8000 50051

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
