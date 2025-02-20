# 股票交易管理系统

这是一个用于管理股票交易记录的系统，支持港股和美股的交易记录管理。

## 功能特点

- 支持港股和美股交易记录管理
- 实时汇率转换
- 交易明细查看
- 盈亏统计分析
- 股票基本信息管理

## 技术栈

### 后端
- Python 3.12
- Flask
- MySQL

### 前端
- Vue 3
- Bootstrap 5
- Bootstrap Icons
- Axios

## 安装说明

### 后端环境配置

1. 创建 Python 虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置数据库：
```bash
mysql -u root -p < database.sql
```

### 前端环境配置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

## 运行说明

### 启动后端服务

```bash
python main.py
```

### 启动前端服务

```bash
cd frontend
npm run dev
```

## 配置说明

1. 后端配置文件：`config/config.py`
2. 前端配置文件：`frontend/vite.config.js`

## 主要功能模块

1. 用户认证
2. 股票管理
3. 交易记录
4. 盈亏统计
5. 汇率管理

## 开发团队

- 后端开发：[您的名字]
- 前端开发：[您的名字]

## 许可证

MIT License
