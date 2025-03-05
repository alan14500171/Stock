# 在群辉NAS上部署股票交易系统

本文档提供了在群辉NAS的Docker环境中部署股票交易系统的详细步骤。

## 前提条件

- 群辉NAS已安装Docker套件
- 已启用SSH访问
- 基本的Linux命令行知识

## 部署步骤

### 1. 准备工作

1. 登录群辉DSM界面
2. 确保已安装并启用Docker套件
3. 启用SSH服务（控制面板 -> 终端机和SNMP -> 启用SSH服务）

### 2. 通过SSH连接到NAS

```bash
ssh admin@your-nas-ip
```

将`admin`替换为您的管理员用户名，`your-nas-ip`替换为NAS的IP地址。

### 3. 创建部署目录

```bash
# 创建应用目录
mkdir -p /volume1/docker/stock
cd /volume1/docker/stock

# 创建后端目录
mkdir -p backend
cd backend
```

### 4. 上传文件到NAS

您可以使用SCP、SFTP或File Station将以下文件上传到`/volume1/docker/stock/backend`目录：

- `Dockerfile`
- `docker-compose.yml`
- `start.sh`
- `requirements.txt`
- 应用代码文件

或者，您可以直接在NAS上使用Git克隆仓库：

```bash
git clone https://your-repository-url.git /volume1/docker/stock
cd /volume1/docker/stock/backend
```

### 5. 配置数据库连接

1. 确保`config`目录中有`db_config.py`文件
2. 编辑`db_config.py`文件，配置正确的数据库连接信息：

```bash
# 如果使用vi编辑器
vi config/db_config.py
```

修改数据库配置，确保与`docker-compose.yml`中的设置一致：

```python
def get_db_config(env: str = 'production') -> dict:
    """获取数据库配置"""
    configs = {
        'production': {
            'host': 'stock-db',  # 使用Docker服务名称
            'port': 3306,
            'user': 'stockuser',
            'password': 'your_password',  # 与docker-compose.yml中设置一致
            'db': 'stock',
            'charset': 'utf8mb4'
        }
    }
    return configs.get(env, configs['production'])
```

### 6. 设置权限并启动服务

```bash
# 设置启动脚本可执行权限
chmod +x start.sh

# 启动服务
./start.sh start
```

### 7. 验证部署

1. 检查容器是否正常运行：

```bash
docker ps
```

2. 查看应用日志：

```bash
./start.sh logs
```

3. 在浏览器中访问应用：

```
http://your-nas-ip:9099
```

## 常用操作

### 重启服务

```bash
./start.sh restart
```

### 停止服务

```bash
./start.sh stop
```

### 查看日志

```bash
./start.sh logs
```

### 重置管理员密码

```bash
./start.sh reset-pwd
```

### 清理Docker资源

如果遇到部署问题，可以尝试清理Docker资源后重新部署：

```bash
./start.sh clean
./start.sh start
```

### 系统诊断

如果遇到问题，可以运行诊断命令获取系统信息：

```bash
./start.sh diagnose
```

## 使用群辉Docker GUI管理

除了命令行，您还可以使用群辉的Docker GUI界面管理容器：

1. 登录DSM界面
2. 打开Docker应用
3. 在"容器"标签页中可以看到运行中的`stock-backend`和`stock-db`容器
4. 您可以通过界面启动、停止、重启容器，或查看日志

## 故障排除

### 数据库连接问题

如果应用无法连接到数据库，请检查：

1. `docker-compose.yml`中的数据库配置
2. `config/db_config.py`中的连接信息
3. 确保两者的用户名、密码、数据库名称一致

### 端口冲突

如果端口9099或13306已被占用，可以修改`docker-compose.yml`文件中的端口映射：

```yaml
# 后端服务端口
ports:
  - "9100:9099"  # 将主机的9100端口映射到容器的9099端口

# 数据库端口
ports:
  - "13307:3306"  # 将主机的13307端口映射到容器的3306端口
```

### 网络问题

如果遇到网络相关错误（如"Error response from daemon: driver failed programming external connectivity"），请尝试以下解决方案：

1. 清理Docker资源：

```bash
./start.sh clean
```

2. 重启Docker服务：

```bash
# 在群辉DSM界面中重启Docker套件
# 或者通过SSH执行
sudo synoservice --restart pkgctl-Docker
```

3. 检查防火墙设置，确保端口9099和13306未被阻止

4. 如果问题仍然存在，尝试使用默认网络：

```yaml
# 修改docker-compose.yml，删除networks部分，使用默认网络
services:
  stock-backend:
    # ... 其他配置 ...
    # 删除networks配置
  
  stock-db:
    # ... 其他配置 ...
    # 删除networks配置

# 删除networks部分
```

### 权限问题

如果遇到权限问题，可以尝试：

```bash
# 设置目录权限
chmod -R 755 /volume1/docker/stock
```

### 构建失败

如果Docker镜像构建失败，请检查：

1. `requirements.txt`文件是否有语法错误
2. 确保所有依赖包名称正确
3. 查看构建日志获取详细错误信息：

```bash
docker-compose build --no-cache
```

### 容器启动失败

如果容器无法正常启动，请检查日志：

