#!/bin/bash

echo "群辉NAS股票交易系统简易部署脚本"
echo "=============================="

# 创建健康检查文件
echo "创建健康检查文件..."
mkdir -p dist
echo "ok" > dist/health

# 检查nginx配置文件
if [ ! -f "nginx-synology.conf" ]; then
  echo "错误: 找不到nginx-synology.conf文件！"
  exit 1
fi

# 复制nginx配置文件
echo "复制nginx配置文件..."
cp nginx-synology.conf nginx.conf

# 停止旧容器
echo "停止旧容器..."
docker rm -f stock-frontend &> /dev/null

# 启动容器
echo "启动容器..."
docker-compose -f docker-compose.simple.yml up -d

# 检查结果
if [ $? -eq 0 ]; then
  echo "部署成功！"
  echo "访问地址: http://$(hostname -I | awk '{print $1}')"
  echo "查看日志: docker logs -f stock-frontend"
else
  echo "部署失败，请检查错误信息。"
fi 