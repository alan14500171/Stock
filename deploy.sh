#!/bin/bash
cd /volume1/docker/stock-app

# 重新构建和启动服务
sudo /usr/local/bin/docker-compose up -d --build web

# 清理未使用的镜像
sudo /usr/local/bin/docker image prune -f

# 记录部署时间
echo "Deployment completed at $(date)" >> /volume1/docker/stock-app/deploy.log
