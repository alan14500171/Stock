# 群辉NAS部署指南

## 概述

这个指南将帮助您在群辉NAS上部署股票交易系统前端。为了避免在NAS上出现的XSym符号链接和crypto.getRandomValues错误，我们采用"本地构建+NAS部署"的方式。

## 部署步骤

### 1. 本地构建前端

在您的开发机器上执行以下步骤：

```bash
# 克隆仓库（如果还没有）
git clone <仓库地址>
cd stock/frontend

# 安装依赖
npm install --legacy-peer-deps

# 设置后端API地址 - 替换为您的NAS内网IP和后端端口
echo "VITE_API_BASE_URL=http://192.168.0.109:9099" > .env.production

# 构建项目
npm run build
```

构建完成后，您会得到一个`dist`目录，包含所有编译好的静态文件。

### 2. 准备NAS上的部署目录

在群辉NAS上创建一个目录来存放前端文件：

```bash
# 例如在File Station中创建目录
/volume1/docker/stock-frontend/
```

### 3. 上传文件到NAS

将以下文件上传到NAS上的部署目录：

1. `dist/` 目录（包含所有构建好的前端文件）
2. `nginx.conf` 文件（NGINX配置文件）
3. `synology-deploy.sh` 脚本（部署脚本）

您可以使用File Station、SFTP或其他方式上传这些文件。

### 4. 部署服务

通过SSH连接到NAS，然后执行：

```bash
# 进入部署目录
cd /volume1/docker/stock-frontend

# 给部署脚本添加执行权限
chmod +x synology-deploy.sh

# 创建健康检查文件
echo "ok" > dist/health

# 部署服务
./synology-deploy.sh deploy
```

### 5. 管理服务

以下是管理服务的常用命令：

```bash
# 部署服务
./synology-deploy.sh deploy

# 停止服务
./synology-deploy.sh stop

# 查看日志
./synology-deploy.sh logs
```

## 故障排除

如果遇到问题，请检查：

1. 确保Docker已在NAS上安装
2. 确保dist目录和nginx.conf文件正确上传
3. 检查nginx.conf中的后端API代理地址是否正确
4. 查看容器日志了解详细错误信息
5. 确保防火墙未阻止相关端口

## 更新部署

当需要更新前端时，只需在本地重新构建，然后将新的dist目录上传到NAS，再运行：

```bash
./synology-deploy.sh deploy
```

这将使用新的静态文件重新部署服务。 