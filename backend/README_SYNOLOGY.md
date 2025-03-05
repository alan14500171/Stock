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

如果端口9099已被占用，可以修改`docker-compose.yml`文件中的端口映射：

```yaml
ports:
  - "9100:9099"  # 将主机的9100端口映射到容器的9099端口
```

### 权限问题

如果遇到权限问题，可以尝试：

```bash
# 设置目录权限
chmod -R 755 /volume1/docker/stock
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