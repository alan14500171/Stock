# 股票交易系统前端 - Synology NAS 部署指南

本文档提供在 Synology NAS 上使用 Docker 部署股票交易系统前端的详细步骤。

## 前提条件

1. Synology NAS 已安装 Docker 套件
2. 后端服务已部署并可访问
3. 基本的 Docker 和 Linux 命令知识

## 部署步骤

### 1. 准备工作

1. 将前端代码上传到 Synology NAS 的共享文件夹中
2. 通过 SSH 连接到 Synology NAS
3. 导航到前端代码所在目录

### 2. 配置环境变量

1. 编辑 `.env.production` 文件，设置后端 API 地址：

```
VITE_API_BASE_URL=http://你的后端IP地址:9099
VITE_APP_TITLE=股票交易系统
```

如果文件不存在，启动脚本会自动创建一个默认的配置文件。

### 3. 选择部署模式

系统支持两种部署模式：

1. **Nginx 模式**（推荐用于生产环境）
   - 使用 Nginx 作为 Web 服务器
   - 更好的性能和安全性
   - 默认使用 80 端口

2. **Node.js 模式**
   - 使用 Node.js 的 `serve` 工具提供服务
   - 适合开发和测试
   - 默认使用 9009 端口

### 4. 部署服务

使用提供的启动脚本：

```bash
# 设置脚本可执行权限
chmod +x start.sh

# Nginx 模式部署（推荐）
./start.sh start nginx

# 或者 Node.js 模式部署
./start.sh start node
```

如果在构建过程中遇到问题，请参考 [部署故障排除指南](TROUBLESHOOTING.md)。

### 5. 验证部署

1. 检查容器是否正常运行：

```bash
docker ps | grep stock-frontend
```

2. 在浏览器中访问：
   - Nginx 模式：`http://你的NAS地址`
   - Node.js 模式：`http://你的NAS地址:9009`

## 常见问题排查

### 构建失败

如果在构建过程中遇到 "XSym: not found" 或其他错误，请参考 [部署故障排除指南](TROUBLESHOOTING.md) 中的解决方案。

### 端口冲突

如果遇到端口冲突问题：

1. 修改 `docker-compose.nginx.yml` 或 `docker-compose.yml` 中的端口映射
2. 例如，将 `80:80` 改为 `8080:80`

### 无法连接到后端

1. 确保 `.env.production` 中的 API 地址正确
2. 检查后端服务是否正常运行
3. 验证网络连接是否正常

更多详细的故障排除步骤，请参考 [部署故障排除指南](TROUBLESHOOTING.md)。

## 操作命令

### 查看日志

```bash
./start.sh logs nginx  # Nginx 模式
./start.sh logs node   # Node.js 模式
```

### 重启服务

```bash
./start.sh restart nginx  # Nginx 模式
./start.sh restart node   # Node.js 模式
```

### 停止服务

```bash
./start.sh stop nginx  # Nginx 模式
./start.sh stop node   # Node.js 模式
```

### 清理资源

```bash
./start.sh clean nginx  # Nginx 模式
./start.sh clean node   # Node.js 模式
```

## 更新部署

当有新的前端代码上传时：

1. 停止现有服务：

```bash
./start.sh stop nginx  # 或 node
```

2. 清理资源：

```bash
./start.sh clean nginx  # 或 node
```

3. 重新启动服务：

```bash
./start.sh start nginx  # 或 node
```

## 高级配置

### 自定义 Nginx 配置

如需修改 Nginx 配置，编辑 `nginx.conf` 文件，然后重新构建和部署。

### 自定义端口

如需修改默认端口：

1. 编辑 `docker-compose.nginx.yml` 或 `docker-compose.yml` 文件
2. 修改 `ports` 部分的端口映射

## 故障排除

如果在部署过程中遇到问题，请参考 [部署故障排除指南](TROUBLESHOOTING.md) 获取详细的解决方案。 