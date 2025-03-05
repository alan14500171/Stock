# 群辉NAS部署指南

本指南将帮助您在群辉NAS上部署股票交易系统的前端应用。

## 系统要求

- 群辉NAS DSM 6.2或更高版本
- Docker套件已安装（在套件中心安装）
- Docker Compose已安装（通常随Docker套件一起安装）
- 至少2GB可用内存
- 至少1GB可用存储空间

## 准备工作

1. **启用SSH访问**
   - 在DSM控制面板中，转到"终端机和SNMP"
   - 启用SSH服务
   - 记下您的NAS的IP地址

2. **安装Docker套件**
   - 在DSM套件中心搜索并安装Docker

3. **创建部署目录**
   - 通过File Station或SSH创建一个目录用于存放项目文件
   - 建议路径：`/volume1/docker/stock-frontend`

## 部署步骤

### 1. 上传项目文件

将以下文件上传到您在NAS上创建的部署目录：
- `Dockerfile.nginx`
- `docker-compose.nginx.yml`
- `nginx.conf`
- `start.sh`
- 前端项目源代码

您可以使用以下方法上传文件：
- 通过File Station拖放文件
- 使用SCP命令：`scp -r ./frontend user@nas-ip:/volume1/docker/stock-frontend`

### 2. 连接到NAS

通过SSH连接到您的NAS：

```bash
ssh user@nas-ip
```

### 3. 进入项目目录

```bash
cd /volume1/docker/stock-frontend
```

### 4. 修改配置文件

1. **编辑docker-compose.nginx.yml**

   确保以下配置正确：
   - 将`VITE_API_BASE_URL`环境变量设置为您的后端API地址
   - 检查端口映射是否与您的环境冲突

   ```bash
   vi docker-compose.nginx.yml
   ```

2. **确保start.sh具有执行权限**

   ```bash
   chmod +x start.sh
   ```

### 5. 启动应用

```bash
./start.sh up
```

或者使用Docker Compose命令：

```bash
docker-compose -f docker-compose.nginx.yml up -d
```

### 6. 验证部署

在浏览器中访问：`http://nas-ip:8080`

## 常见问题解决

### 符号链接问题 (XSym错误)

如果您在构建过程中遇到与符号链接相关的错误，请参考[故障排除指南](TROUBLESHOOTING.md)中的"群辉NAS Docker部署特定问题"部分。

### 权限问题

如果遇到权限问题，可能需要以root用户身份运行命令：

```bash
sudo ./start.sh up
```

### 网络问题

如果前端无法连接到后端API，请检查：
1. 后端服务是否正在运行
2. `VITE_API_BASE_URL`环境变量是否设置正确
3. NAS防火墙是否允许相关端口的流量

## 更新应用

要更新应用，请执行以下步骤：

1. 停止当前运行的容器：
   ```bash
   ./start.sh down
   ```

2. 拉取最新的代码或替换更新的文件

3. 重新构建并启动容器：
   ```bash
   ./start.sh rebuild
   ```

## 备份配置

建议定期备份以下文件：
- `docker-compose.nginx.yml`
- `nginx.conf`
- 任何自定义配置文件

您可以使用群辉的Hyper Backup套件创建定期备份任务。

## 性能优化

- 如果NAS资源有限，可以在`docker-compose.nginx.yml`中添加资源限制：
  ```yaml
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
  ```

- 对于高负载环境，可以增加Nginx的worker进程数量，在`nginx.conf`中修改：
  ```
  worker_processes 4;
  ```

## 安全建议

1. 不要使用root用户运行Docker容器
2. 定期更新DSM和Docker套件
3. 考虑使用HTTPS而非HTTP
4. 限制对NAS的SSH访问

## 更多资源

- [群辉Docker文档](https://www.synology.com/en-global/knowledgebase/DSM/tutorial/Application/How_to_run_Docker_on_SynologyNAS)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [项目故障排除指南](TROUBLESHOOTING.md) 