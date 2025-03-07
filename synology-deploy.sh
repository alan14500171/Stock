#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}股票交易系统 - 群辉NAS部署脚本${NC}"
echo "================================="

# 检查必要目录
echo -e "${YELLOW}检查并创建必要目录...${NC}"
mkdir -p logs
chmod 777 logs

# 检查配置文件
if [ ! -f "./backend/config/db_config.py" ]; then
    echo -e "${YELLOW}创建数据库配置文件...${NC}"
    cp ./backend/config/db_config.example.py ./backend/config/db_config.py
    echo -e "${GREEN}请修改 backend/config/db_config.py 中的数据库配置${NC}"
fi

# 设置文件权限
echo -e "${YELLOW}设置文件权限...${NC}"
chmod -R 755 ./backend/scripts
chmod -R 755 ./backend/*.sh
chmod -R 755 ./frontend/*.sh

# 创建docker网络（如果不存在）
echo -e "${YELLOW}创建docker网络...${NC}"
docker network create stock-network 2>/dev/null || true

# 停止并删除旧容器
echo -e "${YELLOW}清理旧容器...${NC}"
docker-compose down

# 构建并启动服务
echo -e "${YELLOW}构建并启动服务...${NC}"
docker-compose build --no-cache
docker-compose up -d

# 检查服务状态
echo -e "${YELLOW}检查服务状态...${NC}"
docker-compose ps

echo -e "${GREEN}部署完成！${NC}"
echo -e "后端API地址: http://localhost:9099"
echo -e "前端访问地址: http://localhost:9009"
echo -e "\n${YELLOW}提示：${NC}"
echo "1. 如果是首次部署，请确保已经正确配置数据库连接"
echo "2. 可以通过 'docker-compose logs -f' 查看服务日志"
echo "3. 如果遇到问题，请检查 logs 目录下的日志文件" 