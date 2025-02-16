#!/bin/bash

# 设置工作目录
cd /volume1/docker/stock-app

# 拉取最新代码
git pull

# 重新构建并启动容器
docker-compose up -d --build web

# 清理未使用的镜像
docker image prune -f

# 输出日志
echo "Deployment completed at $(date)" >> /volume1/docker/stock-app/deploy.log 