```bash
docker logs stock-backend
docker logs stock-db
```

## 备份与恢复

### 备份数据库

```bash
# 创建备份目录
mkdir -p /volume1/backup/stock

# 备份数据库
docker exec stock-db sh -c 'exec mysqldump -uroot -p"your_root_password" stock' > /volume1/backup/stock/stock_db_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
# 恢复数据库
cat /volume1/backup/stock/stock_db_20240305.sql | docker exec -i stock-db sh -c 'exec mysql -uroot -p"your_root_password" stock'
```

## 更新应用

1. 停止服务：

```bash
./start.sh stop
```

2. 拉取最新代码（如果使用Git）：

```bash
git pull
```

3. 重新构建并启动服务：

```bash
./start.sh start
```

## 群辉NAS特有问题

### Docker套件版本兼容性

群辉NAS的Docker套件可能与最新的Docker版本有所不同。如果遇到兼容性问题，可以尝试：

1. 在`docker-compose.yml`中指定较低版本的镜像：

```yaml
stock-db:
  image: mysql:5.7  # 使用较低版本的MySQL
```

2. 更新Docker套件到最新版本（通过套件中心）

### 资源限制

群辉NAS可能有资源限制，特别是入门级型号。如果应用运行缓慢或崩溃，可以：

1. 在`docker-compose.yml`中添加资源限制：

```yaml
stock-backend:
  # ... 其他配置 ...
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

2. 减少MySQL内存使用：

```yaml
stock-db:
  # ... 其他配置 ...
  command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci --innodb_buffer_pool_size=128M
```

## 在Synology NAS上部署股票交易系统

本指南将帮助您在Synology NAS上使用Docker部署股票交易系统。

### 前提条件

1. Synology NAS已安装Docker套件
2. 已有MySQL/MariaDB数据库（可以是NAS上的或外部的）
3. 基本的Linux命令行知识

### 部署步骤

#### 1. 准备工作

1. 在Synology NAS上创建一个文件夹用于存放项目文件，例如 `/volume1/docker/stock`
2. 将项目文件上传到该文件夹

#### 2. 配置数据库连接

1. 复制配置文件模板：
   ```bash
   cp config/db_config.example.py config/db_config.py
   ```

2. 编辑 `config/db_config.py` 文件，配置数据库连接信息：
   ```python
   def get_db_config(env: str = 'production') -> Dict[str, Any]:
       """获取数据库配置"""
       configs = {
           'production': {
               'host': '192.168.1.100',  # 替换为您的数据库IP地址
               'port': 3306,             # 替换为您的数据库端口
               'user': 'stockuser',      # 替换为您的数据库用户名
               'password': 'password',   # 替换为您的数据库密码
               'db': 'stock',            # 替换为您的数据库名称
               'charset': 'utf8mb4'
           }
       }
       return configs.get(env, configs['production'])
   ```

#### 3. 构建和启动服务

1. 进入项目目录：
   ```bash
   cd /volume1/docker/stock/backend
   ```

2. 构建Docker镜像：
   ```bash
   docker-compose build
   ```

3. 启动服务：
   ```bash
   docker-compose up -d
   ```

### 使用外部数据库

本项目已配置为可以连接到外部已存在的数据库，而不是部署新的数据库容器。请按照以下步骤操作：

1. 确保您的外部数据库已创建名为 `stock` 的数据库（或您在配置中指定的数据库名）
2. 确保数据库用户具有足够的权限（SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER）
3. 确保NAS可以访问外部数据库（检查网络连接和防火墙设置）
4. 在 `config/db_config.py` 中正确配置数据库连接信息

如果您的数据库是全新的，系统将自动创建必要的表结构。如果您使用的是已有数据，请确保表结构与系统要求兼容。

### 故障排除

#### 数据库连接问题

如果遇到数据库连接问题，请检查：

1. 数据库服务器是否运行
2. 数据库连接信息是否正确
3. 数据库用户是否有足够权限
4. 网络连接是否正常

您可以通过查看容器日志来诊断问题：
```bash
docker logs stock-backend
```

#### 端口冲突

如果遇到端口冲突，可以在 `docker-compose.yml` 中修改端口映射：
```yaml
ports:
  - "9099:9099"  # 将左侧的端口改为其他未使用的端口
```

#### 网络问题

如果后端服务无法连接到数据库，请检查网络配置：

1. 确保Docker网络设置正确
2. 检查NAS的防火墙设置
3. 如果使用外部数据库，确保数据库服务器允许从NAS的IP地址连接

### 常用操作

#### 查看日志
```bash
docker logs stock-backend
```

#### 重启服务
```bash
docker-compose restart
```

#### 停止服务
```bash
docker-compose down
```

#### 更新服务
```bash
git pull
docker-compose build
docker-compose up -d
```

### 系统诊断

如果系统不能正常工作，可以运行以下命令进行诊断：

```bash
# 检查容器状态
docker ps -a | grep stock-backend

# 检查容器日志
docker logs stock-backend

# 检查网络连接
docker exec stock-backend ping -c 3 <数据库IP>

# 检查数据库连接
docker exec stock-backend mysqladmin ping -h <数据库IP> -P <端口> -u <用户名> -p<密码>
``` 