#!/bin/bash
#
# 群辉NAS前端部署脚本
# 用法: ./deploy.sh [命令]
# 命令: build, start, stop, logs

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 日志函数
log_info() { echo -e "${GREEN}[信息]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
log_error() { echo -e "${RED}[错误]${NC} $1"; }
log_step() { echo -e "${BLUE}[步骤]${NC} $1"; }

# 检查Docker是否存在
check_docker() {
  if ! command -v docker &> /dev/null; then
    log_error "未安装Docker！请先在群辉控制面板中安装Docker"
    exit 1
  fi
  
  if ! command -v docker-compose &> /dev/null; then
    log_error "未安装docker-compose！请确保已安装Docker Compose"
    exit 1
  fi
}

# 构建前端Docker镜像
build_frontend() {
  log_step "开始构建前端Docker镜像"
  
  # 确保文件存在
  if [ ! -f "Dockerfile.simple" ]; then
    log_error "Dockerfile.simple文件不存在！"
    exit 1
  fi
  
  if [ ! -f "docker-compose.frontend.yml" ]; then
    log_error "docker-compose.frontend.yml文件不存在！"
    exit 1
  fi
  
  # 构建镜像
  docker-compose -f docker-compose.frontend.yml build
  
  if [ $? -eq 0 ]; then
    log_info "前端Docker镜像构建成功！"
  else
    log_error "前端Docker镜像构建失败！请检查错误日志"
    exit 1
  fi
}

# 启动前端服务
start_frontend() {
  log_step "启动前端服务"
  docker-compose -f docker-compose.frontend.yml up -d
  
  if [ $? -eq 0 ]; then
    log_info "前端服务启动成功！"
    log_info "您可以通过以下地址访问前端: http://$(hostname -I | awk '{print $1}'):80"
  else
    log_error "前端服务启动失败！请检查错误日志"
    exit 1
  fi
}

# 停止前端服务
stop_frontend() {
  log_step "停止前端服务"
  docker-compose -f docker-compose.frontend.yml down
  
  if [ $? -eq 0 ]; then
    log_info "前端服务已停止"
  else
    log_error "停止前端服务失败"
  fi
}

# 查看日志
show_logs() {
  log_step "显示前端容器日志"
  docker logs stock-frontend --tail 100 -f
}

# 检查健康状态
check_health() {
  log_step "检查前端服务健康状态"
  
  # 获取容器状态
  CONTAINER_STATUS=$(docker ps -a --filter "name=stock-frontend" --format "{{.Status}}")
  
  if [[ $CONTAINER_STATUS == *"Up"* ]]; then
    log_info "容器状态: 运行中"
    
    # 检查健康状态
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' stock-frontend)
    log_info "健康状态: $HEALTH_STATUS"
    
    # 尝试访问健康检查端点
    if command -v wget &> /dev/null; then
      HEALTH_CHECK=$(wget -qO- http://localhost:80/health 2>/dev/null)
      if [ "$HEALTH_CHECK" == "ok" ]; then
        log_info "健康检查端点响应正常"
      else
        log_warn "健康检查端点响应异常"
      fi
    fi
    
    # 检查API连接
    if command -v curl &> /dev/null; then
      API_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9099/api/health 2>/dev/null)
      if [ "$API_CHECK" == "200" ]; then
        log_info "与后端API连接正常"
      else
        log_warn "与后端API连接异常 (HTTP状态码: $API_CHECK)"
      fi
    fi
  else
    log_warn "容器未运行！当前状态: $CONTAINER_STATUS"
  fi
}

# 主函数
main() {
  check_docker
  
  case "$1" in
    build)
      build_frontend
      ;;
    start)
      start_frontend
      ;;
    stop)
      stop_frontend
      ;;
    logs)
      show_logs
      ;;
    health)
      check_health
      ;;
    *)
      echo "用法: $0 {build|start|stop|logs|health}"
      echo ""
      echo "命令:"
      echo "  build   - 构建前端Docker镜像"
      echo "  start   - 启动前端服务"
      echo "  stop    - 停止前端服务"
      echo "  logs    - 查看服务日志"
      echo "  health  - 检查服务健康状态"
      echo ""
      echo "推荐使用流程:"
      echo "  1. ./deploy.sh build"
      echo "  2. ./deploy.sh start"
      echo "  3. ./deploy.sh health"
      exit 1
      ;;
  esac
}

main "$@" 