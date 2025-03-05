#!/bin/bash

# 群辉NAS专用部署脚本
# 用法: ./synology-deploy.sh [start|stop|restart|status|rebuild]

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 检查Docker是否安装
check_docker() {
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误：未检测到Docker，请先安装Docker${NC}"
    exit 1
  fi
  
  if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误：未检测到docker-compose，请先安装${NC}"
    exit 1
  fi
}

# 检查配置文件
check_config() {
  if [ ! -f "docker-compose.nginx.yml" ]; then
    echo -e "${RED}错误：未找到docker-compose.nginx.yml配置文件${NC}"
    exit 1
  fi
  
  if [ ! -f "nginx.conf" ]; then
    echo -e "${RED}错误：未找到nginx.conf配置文件${NC}"
    exit 1
  }
}

# 启动服务
start_service() {
  echo -e "${BLUE}正在启动股票交易系统前端服务...${NC}"
  docker-compose -f docker-compose.nginx.yml up -d
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}服务启动成功！${NC}"
    echo -e "您可以通过访问 ${YELLOW}http://您的群辉NAS IP${NC} 来访问服务"
  else
    echo -e "${RED}服务启动失败，请检查错误信息${NC}"
  fi
}

# 停止服务
stop_service() {
  echo -e "${BLUE}正在停止股票交易系统前端服务...${NC}"
  docker-compose -f docker-compose.nginx.yml down
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}服务已停止${NC}"
  else
    echo -e "${RED}服务停止失败，请检查错误信息${NC}"
  fi
}

# 重启服务
restart_service() {
  stop_service
  sleep 2
  start_service
}

# 查看服务状态
check_status() {
  echo -e "${BLUE}服务状态:${NC}"
  docker-compose -f docker-compose.nginx.yml ps
  
  echo -e "\n${BLUE}容器日志:${NC}"
  docker logs stock-frontend-nginx --tail 20
}

# 重建服务
rebuild_service() {
  echo -e "${BLUE}正在重建股票交易系统前端服务...${NC}"
  docker-compose -f docker-compose.nginx.yml build --no-cache
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}构建成功，正在启动服务...${NC}"
    docker-compose -f docker-compose.nginx.yml up -d
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}服务启动成功！${NC}"
    else
      echo -e "${RED}服务启动失败，请检查错误信息${NC}"
    fi
  else
    echo -e "${RED}构建失败，请检查错误信息${NC}"
  fi
}

# 使用简化版部署（不需要在NAS上构建）
simplified_deploy() {
  echo -e "${BLUE}正在使用简化版Dockerfile部署...${NC}"
  
  if [ ! -f "simplified-dockerfile" ]; then
    echo -e "${RED}错误：未找到simplified-dockerfile文件${NC}"
    exit 1
  fi
  
  if [ ! -d "dist" ]; then
    echo -e "${RED}错误：未找到dist目录，请先在本地机器上构建项目${NC}"
    exit 1
  fi
  
  docker build -t stock-frontend-simplified -f simplified-dockerfile .
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}构建成功，正在启动服务...${NC}"
    docker stop stock-frontend-simplified || true
    docker rm stock-frontend-simplified || true
    docker run -d --name stock-frontend-simplified --network host stock-frontend-simplified
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}服务启动成功！${NC}"
    else
      echo -e "${RED}服务启动失败，请检查错误信息${NC}"
    fi
  else
    echo -e "${RED}构建失败，请检查错误信息${NC}"
  fi
}

# 修复群辉NAS特有问题
fix_synology_issues() {
  echo -e "${BLUE}正在修复群辉NAS特有问题...${NC}"
  
  # 检查是否有XSym错误
  echo -e "${YELLOW}检查Docker构建日志中是否有XSym错误...${NC}"
  docker logs $(docker ps -a | grep stock-frontend | awk '{print $1}') 2>&1 | grep -i XSym
  
  if [ $? -eq 0 ]; then
    echo -e "${RED}检测到XSym错误，尝试修复...${NC}"
    
    # 将容器提交为新镜像进行调试
    CONTAINER_ID=$(docker ps -a | grep stock-frontend | awk '{print $1}')
    if [ -n "$CONTAINER_ID" ]; then
      docker commit $CONTAINER_ID stock-frontend-debug
      echo -e "${GREEN}已创建调试镜像: stock-frontend-debug${NC}"
      echo -e "${YELLOW}您可以使用以下命令进入调试环境:${NC}"
      echo -e "docker run -it --rm stock-frontend-debug /bin/sh"
    else
      echo -e "${RED}未找到相关容器${NC}"
    fi
    
    echo -e "${YELLOW}建议使用简化版部署方式避开构建问题...${NC}"
    echo -e "使用命令: ./synology-deploy.sh simplified"
  else
    echo -e "${GREEN}未检测到XSym错误${NC}"
  fi
}

# 主函数
main() {
  # 检查Docker安装
  check_docker
  
  # 检查参数
  if [ $# -eq 0 ]; then
    echo -e "${YELLOW}用法: $0 [start|stop|restart|status|rebuild|simplified|fix]${NC}"
    exit 1
  fi
  
  # 根据参数执行相应操作
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
    rebuild)
      rebuild_service
      ;;
    simplified)
      simplified_deploy
      ;;
    fix)
      fix_synology_issues
      ;;
    *)
      echo -e "${RED}无效的参数: $1${NC}"
      echo -e "${YELLOW}用法: $0 [start|stop|restart|status|rebuild|simplified|fix]${NC}"
      exit 1
      ;;
  esac
}

# 执行主函数
main "$@" 