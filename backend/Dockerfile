FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖和网络诊断工具
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    curl \
    iputils-ping \
    net-tools \
    telnet \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# 设置时区为亚洲/上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置Python环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# 创建必要的目录并设置权限
RUN mkdir -p /app/logs /app/config && \
    chmod 777 /app/logs && \
    chmod 755 /app/config

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 确保脚本可执行
RUN chmod +x container_start.sh

# 暴露端口
EXPOSE 9099

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:9099/api/health || exit 1

# 启动应用
CMD ["./container_start.sh"] 