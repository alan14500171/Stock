#!/bin/bash
cd /volume1/docker/stock-app

# 重新构建和启动服务
/usr/local/bin/docker-compose up -d --build web
/usr/local/bin/docker image prune -f
echo "Deployment completed at $(date)" >> /volume1/docker/stock-app/deploy.log
