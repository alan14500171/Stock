#!/bin/bash

# 记录开始时间
echo "Deployment started at $(date)" >> /app/deploy.log

# 拉取最新代码
cd /app
git pull origin main >> /app/deploy.log 2>&1

# 停止并删除旧容器
sudo /usr/local/bin/docker stop stock-app || true
sudo /usr/local/bin/docker rm stock-app || true

# 启动新容器
sudo /usr/local/bin/docker run -d --name stock-app \
  -v /volume1/docker/stock-app:/app \
  -p 3000:3000 \
  -w /app \
  python:3.10 \
  bash -c "pip install -r requirements.txt && python3 main.py"

# 记录完成时间和容器ID
echo "Deployment completed at $(date)" >> /app/deploy.log
echo "Container ID: $(sudo /usr/local/bin/docker ps -q -f name=stock-app)" >> /app/deploy.log
echo "----------------------------------------" >> /app/deploy.log

# 输出日志
echo "Stock app restarted at $(date)" >> /app/restart.log 