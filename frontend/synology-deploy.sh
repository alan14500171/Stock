#!/bin/bash

# 群辉NAS股票交易系统前端部署脚本
# 用法: ./synology-deploy.sh [命令]
# 命令: start, stop, restart, status, build, buildlocal

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 日志函数
log_info() {
  echo -e "${GREEN}[信息]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
  echo -e "${RED}[错误]${NC} $1"
}

log_step() {
  echo -e "${BLUE}[步骤]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
  if ! command -v docker &> /dev/null; then
    log_error "未找到Docker。请确保在群辉NAS上安装了Docker。"
    exit 1
  fi
  
  if ! command -v docker-compose &> /dev/null; then
    log_error "未找到docker-compose。请确保在群辉NAS上安装了Docker Compose。"
    exit 1
  fi
}

# 检查必要文件
check_files() {
  local missing_files=false
  
  if [ ! -f "Dockerfile.synology" ]; then
    log_error "未找到Dockerfile.synology"
    missing_files=true
  fi
  
  if [ ! -f "docker-compose.synology.yml" ]; then
    log_error "未找到docker-compose.synology.yml"
    missing_files=true
  fi
  
  if [ ! -d "synology" ]; then
    log_error "未找到synology目录"
    missing_files=true
  fi
  
  if [ "$missing_files" = true ]; then
    log_error "缺少必要的文件，请检查部署准备步骤。"
    exit 1
  fi
}

# 启动服务
start_service() {
  log_step "正在启动股票交易系统前端服务..."
  docker-compose -f docker-compose.synology.yml up -d
  
  if [ $? -eq 0 ]; then
    log_info "服务已成功启动！"
    log_info "访问地址: http://$(hostname -I | awk '{print $1}'):80"
  else
    log_error "服务启动失败，请检查错误信息。"
  fi
}

# 停止服务
stop_service() {
  log_step "正在停止股票交易系统前端服务..."
  docker-compose -f docker-compose.synology.yml down
  
  if [ $? -eq 0 ]; then
    log_info "服务已成功停止！"
  else
    log_error "服务停止失败，请检查错误信息。"
  fi
}

# 重启服务
restart_service() {
  log_step "正在重启股票交易系统前端服务..."
  stop_service
  start_service
}

# 检查服务状态
check_status() {
  log_step "检查服务状态..."
  docker ps --filter "name=stock-frontend"
  
  if [ $? -ne 0 ]; then
    log_error "无法获取容器状态。"
    return
  fi
  
  if docker ps --filter "name=stock-frontend" | grep -q "stock-frontend"; then
    log_info "服务正在运行。"
    log_info "容器日志 (最近10行):"
    docker logs --tail 10 stock-frontend
  else
    log_warn "服务未运行。"
  fi
}

# 在群辉NAS上构建
build_on_nas() {
  log_step "在群辉NAS上构建服务..."
  check_files
  
  log_info "开始构建Docker镜像..."
  docker-compose -f docker-compose.synology.yml build --no-cache
  
  if [ $? -eq 0 ]; then
    log_info "Docker镜像构建成功！"
    log_info "现在您可以使用 ./synology-deploy.sh start 启动服务。"
  else
    log_error "Docker镜像构建失败。"
    log_error "请检查构建日志了解详情。"
  fi
}

# 本地构建，上传到NAS
build_local() {
  log_step "准备本地构建环境..."
  
  # 确保synology目录存在
  if [ ! -d "synology" ]; then
    mkdir -p synology
    log_info "创建了synology目录"
  fi
  
  # 创建crypto-fix.js
  if [ ! -f "synology/crypto-fix.js" ]; then
    log_warn "未找到crypto-fix.js，将创建此文件"
    cat > synology/crypto-fix.js << 'EOF'
/**
 * crypto-fix.js - 为群辉NAS环境提供的加密API修复
 * 
 * 这个文件解决了在群辉NAS Docker环境中出现的
 * "crypto.getRandomValues is not a function"错误
 */

// 检查环境
const isNode = typeof window === 'undefined';
const contextObject = isNode ? global : window;

// 定义一个安全的随机数生成函数
function secureRandomValues(buffer) {
  if (buffer.length > 65536) {
    throw new Error("请求的随机值太多");
  }
  
  // 如果我们在Node环境中
  if (isNode) {
    try {
      // 尝试使用Node的crypto模块
      const nodeCrypto = require('crypto');
      const bytes = nodeCrypto.randomBytes(buffer.length);
      
      // 复制到目标buffer
      for (let i = 0; i < buffer.length; i++) {
        buffer[i] = bytes[i];
      }
      
      return buffer;
    } catch (error) {
      console.warn("Node crypto模块不可用，使用备用方法");
    }
  }
  
  // 备用方法
  for (let i = 0; i < buffer.length; i++) {
    buffer[i] = Math.floor(Math.random() * 256);
  }
  
  return buffer;
}

// 确保crypto对象存在
if (!contextObject.crypto) {
  contextObject.crypto = {};
}

// 如果getRandomValues不存在，提供一个实现
if (!contextObject.crypto.getRandomValues) {
  contextObject.crypto.getRandomValues = secureRandomValues;
  console.log("已添加crypto.getRandomValues polyfill");
}

// 为Node环境导出
if (isNode) {
  module.exports = contextObject.crypto;
} else {
  // 浏览器环境无需导出
  console.log("crypto polyfill已应用到window对象");
}
EOF
  fi
  
  # 本地构建并打包
  log_step "开始本地构建..."
  if [ ! -f ".env.production" ]; then
    log_warn "未找到.env.production文件，创建默认配置"
    echo "VITE_API_BASE_URL=http://localhost:9099" > .env.production
    log_info "创建了.env.production文件，请根据需要修改API地址"
  fi
  
  log_info "安装依赖..."
  npm install --legacy-peer-deps
  
  if [ $? -ne 0 ]; then
    log_error "依赖安装失败，请检查NPM错误。"
    exit 1
  fi
  
  log_info "构建项目..."
  npm run build
  
  if [ $? -ne 0 ]; then
    log_error "项目构建失败，请检查构建错误。"
    exit 1
  fi
  
  log_info "项目构建成功！"
  log_info "请将构建产物(dist目录)上传到群辉NAS。"
  log_info "然后在NAS上使用简化Dockerfile部署。"
  
  # 创建简化Dockerfile
  cat > Dockerfile.simple << 'EOF'
FROM nginx:alpine

WORKDIR /usr/share/nginx/html

COPY dist/ .
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD wget -q --spider http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF
  
  log_info "创建了简化Dockerfile: Dockerfile.simple"
  log_info "请将此文件与dist目录一起上传到NAS。"
}

# 主函数
main() {
  check_docker
  
  case "$1" in
    start)
      start_service
      ;;
    stop)
      stop_service
      ;;
    restart)
      restart_service
      ;;
    status)
      check_status
      ;;
    build)
      build_on_nas
      ;;
    buildlocal)
      build_local
      ;;
    *)
      echo "用法: $0 {start|stop|restart|status|build|buildlocal}"
      echo ""
      echo "命令说明:"
      echo "  start      - 启动前端服务"
      echo "  stop       - 停止前端服务"
      echo "  restart    - 重启前端服务"
      echo "  status     - 检查服务状态"
      echo "  build      - 在群辉NAS上构建并部署前端"
      echo "  buildlocal - 在本地构建前端，生成可上传到NAS的文件"
      echo ""
      exit 1
      ;;
  esac
}

# 执行主函数
main "$@" 