#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始部署前端服务...${NC}"

# 检查dist目录
if [ ! -d "../dist" ]; then
    echo -e "${RED}错误: dist目录不存在，请先构建前端项目${NC}"
    echo -e "运行: ${YELLOW}npm run build${NC}"
    exit 1
fi

# 检查dist/index.html是否存在
if [ ! -f "../dist/index.html" ]; then
    echo -e "${RED}错误: dist/index.html不存在，请确认构建是否成功${NC}"
    exit 1
fi

# 创建健康检查文件
echo "ok" > ../dist/health.html

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