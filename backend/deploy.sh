#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始部署后端服务...${NC}"

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p logs
mkdir -p config
chmod -R 755 logs
chmod -R 755 config

# 检查配置文件
if [ ! -f "config/db_config.py" ]; then
    echo -e "${YELLOW}创建数据库配置文件...${NC}"
    cp config/db_config.example.py config/db_config.py
    chmod 644 config/db_config.py
fi

# 停止并删除旧容器
echo -e "${YELLOW}清理旧容器...${NC}"
docker-compose down

# 构建新镜像
echo -e "${YELLOW}构建新镜像...${NC}"
docker-compose build --no-cache

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
docker-compose up -d

# 检查服务状态
echo -e "${YELLOW}检查服务状态...${NC}"
docker-compose ps

echo -e "${GREEN}部署完成！${NC}"
echo "请使用以下命令查看日志："
echo "docker-compose logs -f" 