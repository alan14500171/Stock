#!/bin/bash
cd /volume1/docker/stock-app

# 使用docker执行git pull
/usr/local/bin/docker run --rm \
  -v /volume1/docker/stock-app:/app \
  -w /app \
  alpine/git pull http://192.168.0.109:3000/alan/stock.git

# 重新构建和启动服务
/usr/local/bin/docker-compose up -d --build web
/usr/local/bin/docker image prune -f
echo "Deployment completed at $(date)" >> /volume1/docker/stock-app/deploy.log
