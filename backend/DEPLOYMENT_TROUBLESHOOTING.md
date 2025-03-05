# 股票交易系统部署故障排除指南

本文档提供了在部署股票交易系统时可能遇到的常见问题及其解决方案。

## MySQL/MariaDB 客户端安装问题

### 问题: `mysql-client` 或 `default-libmysqlclient-dev` 安装失败

在某些 Debian 系统上，特别是在 Docker 容器中，可能会遇到以下错误：

```
Package mysql-client is not available, but is referred to by another package.
This may mean that the package is missing, has been obsoleted, or is only available from another source
E: Package 'mysql-client' has no installation candidate
```

### 解决方案

使用 MariaDB 客户端替代 MySQL 客户端：

1. 修改 `Dockerfile`，将：

```dockerfile
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    mysql-client \
    # 其他依赖...
```

替换为：

```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential \
    mariadb-client \
    libmariadb-dev \
    # 其他依赖...
```

2. 修改 `container_start.sh` 脚本，将所有 `mysql` 命令替换为 `mariadb` 命令。

## 数据库连接问题

### 问题: 无法连接到数据库

常见错误信息：

```
ERROR: 无法连接到数据库 172.16.0.109:3306
```

### 可能的原因和解决方案

1. **网络连接问题**
   - 确保数据库服务器可以从 Docker 容器访问
   - 检查防火墙设置，确保端口 3306 已开放
   - 使用 `ping` 和 `telnet` 测试连接

2. **数据库服务未运行**
   - 确保 MySQL/MariaDB 服务正在运行
   - 检查数据库服务器日志

3. **认证问题**
   - 确保用户名和密码正确
   - 检查用户是否有远程访问权限：
     ```sql
     CREATE USER 'username'@'%' IDENTIFIED BY 'password';
     GRANT ALL PRIVILEGES ON database_name.* TO 'username'@'%';
     FLUSH PRIVILEGES;
     ```

4. **数据库名称大小写问题**
   - MySQL 在某些操作系统上对数据库名称大小写敏感
   - 使用 `check_db_connection.py` 脚本检查实际数据库名称

## Docker 相关问题

### 问题: 容器无法启动

### 解决方案

1. 检查 Docker 日志：
   ```bash
   docker logs container_name
   ```

2. 确保所有必要的文件都存在，特别是配置文件：
   ```bash
   docker exec -it container_name ls -la /app/config
   ```

3. 尝试以交互模式启动容器进行调试：
   ```bash
   docker run -it --rm --entrypoint /bin/bash image_name
   ```

## 权限问题

### 问题: 无法写入日志文件或其他文件

### 解决方案

1. 确保容器内的目录具有适当的权限：
   ```bash
   docker exec -it container_name chmod -R 777 /app/logs
   ```

2. 确保卷映射正确：
   ```yaml
   volumes:
     - ./logs:/app/logs
   ```

## 使用诊断工具

系统提供了几个诊断工具来帮助排查问题：

1. **数据库连接检查脚本**：
   ```bash
   python scripts/check_db_connection.py --env production
   ```
   
   如果数据库不存在，可以尝试创建：
   ```bash
   python scripts/check_db_connection.py --env production --create
   ```

2. **容器启动脚本**：
   容器启动脚本 `container_start.sh` 包含详细的诊断信息，可以帮助识别问题。

## 联系支持

如果您在部署过程中遇到无法解决的问题，请联系技术支持团队，并提供以下信息：

1. 详细的错误信息和日志
2. 系统环境信息（操作系统、Docker 版本等）
3. 已尝试的解决方案 