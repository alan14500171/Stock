# 股票交易系统前端线上部署指南

本文档提供了在生产环境中部署股票交易系统前端的详细步骤和最佳实践。

## 部署前准备

### 1. 系统要求

- Docker 20.10.x 或更高版本
- Docker Compose 2.x 或更高版本
- 至少 2GB 可用内存
- 至少 10GB 可用磁盘空间

### 2. 网络环境

- 确保服务器可以访问互联网（用于拉取Docker镜像）
- 确保前端服务器可以访问后端API服务器
- 如果使用防火墙，需要开放80端口（或您计划使用的其他端口）

### 3. 配置文件准备

在部署前，您需要修改以下配置文件中的相关参数：

1. **docker-compose.nginx.yml**
   - 修改 `VITE_API_BASE_URL` 为实际的后端API地址
   - 根据需要调整端口映射（默认为80:80）

2. **nginx.conf**
   - 修改 `proxy_pass` 指向实际的后端API地址
   - 根据需要调整缓存策略和超时设置

## 部署步骤

### 1. 克隆代码仓库

```bash
git clone <仓库地址> stock-frontend
cd stock-frontend
```

### 2. 修改配置

根据您的环境修改配置文件：

```bash
# 修改docker-compose.nginx.yml中的后端API地址
sed -i 's/后端实际IP地址/<您的后端IP>/g' docker-compose.nginx.yml

# 修改nginx.conf中的后端API地址
sed -i 's/后端实际IP地址/<您的后端IP>/g' nginx.conf
```

### 3. 构建并启动容器

```bash
# 使用docker-compose构建并启动
docker-compose -f docker-compose.nginx.yml up -d
```

### 4. 验证部署

```bash
# 检查容器是否正常运行
docker ps | grep stock-frontend-nginx

# 检查Nginx是否正常响应
curl http://localhost/health
```

## 更新部署

当需要更新前端应用时，请按照以下步骤操作：

```bash
# 拉取最新代码
git pull

# 重新构建并启动容器
docker-compose -f docker-compose.nginx.yml up -d --build
```

## 常见问题排查

### 1. 容器无法启动

检查Docker日志：

```bash
docker logs stock-frontend-nginx
```

### 2. 无法访问前端应用

检查Nginx配置和端口映射：

```bash
# 检查Nginx配置
docker exec -it stock-frontend-nginx nginx -t

# 检查端口是否被占用
netstat -tulpn | grep 80
```

### 3. 无法连接后端API

检查网络连接和API配置：

```bash
# 从容器内部测试API连接
docker exec -it stock-frontend-nginx curl -I http://后端IP:9099

# 检查nginx.conf中的代理配置
docker exec -it stock-frontend-nginx cat /etc/nginx/conf.d/default.conf
```

### 4. 性能优化

如果您的应用需要处理大量请求，可以考虑以下优化：

1. **增加Nginx工作进程**

   修改 `nginx.conf` 添加：
   ```
   worker_processes auto;
   worker_rlimit_nofile 65535;
   ```

2. **配置CDN**

   将静态资源部署到CDN，减轻服务器负载。

3. **启用HTTP/2**

   在 `nginx.conf` 中启用HTTP/2：
   ```
   listen 443 ssl http2;
   ```

## 安全最佳实践

1. **启用HTTPS**

   获取SSL证书并配置HTTPS：
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       # 其他SSL配置...
   }
   ```

2. **设置安全头**

   在 `nginx.conf` 中添加安全相关的HTTP头：
   ```nginx
   add_header X-Content-Type-Options nosniff;
   add_header X-XSS-Protection "1; mode=block";
   add_header X-Frame-Options SAMEORIGIN;
   add_header Content-Security-Policy "default-src 'self'";
   ```

3. **限制请求速率**

   防止DDoS攻击：
   ```nginx
   limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;
   
   location / {
       limit_req zone=mylimit burst=20 nodelay;
       # 其他配置...
   }
   ```

## 监控与日志

### 1. 配置日志轮转

防止日志文件过大：

```bash
# 创建logrotate配置
cat > /etc/logrotate.d/nginx-stock << EOF
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -s /run/nginx.pid ] && kill -USR1 \`cat /run/nginx.pid\`
    endscript
}
EOF
```

### 2. 设置监控

推荐使用Prometheus和Grafana监控Nginx状态：

1. 安装Nginx Prometheus Exporter
2. 配置Prometheus抓取指标
3. 在Grafana中创建仪表板

## 备份策略

定期备份Nginx配置和静态文件：

```bash
# 创建备份脚本
cat > /usr/local/bin/backup-nginx.sh << EOF
#!/bin/bash
BACKUP_DIR="/backup/nginx/\$(date +%Y%m%d)"
mkdir -p \$BACKUP_DIR
docker cp stock-frontend-nginx:/etc/nginx/conf.d \$BACKUP_DIR/
docker cp stock-frontend-nginx:/usr/share/nginx/html \$BACKUP_DIR/
tar -czf \$BACKUP_DIR.tar.gz \$BACKUP_DIR
rm -rf \$BACKUP_DIR
EOF

chmod +x /usr/local/bin/backup-nginx.sh

# 添加到crontab
echo "0 2 * * * /usr/local/bin/backup-nginx.sh" >> /etc/crontab
```

## 联系与支持

如果您在部署过程中遇到任何问题，请参考 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 文档或联系技术支持团队。 