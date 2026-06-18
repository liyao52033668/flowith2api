# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN curl -sSL https://astral.sh/uv/install.sh | bash

# 先复制项目配置文件（用于缓存优化）
COPY pyproject.toml .
COPY uv.lock .

# 使用 uv 安装依赖
RUN /root/.local/bin/uv sync

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["/root/.local/bin/uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
