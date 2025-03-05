#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

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

# 检查Docker是否安装
check_docker() {
    print_status "检查Docker和Docker Compose是否安装..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装。请先安装Docker。"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose未安装。尝试使用Docker内置的compose命令..."
        if ! docker compose version &> /dev/null; then
            print_error "Docker内置的compose命令也不可用。请安装Docker Compose。"
            return 1
        fi
    fi
    
    print_status "Docker和Docker Compose已安装。"
    return 0
}

# 检查配置文件
check_config_files() {
    print_status "检查必要的配置文件..."
    
    # 检查nginx.conf
    if [ ! -f "nginx.conf" ]; then
        print_error "nginx.conf文件不存在。"
        return 1
    fi
    
    # 检查.env.production
    if [ ! -f ".env.production" ]; then
        print_warning ".env.production文件不存在，将创建默认文件。"
        echo "VITE_API_BASE_URL=http://192.168.1.100:9099" > .env.production
        echo "VITE_APP_TITLE=股票交易系统" >> .env.production
        print_status "已创建默认的.env.production文件。"
    fi
    
    print_status "配置文件检查完成。"
    return 0
}

# 检查端口占用
check_port() {
    local port=$1
    print_status "检查端口 $port 是否被占用..."
    
    if command -v lsof &> /dev/null; then
        if lsof -i :$port -t &> /dev/null; then
            print_warning "端口 $port 已被占用。"
            print_warning "您可以在docker-compose文件中修改端口映射，或停止占用该端口的服务。"
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep ":$port " &> /dev/null; then
            print_warning "端口 $port 已被占用。"
            print_warning "您可以在docker-compose文件中修改端口映射，或停止占用该端口的服务。"
            return 1
        fi
    else
        print_warning "无法检查端口占用情况，因为lsof和netstat命令都不可用。"
        print_warning "如果启动失败，可能是端口 $port 已被占用。"
        return 0
    fi
    
    print_status "端口 $port 未被占用。"
    return 0
}

# 清理Docker资源
clean_docker_resources() {
    print_status "清理Docker资源..."
    
    # 停止并删除容器
    if [ "$1" == "nginx" ]; then
        docker-compose -f docker-compose.nginx.yml down 2>/dev/null || docker compose -f docker-compose.nginx.yml down
    else
        docker-compose down 2>/dev/null || docker compose down
    fi
    
    # 删除镜像
    if [ "$1" == "nginx" ]; then
        docker rmi stock-frontend-nginx:latest 2>/dev/null
    else
        docker rmi stock-frontend:latest 2>/dev/null
    fi
    
    print_status "Docker资源清理完成。"
}

# 启动服务
start_service() {
    local mode=$1
    print_status "以 $mode 模式启动服务..."
    
    # 检查配置文件
    check_config_files || return 1
    
    # 检查端口占用
    if [ "$mode" == "nginx" ]; then
        check_port 80 || return 1
    else
        check_port 9009 || return 1
    fi
    
    # 构建并启动服务
    if [ "$mode" == "nginx" ]; then
        print_status "使用Nginx模式构建和启动服务..."
        docker-compose -f docker-compose.nginx.yml build --no-cache || docker compose -f docker-compose.nginx.yml build --no-cache
        
        # 检查构建是否成功
        if [ $? -ne 0 ]; then
            print_error "Docker构建失败。请检查日志以获取更多信息。"
            print_status "尝试查看构建日志..."
            docker logs $(docker ps -a | grep stock-frontend | awk '{print $1}') 2>/dev/null
            return 1
        fi
        
        docker-compose -f docker-compose.nginx.yml up -d || docker compose -f docker-compose.nginx.yml up -d
        
        # 检查启动是否成功
        if [ $? -ne 0 ]; then
            print_error "服务启动失败。请检查日志以获取更多信息。"
            return 1
        fi
    else
        print_status "使用Node.js模式构建和启动服务..."
        docker-compose build --no-cache || docker compose build --no-cache
        
        # 检查构建是否成功
        if [ $? -ne 0 ]; then
            print_error "Docker构建失败。请检查日志以获取更多信息。"
            print_status "尝试查看构建日志..."
            docker logs $(docker ps -a | grep stock-frontend | awk '{print $1}') 2>/dev/null
            return 1
        fi
        
        docker-compose up -d || docker compose up -d
        
        # 检查启动是否成功
        if [ $? -ne 0 ]; then
            print_error "服务启动失败。请检查日志以获取更多信息。"
            return 1
        fi
    fi
    
    # 检查容器是否正在运行
    if [ "$mode" == "nginx" ]; then
        if docker ps | grep -q stock-frontend; then
            print_status "服务已成功启动。"
            print_status "您可以通过 http://localhost 访问服务。"
        else
            print_error "服务启动失败。容器未运行。"
            print_status "尝试查看容器日志..."
            docker logs $(docker ps -a | grep stock-frontend | awk '{print $1}') 2>/dev/null
            return 1
        fi
    else
        if docker ps | grep -q stock-frontend; then
            print_status "服务已成功启动。"
            print_status "您可以通过 http://localhost:9009 访问服务。"
        else
            print_error "服务启动失败。容器未运行。"
            print_status "尝试查看容器日志..."
            docker logs $(docker ps -a | grep stock-frontend | awk '{print $1}') 2>/dev/null
            return 1
        fi
    fi
    
    return 0
}

