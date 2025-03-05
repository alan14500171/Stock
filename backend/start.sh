#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 打印带颜色的消息
print_message() {
  echo -e "${GREEN}[股票交易系统]${NC} $1"
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
  if [ ! -f "./config/db_config.py" ]; then
    print_warning "未找到数据库配置文件，将从示例文件创建"
    if [ -f "./config/db_config.example.py" ]; then
      cp ./config/db_config.example.py ./config/db_config.py
      print_message "已创建配置文件，请修改 ./config/db_config.py 中的数据库连接信息"
    else
      print_error "未找到示例配置文件，请手动创建配置文件"
      exit 1
    fi
  fi
}

# 创建必要的目录
create_directories() {
  mkdir -p logs
  mkdir -p init-db
  
  # 设置权限
  chmod -R 755 logs
  chmod -R 755 init-db
  
  print_message "已创建必要的目录"
}

# 启动服务
start_services() {
  print_message "正在启动服务..."
  $DOCKER_COMPOSE up -d
  
  if [ $? -eq 0 ]; then
    print_message "服务已成功启动！"
    print_message "后端API地址: http://localhost:9099"
    print_message "数据库地址: localhost:3306"
  else
    print_error "启动服务失败，请检查日志"
  fi
}

# 停止服务
stop_services() {
  print_message "正在停止服务..."
  $DOCKER_COMPOSE down
  
  if [ $? -eq 0 ]; then
    print_message "服务已停止"
  else
    print_error "停止服务失败"
  fi
}

# 重启服务
restart_services() {
  print_message "正在重启服务..."
  $DOCKER_COMPOSE restart
  
  if [ $? -eq 0 ]; then
    print_message "服务已重启"
  else
    print_error "重启服务失败"
  fi
}

# 查看日志
view_logs() {
  print_message "显示服务日志..."
  $DOCKER_COMPOSE logs -f
}

# 重置管理员密码
reset_admin_password() {
  print_message "正在重置管理员密码..."
  $DOCKER_COMPOSE exec stock-backend python scripts/reset_admin_password.py
  
  if [ $? -eq 0 ]; then
    print_message "管理员密码已重置"
  else
    print_error "重置密码失败"
  fi
}

# 显示帮助信息
show_help() {
  echo "股票交易系统 Docker 部署脚本"
  echo ""
  echo "用法: $0 [命令]"
  echo ""
  echo "命令:"
  echo "  start       启动服务"
  echo "  stop        停止服务"
  echo "  restart     重启服务"
  echo "  logs        查看日志"
  echo "  reset-pwd   重置管理员密码"
  echo "  help        显示帮助信息"
  echo ""
}

# 主函数
main() {
  check_docker
  
  case "$1" in
    start)
      check_config
      create_directories
      start_services
      ;;
    stop)
      stop_services
      ;;
    restart)
      restart_services
      ;;
    logs)
      view_logs
      ;;
    reset-pwd)
      reset_admin_password
      ;;
    help|*)
      show_help
      ;;
  esac
}

# 执行主函数
main "$@" 