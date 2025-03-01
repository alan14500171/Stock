# 股票交易管理系统

一个基于 Python Flask 和 Vue.js 的股票交易管理系统。

## 项目结构

```
.
├── frontend/                # 前端项目目录
│   ├── src/                # 源代码
│   │   ├── components/     # 通用组件
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   ├── composables/   # 组合式函数
│   │   └── main.js        # 入口文件
│   ├── public/            # 静态资源
│   ├── index.html         # HTML 模板
│   └── package.json       # 项目配置
│
├── backend/               # 后端项目目录
│   ├── config/           # 配置文件
│   │   ├── __init__.py
│   │   ├── config.py     # 主配置文件
│   │   ├── mysql.cnf     # 数据库配置
│   │   └── database.py   # 数据库连接配置
│   ├── routes/           # API 路由
│   │   ├── auth.py       # 认证相关
│   │   ├── stock.py      # 股票相关
│   │   └── profit.py     # 盈利统计
│   ├── models/           # 数据模型
│   ├── services/         # 业务逻辑
│   ├── utils/            # 工具函数
│   ├── scripts/          # 脚本文件
│   ├── tests/            # 测试文件
│   ├── main.py          # 主程序入口
│   └── requirements.txt  # Python 依赖
│
├── logs/                 # 日志文件
├── database.sql          # 数据库结构
└── README.md            # 项目说明
```

## 开发环境设置

### 后端设置

1. 创建并激活虚拟环境：
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置数据库：
```bash
mysql -u root -p < database.sql
```

4. 启动后端服务（默认端口 9099）：
```bash
python main.py
```

### 前端设置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器（默认端口 9009）：
```bash
npm run dev
```

## 主要功能

- 股票交易记录管理
- 盈亏统计分析
- 持仓监控
- 交易费用计算
- 数据导出

## 技术栈

### 前端
- Vue 3
- Vue Router
- Bootstrap 5
- Axios

### 后端
- Python 3.8+
- Flask
- MySQL
- SQLAlchemy

## 开发规范

1. 代码风格
   - 前端遵循 Vue 3 组合式 API 风格
   - 后端遵循 PEP 8 规范
   - 使用 ESLint 和 Prettier 进行代码格式化

2. 提交规范
   - feat: 新功能
   - fix: 修复问题
   - docs: 文档修改
   - style: 代码格式修改
   - refactor: 代码重构
   - test: 测试用例修改
   - chore: 其他修改

3. 分支管理
   - main: 主分支，用于生产环境
   - develop: 开发分支
   - feature/*: 功能分支
   - bugfix/*: 问题修复分支

## 部署说明

1. 后端部署
   - 使用 gunicorn 作为 WSGI 服务器
   - 使用 supervisor 进行进程管理
   - 使用 nginx 作为反向代理

2. 前端部署
   - 构建静态文件：`npm run build`
   - 使用 nginx 托管静态文件

## 许可证

MIT License

# GitHub自动更新容器

这是一个用于在群辉NAS的Container Manager中部署的Docker容器，可以自动监控GitHub仓库的更新并同步到本地。

## 功能特点

- 定期检查GitHub仓库更新
- 自动同步最新代码到本地
- 支持Webhook通知
- 支持自定义更新间隔
- 支持自定义分支
- 支持GitHub API令牌（提高API请求限制）
- 支持更新后执行自定义脚本

## 在群辉Container Manager中部署

### 方法一：使用Docker Compose

1. 在群辉中安装Docker和Container Manager
2. 创建一个目录用于存放配置文件和数据
3. 将本仓库中的文件上传到该目录
4. 修改`docker-compose.yml`文件中的环境变量
5. 在Container Manager中使用"添加 > 从docker-compose添加"功能

### 方法二：直接使用镜像

1. 在Container Manager中点击"添加"
2. 搜索并选择`alpine:latest`镜像
3. 设置容器名称为`github-updater`
4. 在"高级设置"中：
   - 添加环境变量
   - 设置卷映射
   - 设置自动重启策略
5. 启动容器

## 环境变量说明

| 环境变量 | 说明 | 必填 | 默认值 |
|---------|------|------|-------|
| GITHUB_REPO | GitHub仓库（格式：用户名/仓库名） | 是 | 无 |
| GITHUB_BRANCH | 要监控的分支 | 否 | main |
| LOCAL_PATH | 容器内存储路径 | 否 | /data |
| CHECK_INTERVAL | 检查间隔（秒） | 否 | 3600 |
| GITHUB_TOKEN | GitHub API令牌 | 否 | 无 |
| WEBHOOK_URL | 通知Webhook URL | 否 | 无 |
| TZ | 时区 | 否 | Asia/Shanghai |

## 卷映射

- `/data`: 用于存储同步的仓库内容

## 自定义更新后操作

如果您需要在更新后执行特定操作（如重启服务），可以在仓库中添加`post-update.sh`脚本。该脚本将在每次更新后自动执行。

## 日志查看

可以通过Container Manager的日志查看功能查看容器日志，了解更新状态。

## 故障排除

1. 如果容器无法启动，请检查环境变量是否正确设置
2. 如果无法连接GitHub，请检查网络连接
3. 如果API请求频繁失败，考虑添加GitHub Token
4. 如果需要访问私有仓库，必须提供有效的GitHub Token

## 安全注意事项

- 建议使用只读权限的GitHub Token
- 不要将包含敏感信息的Token直接写入docker-compose.yml
- 考虑使用群辉的环境变量功能存储敏感信息
