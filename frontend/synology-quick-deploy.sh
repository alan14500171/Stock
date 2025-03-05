#!/bin/bash
#
# 群辉NAS快速部署脚本 - 特别针对XSym问题
# 用法: ./synology-quick-deploy.sh [命令]
# 命令: build, deploy, start, stop

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印信息
info() { echo -e "${GREEN}[信息]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
error() { echo -e "${RED}[错误]${NC} $1"; }
step() { echo -e "${BLUE}[步骤]${NC} $1"; }

step "开始群辉NAS前端部署流程"

# 检查Docker是否安装
if ! command -v docker &>/dev/null; then
  error "未找到Docker！请确保已在群辉NAS上安装Docker"
  exit 1
fi

# 创建必要文件
create_files() {
  step "创建必要的部署文件"
  
  # 创建Dockerfile
  cat > Dockerfile.quick << 'EOF'
# 第一阶段：构建阶段
FROM node:16-alpine as build

# 设置工作目录
WORKDIR /app

# 复制预构建的dist文件
COPY ./dist/ ./dist/

# 第二阶段：部署阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost:80/health || exit 1

# 暴露端口
EXPOSE 80

# 启动命令
CMD ["nginx", "-g", "daemon off;"]
EOF
  info "已创建Dockerfile.quick文件"
  
  # 创建docker-compose文件
  cat > docker-compose.quick.yml << 'EOF'
version: '3'

services:
  stock-frontend:
    container_name: stock-frontend
    build:
      context: .
      dockerfile: Dockerfile.quick
    image: stock-frontend:latest
    restart: always
    network_mode: host
    environment:
      - TZ=Asia/Shanghai
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
EOF
  info "已创建docker-compose.quick.yml文件"
}

# 本地构建前端
build_frontend() {
  step "在本地构建前端"
  
  if [ ! -f "package.json" ]; then
    error "未找到package.json文件，请确保您在正确的目录中"
    exit 1
  fi
  
  # 修复crypto问题
  cat > crypto-fix.js << 'EOF'
// 确保全局对象存在
if (typeof global === 'undefined' && typeof window !== 'undefined') {
  window.global = window;
}

// 确保crypto对象存在
const contextObject = typeof global !== 'undefined' ? global : window;
if (!contextObject.crypto) {
  contextObject.crypto = {};
}

// 提供getRandomValues实现
if (!contextObject.crypto.getRandomValues) {
  contextObject.crypto.getRandomValues = function(array) {
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256);
    }
    return array;
  };
}

// 如果在Node环境中，导出模块
if (typeof module !== 'undefined' && module.exports) {
  module.exports = contextObject.crypto;
}
EOF
  info "已创建crypto修复文件"
  
  # 修改vite配置
  if [ -f "vite.config.mjs" ]; then
    sed -i 's/global: "window"/global: "globalThis"/g' vite.config.mjs || true
    info "已更新vite.config.mjs"
  fi
  
  # 安装依赖
  info "安装项目依赖..."
  npm install --legacy-peer-deps --no-optional
  
  # 构建项目
  info "开始构建项目..."
  NODE_OPTIONS="--max-old-space-size=4096 --no-warnings" \
  node -e "global.crypto={getRandomValues:b=>{for(let i=0;i<b.length;i++)b[i]=Math.floor(256*Math.random());return b}}" \
  ./node_modules/vite/bin/vite.js build
  
  if [ $? -ne 0 ]; then
    error "构建失败！请查看上面的错误信息"
    exit 1
  fi
  
  info "前端构建成功！"
}

# 部署到NAS
deploy_to_nas() {
  step "部署到群辉NAS"
  
  if [ ! -d "dist" ]; then
    error "未找到dist目录，请先构建前端"
    exit 1
  fi
  
  create_files
  
  info "开始构建Docker镜像..."
  docker-compose -f docker-compose.quick.yml build
  
  if [ $? -ne 0 ]; then
    error "Docker构建失败！"
    exit 1
  fi
  
  info "Docker镜像构建成功！"
  info "现在可以使用 './synology-quick-deploy.sh start' 启动服务"
}

# 启动服务
start_service() {
  step "启动前端服务"
  docker-compose -f docker-compose.quick.yml up -d
  
  if [ $? -eq 0 ]; then
    info "服务已成功启动！"
    info "您可以访问: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost'):80"
  else
    error "服务启动失败！"
  fi
}

# 停止服务
stop_service() {
  step "停止前端服务"
  docker-compose -f docker-compose.quick.yml down
  
  if [ $? -eq 0 ]; then
    info "服务已停止"
  else
    error "停止服务失败"
  fi
}

# 主函数
case "$1" in
  build)
    build_frontend
    ;;
  deploy)
    deploy_to_nas
    ;;
  start)
    start_service
    ;;
  stop)
    stop_service
    ;;
  *)
    echo "用法: $0 {build|deploy|start|stop}"
    echo ""
    echo "命令:"
    echo "  build   - 在本地构建前端项目"
    echo "  deploy  - 将构建好的项目部署到群辉NAS"
    echo "  start   - 启动服务"
    echo "  stop    - 停止服务"
    echo ""
    echo "典型用法流程:"
    echo "  1. ./synology-quick-deploy.sh build   (在本地机器上运行)"
    echo "  2. 上传文件到群辉NAS"
    echo "  3. ./synology-quick-deploy.sh deploy  (在NAS上运行)"
    echo "  4. ./synology-quick-deploy.sh start   (在NAS上运行)"
    exit 1
    ;;
esac 