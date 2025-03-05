# 股票交易系统后端 - Synology NAS 部署指南

本文档提供在 Synology NAS 上使用 Docker 部署股票交易系统后端的详细步骤。

## 前提条件

1. Synology NAS 已安装 Docker 套件
2. MySQL/MariaDB 数据库已安装并运行
3. 已创建名为 `stock` 的数据库（注意大小写）
4. 已创建具有适当权限的数据库用户

## 部署步骤

### 1. 准备工作

1. 将后端代码上传到 Synology NAS 的共享文件夹中
2. 通过 SSH 连接到 Synology NAS
3. 导航到后端代码所在目录

### 2. 配置数据库连接

1. 编辑 `config/db_config.py` 文件，修改数据库连接信息：

```python
'production': {
    'host': '你的数据库IP地址',  # 例如：'172.16.0.109'
    'port': 3306,
    'user': '你的数据库用户名',  # 例如：'root'
    'password': '你的数据库密码',  # 例如：'Zxc000123'
    'db': 'stock',  # 确保与实际数据库名称大小写一致
    'charset': 'utf8mb4'
}
```

### 3. 构建 Docker 镜像

```bash
docker build -t stock-backend:latest .
```

如果在构建过程中遇到 MySQL 客户端安装问题，请参考 [部署故障排除指南](DEPLOYMENT_TROUBLESHOOTING.md) 中的解决方案。

### 4. 启动服务

使用提供的启动脚本：

```bash
chmod +x start.sh
./start.sh
```

或者直接使用 Docker Compose：

```bash
docker-compose up -d
```

### 5. 验证部署

1. 检查容器是否正常运行：

```bash
docker ps | grep stock-backend
```

2. 查看日志：

```bash
docker logs stock-backend
```

3. 测试API接口：

```bash
curl http://localhost:9099/api/v1/health
```

## 常见问题排查

### 数据库连接问题

如果遇到数据库连接问题，可以使用提供的诊断脚本进行检查：

```bash
chmod +x scripts/check_db_connection.py
python3 scripts/check_db_connection.py
```

更详细的故障排除步骤，请参考 [部署故障排除指南](DEPLOYMENT_TROUBLESHOOTING.md)。

#### 常见数据库问题及解决方案：

1. **数据库名称大小写问题**

   MySQL在某些操作系统上对数据库名称大小写敏感。确保配置文件中的数据库名称与实际创建的数据库名称大小写一致。

   ```bash
   # 在MySQL中查看实际数据库名称
   mysql -u root -p -e "SHOW DATABASES;"
   ```

2. **用户权限问题**

   确保数据库用户具有足够的权限：

   ```sql
   -- 在MySQL中授予权限
   GRANT ALL PRIVILEGES ON stock.* TO '用户名'@'%';
   FLUSH PRIVILEGES;
   ```

3. **网络连接问题**

   确保Docker容器可以访问数据库服务器：

   ```bash
   # 从容器内部测试连接
   docker exec -it stock-backend ping 数据库IP地址
   docker exec -it stock-backend mariadb -h 数据库IP地址 -u 用户名 -p
   ```

4. **数据库服务未运行**

   确保MySQL/MariaDB服务正在运行：

   ```bash
   # 在Synology DSM中检查
   synoservice --status mysql
   ```

### 容器启动问题

如果容器无法正常启动：

1. 检查启动日志：

```bash
docker logs stock-backend
```

2. 检查容器状态：

```bash
docker inspect stock-backend
```

3. 尝试以交互模式启动容器进行调试：

```bash
docker run -it --rm --entrypoint /bin/bash stock-backend:latest
```

## 操作命令

### 查看日志

```bash
docker logs -f stock-backend
```

### 重启服务

```bash
docker-compose restart
```

### 停止服务

```bash
docker-compose down
```

### 更新部署

当有新的后端代码上传时：

1. 停止现有服务：

```bash
docker-compose down
```

2. 重新构建镜像：

```bash
docker build -t stock-backend:latest .
```

3. 启动服务：

```bash
docker-compose up -d
```

## 高级配置

### 自定义端口

如需修改默认端口（9099），编辑 `docker-compose.yml` 文件：

```yaml
ports:
  - "自定义端口:9099"
```

### 持久化数据

如需持久化数据，确保在 `docker-compose.yml` 中配置了适当的卷映射。

## 故障排除

如果在部署过程中遇到问题，请参考 [部署故障排除指南](DEPLOYMENT_TROUBLESHOOTING.md) 获取更详细的解决方案。 