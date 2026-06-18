# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖并安装 uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://astral.sh/uv/install.sh | sh

# 复制项目文件
COPY pyproject.toml .
COPY uv.lock .

# 使用 uv 安装依赖（使用绝对路径确保命令可执行）
RUN /root/.cargo/bin/uv sync

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["/root/.cargo/bin/uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
