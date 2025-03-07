#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}=================================${NC}"
echo -e "${PURPLE}  股票交易系统前端部署工具 v1.0  ${NC}"
echo -e "${PURPLE}=================================${NC}"
echo -e "${CYAN}适用于群辉NAS的前端自动部署脚本${NC}"
echo -e "${CYAN}支持：部署、停止、日志查看、状态检查${NC}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: 未安装Docker。请先安装Docker。${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: 未安装Docker Compose。请先安装Docker Compose。${NC}"
    exit 1
fi

# 服务名称
SERVICE_NAME="stock-frontend"
COMPOSE_FILE="docker-compose.simple.yml"
NGINX_CONF="nginx-synology.conf"

# 显示使用说明
show_usage() {
    echo -e "${BLUE}使用方法:${NC}"
    echo -e "  ${YELLOW}$0 deploy${NC}  - 部署前端服务"
    echo -e "  ${YELLOW}$0 stop${NC}    - 停止前端服务"
    echo -e "  ${YELLOW}$0 logs${NC}    - 查看服务日志"
    echo -e "  ${YELLOW}$0 status${NC}  - 检查服务状态"
    echo -e "  ${YELLOW}$0 health${NC}  - 检查健康状态"
    echo -e "  ${YELLOW}$0 help${NC}    - 显示此帮助信息"
    echo ""
}

# 部署服务
deploy_service() {
    echo -e "${BLUE}开始部署前端服务...${NC}"
    
    # 添加调试信息
    echo -e "${BLUE}[调试] 当前工作目录: $(pwd)${NC}"
    echo -e "${BLUE}[调试] Docker版本: $(docker --version)${NC}"
    echo -e "${BLUE}[调试] Docker Compose版本: $(docker-compose --version)${NC}"
    
    # 检查dist目录
    if [ ! -d "./dist" ]; then
        echo -e "${RED}错误: dist目录不存在，请先构建前端项目${NC}"
        exit 1
    fi
    
    # 检查dist/index.html是否存在
    if [ ! -f "./dist/index.html" ]; then
        echo -e "${RED}错误: dist/index.html不存在，请确认构建是否成功${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}[调试] 检查dist目录内容:${NC}"
    ls -la ./dist
    
    # 检查Nginx配置
    if [ ! -f "./nginx-synology.conf" ]; then
        echo -e "${RED}错误: nginx-synology.conf不存在${NC}"
        exit 1
    fi
    
    # 创建健康检查文件
    echo "ok" > ./dist/health.html
    
    # 停止之前的容器
    echo -e "${BLUE}[调试] 停止现有容器...${NC}"
    docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
    
    # 启动容器
    echo -e "${BLUE}[调试] 启动新容器...${NC}"
    if docker-compose -f docker-compose.simple.yml up -d; then
        echo -e "${GREEN}前端应用部署成功!${NC}"
        echo -e "${BLUE}[调试] 容器状态:${NC}"
        docker ps | grep stock-frontend
        
        # 等待服务启动
        echo -e "${BLUE}等待服务启动...${NC}"
        sleep 5
        
        # 检查服务健康状态
        if curl -s http://localhost/health.html | grep -q "ok"; then
            echo -e "${GREEN}服务健康检查通过!${NC}"
        else
            echo -e "${RED}警告: 服务健康检查失败，请检查日志${NC}"
            docker-compose -f docker-compose.simple.yml logs
        fi
    else
        echo -e "${RED}部署失败，请查看错误信息${NC}"
        docker-compose -f docker-compose.simple.yml logs
        exit 1
    fi
}

# 停止服务
stop_service() {
    echo -e "${BLUE}停止前端服务...${NC}"
    docker-compose -f $COMPOSE_FILE down
    
    if ! docker ps | grep -q "$SERVICE_NAME"; then
        echo -e "${GREEN}✓ 服务已停止${NC}"
    else
        echo -e "${RED}✗ 服务停止失败${NC}"
        exit 1
    fi
}

# 查看日志
view_logs() {
    echo -e "${BLUE}显示服务日志...${NC}"
    docker-compose -f $COMPOSE_FILE logs
}

# 检查状态
check_status() {
    echo -e "${BLUE}检查服务状态...${NC}"
    
    if docker ps | grep -q "$SERVICE_NAME"; then
        container_id=$(docker ps | grep "$SERVICE_NAME" | awk '{print $1}')
        echo -e "${GREEN}✓ 服务正在运行${NC}"
        echo -e "${YELLOW}容器ID: ${NC}$container_id"
        echo -e "${YELLOW}运行时间: ${NC}$(docker ps --format "{{.RunningFor}}" --filter "id=$container_id")"
        echo -e "${YELLOW}端口: ${NC}$(docker ps --format "{{.Ports}}" --filter "id=$container_id")"
        echo -e "${YELLOW}状态: ${NC}$(docker ps --format "{{.Status}}" --filter "id=$container_id")"
    else
        echo -e "${RED}✗ 服务未运行${NC}"
    fi
}

# 健康检查
check_health() {
    echo -e "${BLUE}执行健康检查...${NC}"
    
    # 检查容器是否运行
    if ! docker ps | grep -q "$SERVICE_NAME"; then
        echo -e "${RED}✗ 服务未运行${NC}"
        exit 1
    fi
    
    # 检查前端健康端点
    http_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ 前端健康检查通过${NC}"
    else
        echo -e "${RED}✗ 前端健康检查失败 (HTTP状态码: $http_code)${NC}"
    fi
    
    # 检查后端连接
    echo -e "${YELLOW}检查后端API连接...${NC}"
    backend_url=$(grep -o "proxy_pass [^;]*" $NGINX_CONF | head -1 | awk '{print $2}')
    
    if [ -z "$backend_url" ]; then
        echo -e "${RED}✗ 无法从Nginx配置中获取后端URL${NC}"
    else
        # 从URL中提取主机和端口
        backend_host=$(echo $backend_url | sed -E 's|http://([^:/]+)(:[0-9]+)?.*|\1|')
        backend_port=$(echo $backend_url | grep -o ':[0-9]\+' | sed 's/://')
        
        if [ -z "$backend_port" ]; then
            backend_port=80
        fi
        
        # 检查主机端口是否可达
        if nc -z -w5 $backend_host $backend_port 2>/dev/null; then
            echo -e "${GREEN}✓ 后端API可达 ($backend_host:$backend_port)${NC}"
        else
            echo -e "${RED}✗ 无法连接到后端API ($backend_host:$backend_port)${NC}"
        fi
    fi
}

# 主程序
case "$1" in
    deploy)
        deploy_service
        ;;
    stop)
        stop_service
        ;;
    logs)
        view_logs
        ;;
    status)
        check_status
        ;;
    health)
        check_health
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${YELLOW}未知的命令: $1${NC}"
        show_usage
        exit 1
        ;;
esac

exit 0 