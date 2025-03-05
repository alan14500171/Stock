# 在群晖NAS上部署股票交易系统前端

本指南将帮助您在群晖NAS上使用Docker部署股票交易系统的前端部分。

## 前提条件

1. 群晖NAS已安装Docker套件
2. 后端服务已部署并可访问
3. 基本的Linux命令行知识

## 部署步骤

### 1. 准备工作

1. 在群晖NAS上创建一个文件夹用于存放项目文件，例如 `/volume1/docker/stock/frontend`
2. 将前端项目文件上传到该文件夹

### 2. 配置环境变量

1. 编辑 `.env.production` 文件，配置后端API地址：
   ```
   VITE_API_BASE_URL=http://192.168.1.100:9099
   ```
   请将IP地址替换为您的实际后端服务地址。

### 3. 选择部署模式

您可以选择以下两种部署模式之一：

#### 方式一：使用Nginx部署（推荐用于生产环境）

1. 确保 `nginx.conf` 文件已正确配置
2. 使用以下命令启动服务：
   ```bash
   chmod +x start.sh
   ./start.sh start nginx
   ```

#### 方式二：使用Node.js部署

1. 使用以下命令启动服务：
   ```bash
   chmod +x start.sh
   ./start.sh start
   ```

### 4. 验证部署

1. 如果使用Nginx模式，访问 `http://您的NAS地址:80`
2. 如果使用Node.js模式，访问 `http://您的NAS地址:9009`
3. 使用有效的用户名和密码登录系统

## 常见问题排查

### 端口冲突

如果遇到端口冲突，可以修改 `docker-compose.nginx.yml` 或 `docker-compose.yml` 文件中的端口映射：

```yaml
ports:
  - "8080:80"  # 将左侧的端口改为其他未使用的端口
```

### 无法连接到后端

1. 确保后端服务正在运行
2. 检查 `.env.production` 文件中的API地址是否正确
3. 确保NAS和后端服务器之间的网络连接正常
4. 检查防火墙设置，确保端口已开放

### Nginx配置问题

如果使用Nginx模式遇到问题：

1. 检查 `nginx.conf` 文件中的配置是否正确
2. 确保代理地址指向正确的后端服务
3. 查看Nginx日志以获取更多信息：
   ```bash
   ./start.sh logs nginx
   ```

## 常用操作

### 查看日志
```bash
# Nginx模式
./start.sh logs nginx

# Node.js模式
./start.sh logs
```

### 重启服务
```bash
# 先停止
./start.sh stop nginx  # 或 ./start.sh stop

# 再启动
./start.sh start nginx  # 或 ./start.sh start
```

### 停止服务
```bash
# Nginx模式
./start.sh stop nginx

# Node.js模式
./start.sh stop
```

### 清理资源
```bash
./start.sh clean
```

## 更新部署

当需要更新前端代码时，请按照以下步骤操作：

1. 上传新的代码到NAS
2. 停止当前服务：
   ```bash
   ./start.sh stop nginx  # 或 ./start.sh stop
   ```
3. 清理资源：
   ```bash
   ./start.sh clean
   ```
4. 重新启动服务：
   ```bash
   ./start.sh start nginx  # 或 ./start.sh start
   ```

## 注意事项

1. 在生产环境中，建议使用Nginx模式部署，它提供更好的性能和安全性
2. 定期备份您的配置文件
3. 保持Docker镜像更新以获取最新的安全补丁 