FROM nginx:alpine

# 设置工作目录
WORKDIR /usr/share/nginx/html

# 安装基本工具
RUN apk add --no-cache \
    curl \
    wget \
    tzdata

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 创建健康检查文件
RUN echo "ok" > /usr/share/nginx/html/health.html

# 复制前端构建文件
COPY dist/ /usr/share/nginx/html/

# 复制Nginx配置
COPY nginx-synology.conf /etc/nginx/conf.d/default.conf

# 设置文件权限
RUN chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost/health.html || exit 1 