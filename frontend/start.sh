#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 打印状态消息
print_status() {
    echo -e "${GREEN}[状态] $1${NC}"
}

# 打印警告消息
print_warning() {
    echo -e "${YELLOW}[警告] $1${NC}"
}

# 打印错误消息
print_error() {
    echo -e "${RED}[错误] $1${NC}"
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}股票交易系统前端部署脚本${NC}"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看服务状态"
    echo "  logs        查看服务日志"
    echo "  build       构建镜像"
    echo "  clean       清理资源"
    echo "  nginx       使用Nginx模式部署"
    echo "  help        显示帮助信息"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose未安装，请先安装Docker Compose${NC}"
        exit 1
    fi
}

# 检查配置文件
check_config() {
    if [ "$USE_NGINX" = true ]; then
        if [ ! -f "docker-compose.nginx.yml" ]; then
            echo -e "${RED}错误: docker-compose.nginx.yml文件不存在${NC}"
            exit 1
        fi
        
        if [ ! -f "nginx.conf" ]; then
            echo -e "${RED}错误: nginx.conf文件不存在${NC}"
            exit 1
        fi
        
        # 检查API地址配置
        if grep -q "后端实际IP地址" docker-compose.nginx.yml; then
            echo -e "${YELLOW}警告: 请修改docker-compose.nginx.yml中的后端API地址${NC}"
        fi
        
        if grep -q "后端实际IP地址" nginx.conf; then
            echo -e "${YELLOW}警告: 请修改nginx.conf中的后端API地址${NC}"
        fi
    else
        if [ ! -f "docker-compose.yml" ]; then
            echo -e "${RED}错误: docker-compose.yml文件不存在${NC}"
            exit 1
        fi
    fi
}

# 检查端口占用
check_port() {
    local port=$1
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$port "; then
            echo -e "${YELLOW}警告: 端口 $port 已被占用，可能会导致部署失败${NC}"
            return 1
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":$port "; then
            echo -e "${YELLOW}警告: 端口 $port 已被占用，可能会导致部署失败${NC}"
            return 1
        fi
    fi
    return 0
}

# 启动服务
start_service() {
    echo -e "${BLUE}正在启动服务...${NC}"
    check_docker
    check_config
    
    if [ "$USE_NGINX" = true ]; then
        check_port 80 || echo -e "${YELLOW}继续启动，但可能会失败...${NC}"
        docker-compose -f docker-compose.nginx.yml up -d
    else
        check_port 9009 || echo -e "${YELLOW}继续启动，但可能会失败...${NC}"
        docker-compose up -d
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}服务启动成功!${NC}"
        show_status
    else
        echo -e "${RED}服务启动失败，请检查日志${NC}"
        exit 1
    fi
}

# 停止服务
stop_service() {
    echo -e "${BLUE}正在停止服务...${NC}"
    
    if [ "$USE_NGINX" = true ]; then
        docker-compose -f docker-compose.nginx.yml down
    else
        docker-compose down
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}服务已停止${NC}"
    else
        echo -e "${RED}停止服务失败${NC}"
        exit 1
    fi
}

# 重启服务
restart_service() {
    stop_service
    start_service
}

# 查看服务状态
show_status() {
    echo -e "${BLUE}服务状态:${NC}"
    
    if [ "$USE_NGINX" = true ]; then
        docker-compose -f docker-compose.nginx.yml ps
    else
        docker-compose ps
    fi
}

# 查看服务日志
show_logs() {
    echo -e "${BLUE}服务日志:${NC}"
    
    if [ "$USE_NGINX" = true ]; then
        docker-compose -f docker-compose.nginx.yml logs --tail=100 -f
    else
        docker-compose logs --tail=100 -f
    fi
}

# 构建镜像
build_image() {
    echo -e "${BLUE}正在构建镜像...${NC}"
    check_docker
    
    if [ "$USE_NGINX" = true ]; then
        docker-compose -f docker-compose.nginx.yml build --no-cache
    else
        docker-compose build --no-cache
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}镜像构建成功!${NC}"
    else
        echo -e "${RED}镜像构建失败${NC}"
        exit 1
    fi
}

# 清理资源
clean_resources() {
    echo -e "${BLUE}正在清理资源...${NC}"
    
    if [ "$USE_NGINX" = true ]; then
        docker-compose -f docker-compose.nginx.yml down -v --remove-orphans
    else
        docker-compose down -v --remove-orphans
    fi
    
    echo -e "${BLUE}正在清理未使用的镜像和卷...${NC}"
    docker system prune -f
    
    echo -e "${GREEN}资源清理完成${NC}"
}

# 主函数
main() {
    # 默认不使用Nginx
    USE_NGINX=false
    
    # 如果没有参数，显示帮助
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # 处理参数
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
            show_status
            ;;
        logs)
            show_logs
            ;;
        build)
            build_image
            ;;
        clean)
            clean_resources
            ;;
        nginx)
            USE_NGINX=true
            if [ $# -gt 1 ]; then
                case "$2" in
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
                        show_status
                        ;;
                    logs)
                        show_logs
                        ;;
                    build)
                        build_image
                        ;;
                    clean)
                        clean_resources
                        ;;
                    *)
                        echo -e "${RED}未知选项: $2${NC}"
                        show_help
                        exit 1
                        ;;
                esac
            else
                echo -e "${YELLOW}使用Nginx模式，但未指定操作，默认启动服务${NC}"
                start_service
            fi
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 