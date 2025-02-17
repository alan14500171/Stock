#!/bin/bash

# 创建必要的目录
mkdir -p /volume1/docker/stock-app
mkdir -p /volume1/docker/gogs/data

# 复制项目文件到指定目录
cp -r ./* /volume1/docker/stock-app/

# 启动 Gogs 服务
docker-compose -f gogs-compose.yml up -d

# 启动应用服务
cd /volume1/docker/stock-app
docker-compose up -d --build

echo "部署完成！"
echo "Gogs 服务地址: http://192.168.0.109:3000"
echo "应用服务地址: http://192.168.0.109:9009"
