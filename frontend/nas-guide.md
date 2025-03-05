# 群辉NAS部署指南 (简化版)

## 所需文件

部署到群辉NAS需要以下文件:

1. `dist/` 目录 - 包含构建好的前端文件
2. `nginx-synology.conf` - NGINX配置文件 
3. `docker-compose.simple.yml` - Docker Compose配置
4. `nas-deploy.sh` - 部署脚本

## 部署步骤

### 在您的本地机器上

1. **构建前端项目**:

   ```bash
   # 安装依赖
   npm install --legacy-peer-deps

   # 创建.env.production (替换为您的后端实际地址)
   echo "VITE_API_BASE_URL=http://192.168.1.100:9099" > .env.production

   # 构建项目
   npm run build
   ```

2. **准备部署文件**:

   将以下文件上传到您的群辉NAS (如: `/volume1/docker/stock-frontend/`):
   - `dist/` 目录
   - `nginx-synology.conf`
   - `docker-compose.simple.yml`
   - `nas-deploy.sh`

### 在群辉NAS上

1. **通过SSH连接到NAS**

2. **进入部署目录**:

   ```bash
   cd /volume1/docker/stock-frontend
   ```

3. **修改nginx配置中的后端地址**:

   ```bash
   # 编辑nginx-synology.conf文件
   # 将proxy_pass后面的地址改为您的后端服务地址
   ```

4. **执行部署脚本**:

   ```bash
   # 添加执行权限
   chmod +x nas-deploy.sh

   # 执行部署
   ./nas-deploy.sh
   ```

## 管理容器

```bash
# 查看容器状态
docker ps | grep stock-frontend

# 查看日志
docker logs -f stock-frontend

# 停止容器
docker-compose -f docker-compose.simple.yml down
```

## 排障指南

如果遇到问题:

1. 确保Docker已安装在NAS上
2. 确认所有文件都正确上传
3. 检查nginx配置中的后端地址是否正确
4. 查看容器日志了解详细错误信息 