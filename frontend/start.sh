#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装。请先在群辉套件中心安装Docker。"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装。请确保Docker套件已正确安装。"
        exit 1
    fi
}

# 检查配置文件
check_config_files() {
    if [ ! -f "docker-compose.nginx.yml" ]; then
        log_error "docker-compose.nginx.yml文件不存在。"
        exit 1
    fi
    
    if [ ! -f "nginx.conf" ]; then
        log_error "nginx.conf文件不存在。"
        exit 1
    fi
    
    if [ ! -f "Dockerfile.nginx" ]; then
        log_error "Dockerfile.nginx文件不存在。"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$port "; then
            return 0
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":$port "; then
            return 0
        fi
    else
        log_warning "无法检查端口占用情况，netstat和ss命令都不可用。"
        return 1
    fi
    return 1
}

# 启动服务
start_service() {
    log_info "正在启动前端服务..."
    
    # 检查端口占用
    if check_port 8080; then
        log_warning "端口8080已被占用。请修改docker-compose.nginx.yml中的端口映射。"
        log_info "您可以编辑docker-compose.nginx.yml文件，将'8080:80'改为其他端口，如'8081:80'"
        read -p "是否继续启动？(y/n): " continue_start
        if [[ "$continue_start" != "y" && "$continue_start" != "Y" ]]; then
            log_info "已取消启动。"
            exit 0
        fi
    fi
    
    # 群辉NAS特定处理
    if [ -f "/etc/synoinfo.conf" ]; then
        log_info "检测到群辉NAS环境，应用特定配置..."
        
        # 检查是否需要使用host网络模式
        if grep -q "network_mode: \"host\"" docker-compose.nginx.yml; then
            log_info "已配置host网络模式。"
        else
            log_warning "群辉NAS环境可能需要使用host网络模式。"
            log_info "如果遇到网络问题，请取消注释docker-compose.nginx.yml中的'network_mode: \"host\"'行。"
        fi
    fi
    
    docker-compose -f docker-compose.nginx.yml up -d
    
    if [ $? -eq 0 ]; then
        log_success "前端服务已成功启动！"
        log_info "您可以通过以下地址访问：http://$(hostname -I | awk '{print $1}'):8080"
    else
        log_error "启动服务失败，请检查错误信息。"
    fi
}

# 停止服务
stop_service() {
    log_info "正在停止前端服务..."
    docker-compose -f docker-compose.nginx.yml down
    
    if [ $? -eq 0 ]; then
        log_success "前端服务已停止。"
    else
        log_error "停止服务失败，请检查错误信息。"
    fi
}

# 重启服务
restart_service() {
    log_info "正在重启前端服务..."
    docker-compose -f docker-compose.nginx.yml restart
    
    if [ $? -eq 0 ]; then
        log_success "前端服务已重启。"
    else
        log_error "重启服务失败，请检查错误信息。"
    fi
}

# 查看日志
view_logs() {
    log_info "查看服务日志..."
    docker-compose -f docker-compose.nginx.yml logs -f
}

# 重建服务
rebuild_service() {
    log_info "正在重建前端服务..."
    docker-compose -f docker-compose.nginx.yml down
    docker-compose -f docker-compose.nginx.yml build --no-cache
    docker-compose -f docker-compose.nginx.yml up -d
    
    if [ $? -eq 0 ]; then
        log_success "前端服务已重建并启动。"
    else
        log_error "重建服务失败，请检查错误信息。"
    fi
}

# 清理资源
clean_resources() {
    log_info "正在清理资源..."
    docker-compose -f docker-compose.nginx.yml down -v
    docker rmi stock-frontend-nginx:latest
    
    if [ $? -eq 0 ]; then
        log_success "资源已清理。"
    else
        log_warning "清理资源时出现一些问题，但可能不影响使用。"
    fi
}

# 检查服务状态
check_status() {
    log_info "检查服务状态..."
    docker-compose -f docker-compose.nginx.yml ps
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}股票交易系统前端部署脚本${NC}"
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  up        启动服务"
    echo "  down      停止服务"
    echo "  restart   重启服务"
    echo "  logs      查看日志"
    echo "  rebuild   重建并启动服务"
    echo "  clean     清理资源"
    echo "  status    检查服务状态"
    echo "  help      显示此帮助信息"
}

# 主函数
main() {
    # 检查Docker安装
    check_docker
    
    # 检查配置文件
    check_config_files
    
    # 处理命令行参数
    case "$1" in
        up)
            start_service
            ;;
        down)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        logs)
            view_logs
            ;;
        rebuild)
            rebuild_service
            ;;
        clean)
            clean_resources
            ;;
        status)
            check_status
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@" 