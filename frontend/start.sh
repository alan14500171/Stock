#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 配置文件
DOCKER_COMPOSE_FILE="docker-compose.nginx.yml"
CONTAINER_NAME="stock-frontend-nginx"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行或当前用户没有权限"
        log_info "请尝试以下命令："
        log_info "  sudo systemctl start docker"
        log_info "  或者将当前用户添加到docker组：sudo usermod -aG docker \$USER"
        exit 1
    fi
    
    log_info "Docker检查通过"
}

# 检查配置文件是否存在
check_config() {
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "配置文件 $DOCKER_COMPOSE_FILE 不存在"
        exit 1
    fi
    
    log_info "配置文件检查通过"
}

# 检查端口是否可用
check_port() {
    PORT=$(grep -oP '(?<=:)[0-9]+(?=:)' "$DOCKER_COMPOSE_FILE" | head -1)
    if [ -z "$PORT" ]; then
        PORT=8080 # 默认端口
    fi
    
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$PORT "; then
            log_warn "端口 $PORT 已被占用，可能会导致启动失败"
        else
            log_info "端口 $PORT 可用"
        fi
    else
        log_warn "无法检查端口占用情况，netstat命令不可用"
    fi
}

# 检查是否为群辉NAS环境
check_synology() {
    if [ -f "/etc/synoinfo.conf" ]; then
        log_info "检测到群辉NAS环境"
        # 群辉NAS特定配置
        if grep -q "network_mode: \"host\"" "$DOCKER_COMPOSE_FILE"; then
            log_info "已配置host网络模式"
        else
            log_warn "建议在群辉NAS环境中使用host网络模式"
        fi
    fi
}

# 启动服务
start_service() {
    log_info "正在启动服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    if [ $? -eq 0 ]; then
        log_info "服务已成功启动"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "正在停止服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    if [ $? -eq 0 ]; then
        log_info "服务已停止"
    else
        log_error "服务停止失败"
        exit 1
    fi
}

# 重启服务
restart_service() {
    log_info "正在重启服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart
    if [ $? -eq 0 ]; then
        log_info "服务已重启"
    else
        log_error "服务重启失败"
        exit 1
    fi
}

# 查看服务状态
status_service() {
    log_info "服务状态："
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
}

# 查看服务日志
logs_service() {
    log_info "服务日志："
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=100
}

# 构建镜像
build_image() {
    log_info "正在构建镜像..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build
    if [ $? -eq 0 ]; then
        log_info "镜像构建成功"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 重新构建并启动
rebuild_service() {
    log_info "正在重新构建并启动服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build
    if [ $? -eq 0 ]; then
        log_info "服务已重新构建并启动"
    else
        log_error "服务重新构建失败"
        exit 1
    fi
}

# 清理资源
clean_resources() {
    log_warn "此操作将删除所有未使用的镜像、容器和网络"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "正在清理资源..."
        docker system prune -f
        log_info "资源清理完成"
    fi
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ]; then
        log_error "缺少参数"
        echo "用法: $0 {start|stop|restart|status|logs|build|rebuild|clean}"
        exit 1
    fi

    # 根据参数执行相应操作
    case "$1" in
        start)
            check_docker
            check_config
            check_port
            check_synology
            start_service
            ;;
        stop)
            check_config
            stop_service
            ;;
        restart)
            check_config
            restart_service
            ;;
        status)
            check_config
            status_service
            ;;
        logs)
            check_config
            logs_service
            ;;
        build)
            check_docker
            check_config
            build_image
            ;;
        rebuild)
            check_docker
            check_config
            rebuild_service
            ;;
        clean)
            check_docker
            clean_resources
            ;;
        *)
            log_error "未知参数: $1"
            echo "用法: $0 {start|stop|restart|status|logs|build|rebuild|clean}"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 