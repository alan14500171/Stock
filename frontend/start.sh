#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 打印带颜色的消息
print_message() {
  echo -e "${GREEN}[股票交易系统前端]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
  echo -e "${RED}[错误]${NC} $1"
}

# 检查docker和docker-compose是否安装
check_docker() {
  if ! command -v docker &> /dev/null; then
    print_error "未找到docker命令，请确保Docker已安装"
    exit 1
  fi
  
  if ! command -v docker-compose &> /dev/null; then
    print_warning "未找到docker-compose命令，尝试使用docker compose"
    if ! docker compose version &> /dev/null; then
      print_error "Docker Compose未安装，请先安装"
      exit 1
    fi
    DOCKER_COMPOSE="docker compose"
  else
    DOCKER_COMPOSE="docker-compose"
  fi
}

# 检查配置文件
check_config() {
  # 检查Nginx配置文件
  if [ ! -f "./nginx.conf" ]; then
    print_error "未找到Nginx配置文件 (nginx.conf)"
    exit 1
  fi
  
  # 检查环境变量文件
  if [ ! -f "./.env.production" ]; then
    print_warning "未找到生产环境配置文件 (.env.production)，将使用默认配置"
    
    # 创建默认的环境变量文件
    echo "VITE_API_BASE_URL=http://192.168.1.100:9099" > .env.production
    print_message "已创建默认的环境变量文件，请检查 .env.production 中的API地址是否正确"
  fi
}

# 检查端口占用
check_ports() {
  print_message "检查端口占用情况..."
  
  # 检查80端口
  if netstat -tuln | grep -q ":80 "; then
    print_warning "端口80已被占用，可能会导致部署失败"
    print_message "占用端口80的进程信息："
    lsof -i :80 || netstat -tuln | grep ":80 "
    
    # 提示修改端口
    print_message "建议修改 docker-compose.nginx.yml 文件中的端口映射，例如将 80:80 改为 8080:80"
  else
    print_message "端口80未被占用，可以正常使用"
  fi
}

# 清理Docker资源
clean_docker_resources() {
  print_message "清理相关的Docker资源..."
  
  # 停止并删除相关容器
  docker stop stock-frontend 2>/dev/null || true
  docker rm stock-frontend 2>/dev/null || true
  
  print_message "Docker资源清理完成"
}

# 启动服务
start_services() {
  print_message "正在启动服务..."
  
  # 选择使用哪个Docker Compose文件
  if [ "$1" == "nginx" ]; then
    COMPOSE_FILE="docker-compose.nginx.yml"
    print_message "使用Nginx模式启动前端服务"
  else
    COMPOSE_FILE="docker-compose.yml"
    print_message "使用Node.js模式启动前端服务"
  fi
  
  # 先尝试构建镜像
  print_message "构建Docker镜像..."
  $DOCKER_COMPOSE -f $COMPOSE_FILE build
  
  if [ $? -ne 0 ]; then
    print_error "构建Docker镜像失败，请检查Dockerfile和依赖"
    exit 1
  fi
  
  # 启动服务
  print_message "启动Docker容器..."
  $DOCKER_COMPOSE -f $COMPOSE_FILE up -d
  
  if [ $? -eq 0 ]; then
    print_message "服务已成功启动！"
    
    if [ "$1" == "nginx" ]; then
      print_message "前端地址: http://localhost:80"
    else
      print_message "前端地址: http://localhost:9009"
    fi
    
    # 显示容器状态
    print_message "容器状态："
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  else
    print_error "启动服务失败，请检查日志"
    print_message "显示详细错误信息："
    $DOCKER_COMPOSE -f $COMPOSE_FILE logs
  fi
}

# 停止服务
stop_services() {
  print_message "正在停止服务..."
  
  # 选择使用哪个Docker Compose文件
  if [ "$1" == "nginx" ]; then
    COMPOSE_FILE="docker-compose.nginx.yml"
  else
    COMPOSE_FILE="docker-compose.yml"
  fi
  
  $DOCKER_COMPOSE -f $COMPOSE_FILE down
  
  if [ $? -eq 0 ]; then
    print_message "服务已停止"
  else
    print_error "停止服务失败"
  fi
}

# 查看日志
view_logs() {
  print_message "显示服务日志..."
  
  # 选择使用哪个Docker Compose文件
  if [ "$1" == "nginx" ]; then
    COMPOSE_FILE="docker-compose.nginx.yml"
  else
    COMPOSE_FILE="docker-compose.yml"
  fi
  
  $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f
}

# 显示帮助信息
show_help() {
  echo "股票交易系统前端 Docker 部署脚本"
  echo ""
  echo "用法: $0 [命令] [模式]"
  echo ""
  echo "命令:"
  echo "  start       启动服务"
  echo "  stop        停止服务"
  echo "  logs        查看日志"
  echo "  clean       清理Docker资源"
  echo "  help        显示帮助信息"
  echo ""
  echo "模式:"
  echo "  nginx       使用Nginx模式 (推荐用于生产环境)"
  echo "  node        使用Node.js模式 (默认)"
  echo ""
  echo "示例:"
  echo "  $0 start nginx    # 使用Nginx模式启动服务"
  echo "  $0 start          # 使用Node.js模式启动服务"
  echo ""
}

# 主函数
main() {
  check_docker
  
  # 获取命令和模式
  COMMAND=$1
  MODE=$2
  
  case "$COMMAND" in
    start)
      check_config
      check_ports
      start_services $MODE
      ;;
    stop)
      stop_services $MODE
      ;;
    logs)
      view_logs $MODE
      ;;
    clean)
      clean_docker_resources
      ;;
    help|*)
      show_help
      ;;
  esac
}

# 执行主函数
main "$@" 