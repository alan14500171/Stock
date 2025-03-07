#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}前端极致简化部署脚本${NC}"
echo "========================="

# 检查前置条件
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    exit 1
fi

# 检查dist目录
if [ ! -d "./dist" ]; then
    echo -e "${RED}错误: 未找到dist目录${NC}"
    exit 1
fi

# 添加提示用户输入后端API地址
echo -e "${YELLOW}请输入后端API地址（格式：http://IP:端口）${NC}"
echo -e "${YELLOW}默认为: http://192.168.0.109:9099${NC}"
read -p "后端API地址: " BACKEND_API
BACKEND_API=${BACKEND_API:-"http://192.168.0.109:9099"}
echo -e "${GREEN}使用后端API地址: ${BACKEND_API}${NC}"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}创建临时目录: $TEMP_DIR${NC}"

# 在临时目录中创建所需文件
mkdir -p $TEMP_DIR/html
cp -r ./dist/* $TEMP_DIR/html/

# 创建健康检查文件
echo "ok" > $TEMP_DIR/html/health.html

# 创建nginx配置 - 增强版
cat > $TEMP_DIR/default.conf << EOF
server {
    listen 80;
    server_name localhost;
    
    # 开启调试
    error_log /var/log/nginx/error.log debug;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # 启用gzip
    gzip on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/javascript application/json;
    
    # 禁用缓存（调试用）
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate";
    add_header Pragma "no-cache";
    expires 0;
    
    # 健康检查
    location /health.html {
        default_type text/plain;
        return 200 'ok';
    }
    
    # 处理静态资源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires off;
        add_header Cache-Control "public, max-age=0";
        try_files \$uri =404;
    }
    
    # 前端路由 - 确保所有请求都返回index.html
    location / {
        try_files \$uri \$uri/ /index.html;
        add_header X-Debug-Message "Serving SPA route";
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass ${BACKEND_API};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        proxy_buffering off;
        
        # 调试API请求
        add_header X-Proxied-By "Nginx";
        add_header X-Proxy-Destination "${BACKEND_API}";
    }
    
    # 添加调试端点
    location /debug {
        default_type application/json;
        return 200 '{"status":"ok","backend":"${BACKEND_API}","timestamp":"\$time_local"}';
    }
    
    # 错误页面
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF

# 检查用户是否需要修改前端环境变量
echo -e "\n${YELLOW}是否需要创建自定义环境配置文件? [y/N]${NC}"
read -r create_env
if [[ "$create_env" == "y" || "$create_env" == "Y" ]]; then
    # 创建一个简单的环境变量覆盖文件
    cat > $TEMP_DIR/html/env-config.js << EOF
window.ENV = {
  API_BASE_URL: "${BACKEND_API}",
  NODE_ENV: "production",
  PUBLIC_PATH: "/",
  APP_VERSION: "$(date +%Y.%m.%d)"
};
EOF
    echo -e "${GREEN}✓ 已创建环境配置文件${NC}"
    
    # 添加到index.html
    if [ -f "$TEMP_DIR/html/index.html" ]; then
        sed -i 's/<head>/<head>\n  <script src="\/env-config.js"><\/script>/' "$TEMP_DIR/html/index.html"
        echo -e "${GREEN}✓ 已将环境配置注入到index.html${NC}"
    fi
fi

# 创建Dockerfile
cat > $TEMP_DIR/Dockerfile << EOF
FROM nginx:alpine
COPY html /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf
EOF

# 构建和运行
echo -e "${YELLOW}开始构建镜像...${NC}"
cd $TEMP_DIR
docker build -t stock-frontend:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
    
    # 停止并删除现有容器
    echo -e "${YELLOW}停止并删除现有容器...${NC}"
    docker rm -f stock-frontend >/dev/null 2>&1
    
    # 启动新容器
    echo -e "${YELLOW}启动新容器...${NC}"
    docker run -d --name stock-frontend \
        --restart always \
        -p 9009:80 \
        -e TZ=Asia/Shanghai \
        stock-frontend:latest
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 容器启动成功${NC}"
        echo -e "${GREEN}✓ 前端应用可通过 http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost"):9009 访问${NC}"
    else
        echo -e "${RED}✗ 容器启动失败${NC}"
    fi
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
fi

# 清理临时目录
echo -e "${YELLOW}清理临时文件...${NC}"
rm -rf $TEMP_DIR
echo -e "${GREEN}✓ 清理完成${NC}" 