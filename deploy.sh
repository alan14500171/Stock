#!/bin/bash
cd /volume1/docker/stock-app

# 使用docker容器执行git pull
sudo docker run --rm -v /volume1/docker/stock-app:/app -w /app alpine/git pull

# 重新构建和启动服务
sudo /usr/local/bin/docker-compose up -d --build web
sudo /usr/local/bin/docker image prune -f
echo "Deployment completed at $(date)" >> /volume1/docker/stock-app/deploy.log
