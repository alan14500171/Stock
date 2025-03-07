# 股票交易系统后端

## 项目简介

股票交易系统后端服务，提供股票数据查询、交易模拟等功能。

## 技术栈

- Python 3.9+
- Flask
- SQLAlchemy
- MySQL/MariaDB
- Docker

## 本地开发环境设置

### 前提条件

- Python 3.9+
- MySQL/MariaDB
- pip

### 安装步骤

1. 克隆仓库

```bash
git clone <repository-url>
cd stock/backend
```

2. 创建并激活虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置数据库

复制配置文件模板并编辑：

```bash
cp config/db_config.example.py config/db_config.py
# 编辑 db_config.py 文件，配置数据库连接信息
```

5. 初始化数据库

```bash
python scripts/create_database.py
```

6. 启动服务

```bash
python app.py
```

服务将在 http://localhost:9099 上运行。

## Docker 部署

### 使用 Docker Compose

1. 配置数据库连接

编辑 `config/db_config.py` 文件，确保生产环境配置正确。

2. 构建并启动服务

```bash
docker-compose up -d
```

如果在构建过程中遇到问题，请参考 [部署故障排除指南](DEPLOYMENT_TROUBLESHOOTING.md)。

### 使用启动脚本

提供了便捷的启动脚本，可以执行各种操作：

```bash
# 设置脚本可执行权限
chmod +x start.sh

# 启动服务
./start.sh start

# 查看日志
./start.sh logs

# 重启服务
./start.sh restart

# 停止服务
./start.sh stop

# 清理资源
./start.sh clean
```

## 数据库连接问题排查

如果遇到数据库连接问题，可以使用以下方法进行排查：

### 1. 使用诊断脚本

项目提供了专门的数据库连接诊断脚本：

```bash
chmod +x scripts/check_db_connection.py
python scripts/check_db_connection.py
```

该脚本会检查：
- 数据库主机连通性
- 数据库服务可访问性
- 数据库名称（包括大小写问题）
- 用户权限

更详细的故障排除步骤，请参考 [部署故障排除指南](DEPLOYMENT_TROUBLESHOOTING.md)。

### 2. 常见数据库问题及解决方案

#### 数据库名称大小写问题

MySQL在某些操作系统上对数据库名称大小写敏感。确保配置文件中的数据库名称与实际创建的数据库名称大小写一致。

```bash
# 在MySQL中查看实际数据库名称
mysql -u root -p -e "SHOW DATABASES;"
```

#### 用户权限问题

确保数据库用户具有足够的权限：

```sql
-- 在MySQL中授予权限
GRANT ALL PRIVILEGES ON stock.* TO '用户名'@'%';
FLUSH PRIVILEGES;
```

#### 网络连接问题

确保应用可以访问数据库服务器：

```bash
# 测试网络连接
ping 数据库IP地址

# 测试数据库连接
mysql -h 数据库IP地址 -u 用户名 -p
```

#### 数据库配置问题

检查 `config/db_config.py` 文件中的配置是否正确：

```python
'production': {
    'host': '数据库IP地址',  # 不要使用 'localhost' 或 '127.0.0.1'（在Docker中）
    'port': 3306,
    'user': '数据库用户名',
    'password': '数据库密码',
    'db': 'stock',  # 确保与实际数据库名称大小写一致
    'charset': 'utf8mb4'
}
```

### 3. 容器内部测试

如果使用Docker部署，可以进入容器内部进行测试：

```bash
# 进入容器
docker exec -it stock-backend bash

# 测试数据库连接
python -c "from config.db_config import get_db_config; import pymysql; config = get_db_config('production'); print(f'尝试连接到: {config}'); conn = pymysql.connect(**config); print('连接成功'); conn.close()"
```

## API 文档

API文档可通过以下地址访问：

```
http://localhost:9099/api/docs
```

## 群辉NAS部署

如需在群辉NAS上部署，请参考 [群辉NAS部署指南](README_SYNOLOGY.md)。

## 故障排除

如果在部署或使用过程中遇到问题，请参考 [部署故障排除指南](DEPLOYMENT_TROUBLESHOOTING.md) 获取详细的解决方案。

## 许可证

[MIT](LICENSE) 