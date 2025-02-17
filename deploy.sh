#!/bin/bash
cd /volume1/docker/stock-app

# 使用docker容器执行git pull，并传入git凭证
sudo docker run --rm \
  -v /volume1/docker/stock-app:/app \
  -w /app \
  -e GIT_USERNAME=alan \
  -e GIT_PASSWORD=$GIT_PASSWORD \
  alpine/git pull http://alan:${GIT_PASSWORD}@192.168.0.109:3000/alan/stock.git

# 重新构建和启动服务
sudo /usr/local/bin/docker-compose up -d --build web
sudo /usr/local/bin/docker image prune -f
echo "Deployment completed at $(date)" >> /volume1/docker/stock-app/deploy.log
