#!/bin/bash

echo "群辉NAS股票交易系统部署脚本"
echo "=============================="

deploy() {
  echo "开始部署前端服务..."
  
  # 检查dist目录
  if [ ! -d "dist" ]; then
    echo "错误: 找不到dist目录。请先在本地构建项目。"
    exit 1
  fi
  
  # 检查nginx配置
  if [ ! -f "nginx.conf" ]; then
    echo "错误: 找不到nginx.conf文件。"
    exit 1
  fi
  
  # 创建健康检查文件
  echo "ok" > dist/health
  
  # 停止旧容器
  docker rm -f stock-frontend &> /dev/null
  
  # 启动新容器
  docker run -d \
    --name stock-frontend \
    --restart always \
    --network host \
    -v $(pwd)/dist:/usr/share/nginx/html \
    -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf \
    nginx:alpine
  
  if [ $? -eq 0 ]; then
    echo "部署成功！访问地址: http://$(hostname -I | awk '{print $1}')"
  else
    echo "部署失败，请检查错误。"
  fi
}

stop() {
  echo "停止前端服务..."
  docker rm -f stock-frontend
}

logs() {
  docker logs -f stock-frontend
}

case "$1" in
  deploy)
    deploy
    ;;
  stop)
    stop
    ;;
  logs)
    logs
    ;;
  *)
    echo "用法: $0 {deploy|stop|logs}"
    ;;
esac 