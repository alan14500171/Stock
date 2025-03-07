# 股票交易系统部署指南

本文档提供了在线上环境中部署股票交易系统的详细步骤。

## 前提条件

- Python 3.12
- Node.js 18+
- MySQL 数据库
- Git

## 部署步骤

### 1. 获取最新代码

```bash
# 进入项目目录
cd /path/to/project

# 拉取最新代码
git pull origin main
```

### 2. 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（如果尚未创建）
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 重置管理员密码（可选，如果遇到登录问题）
python scripts/reset_admin_password.py

# 启动后端服务
# 如果使用 systemd 管理服务，重启服务
sudo systemctl restart stock-backend.service

# 如果手动启动，可以使用以下命令
# nohup python main.py > backend.log 2>&1 &
```

### 3. 前端部署

```bash
# 进入前端目录
cd ../frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 将构建好的文件复制到 Web 服务器目录
cp -r dist/* /var/www/html/
```

### 4. 验证部署

1. 访问前端页面（例如：http://your-domain.com）
2. 使用管理员账号登录（用户名：alan 或 admin，密码：123123）
3. 验证系统功能是否正常

### 5. 常见问题排查

#### 登录问题

如果遇到登录问题，可能是密码哈希格式不兼容导致的。请执行以下步骤：

1. 运行密码重置脚本：
   ```bash
   cd backend
   source venv/bin/activate
   python scripts/reset_admin_password.py
   ```

2. 检查日志文件中是否有错误信息：
   ```bash
   tail -f backend.log
   ```

#### 数据库连接问题

确保数据库配置正确：

1. 检查 `backend/config/db_config.py` 文件中的数据库配置
2. 确保数据库服务器正在运行
3. 验证数据库用户有足够的权限

#### 前端资源加载问题

如果前端页面无法正确加载资源：

1. 检查浏览器控制台是否有错误
2. 确保 Web 服务器配置正确
3. 验证静态资源路径是否正确

## 安全建议

1. 部署完成后，立即修改默认管理员密码
2. 配置 HTTPS 以加密传输数据
3. 定期备份数据库
4. 限制服务器访问权限

## 联系支持

如果您在部署过程中遇到任何问题，请联系技术支持团队。 