# 停止服务
stop_service() {
    local mode=$1
    print_status "停止服务..."
    
    if [ "$mode" == "nginx" ]; then
        docker-compose -f docker-compose.nginx.yml down || docker compose -f docker-compose.nginx.yml down
    else
        docker-compose down || docker compose down
    fi
    
    print_status "服务已停止。"
}

# 查看日志
view_logs() {
    local mode=$1
    print_status "查看服务日志..."
    
    if [ "$mode" == "nginx" ]; then
        docker-compose -f docker-compose.nginx.yml logs -f || docker compose -f docker-compose.nginx.yml logs -f
    else
        docker-compose logs -f || docker compose logs -f
    fi
}

# 显示帮助信息
show_help() {
    echo "股票交易系统前端服务管理脚本"
    echo ""
    echo "用法: $0 [命令] [模式]"
    echo ""
    echo "命令:"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  logs        查看日志"
    echo "  clean       清理Docker资源"
    echo "  help        显示帮助信息"
    echo ""
    echo "模式:"
    echo "  nginx       使用Nginx模式 (默认)"
    echo "  node        使用Node.js模式"
    echo ""
    echo "示例:"
    echo "  $0 start nginx    以Nginx模式启动服务"
    echo "  $0 start node     以Node.js模式启动服务"
    echo "  $0 stop           停止服务"
    echo "  $0 logs           查看日志"
}

# 检查Node.js和npm版本
check_node_version() {
    print_status "检查Node.js和npm版本..."
    
    if command -v node &> /dev/null; then
        local node_version=$(node -v)
        print_status "Node.js版本: $node_version"
    else
        print_warning "未检测到Node.js。这不会影响Docker部署，但可能影响本地开发。"
    fi
    
    if command -v npm &> /dev/null; then
        local npm_version=$(npm -v)
        print_status "npm版本: $npm_version"
    else
        print_warning "未检测到npm。这不会影响Docker部署，但可能影响本地开发。"
    fi
}

# 诊断构建问题
diagnose_build_issues() {
    print_status "诊断构建问题..."
    
    # 检查package.json是否存在
    if [ ! -f "package.json" ]; then
        print_error "package.json文件不存在。请确保您在正确的目录中。"
        return 1
    fi
    
    # 检查node_modules是否存在
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules目录不存在。这可能表明依赖项尚未安装。"
        print_status "尝试在本地安装依赖项以验证package.json是否有效..."
        
        if command -v npm &> /dev/null; then
            npm install --legacy-peer-deps
            if [ $? -ne 0 ]; then
                print_error "本地依赖项安装失败。package.json可能有问题。"
                return 1
            else
                print_status "本地依赖项安装成功。"
            fi
        else
            print_warning "未检测到npm，无法在本地验证依赖项。"
        fi
    fi
    
    # 检查vite.config.js是否存在
    if [ ! -f "vite.config.mjs" ] && [ ! -f "vite.config.js" ]; then
        print_error "vite配置文件不存在。请确保vite.config.mjs或vite.config.js文件存在。"
        return 1
    fi
    
    print_status "基本文件检查完成。"
    return 0
}

# 主函数
main() {
    # 检查Docker是否安装
    check_docker || exit 1
    
    # 检查Node.js和npm版本
    check_node_version
    
    # 解析命令行参数
    local command=${1:-"help"}
    local mode=${2:-"nginx"}
    
    case $command in
        start)
            # 诊断构建问题
            diagnose_build_issues
            
            start_service $mode
            ;;
        stop)
            stop_service $mode
            ;;
        restart)
            stop_service $mode
            start_service $mode
            ;;
        logs)
            view_logs $mode
            ;;
        clean)
            clean_docker_resources $mode
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@" 