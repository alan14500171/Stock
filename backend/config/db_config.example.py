"""
数据库配置模块示例文件
请复制此文件为 db_config.py 并修改相应配置
"""
import os
from typing import Dict, Any

# 数据库基础配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'port': 3306,
    'charset': 'utf8mb4',
}

# 不同环境的数据库名配置
DB_NAMES = {
    'development': 'stock',
    'testing': 'stock_test',
    'production': 'stock'
}

# SQLAlchemy 配置
SQLALCHEMY_CONFIG = {
    'pool_size': 20,
    'max_overflow': 40,
    'pool_timeout': 60,
    'pool_recycle': 1800,
    'pool_pre_ping': True,
    'connect_args': {
        'connect_timeout': 30,
        'read_timeout': 30,
        'write_timeout': 30,
        'charset': 'utf8mb4'
    }
}

def get_db_config(env: str = 'development') -> Dict[str, Any]:
    """获取指定环境的数据库配置"""
    config = DB_CONFIG.copy()
    config['database'] = DB_NAMES.get(env, DB_NAMES['development'])
    return config

def get_sqlalchemy_uri(env: str = 'development') -> str:
    """获取 SQLAlchemy 数据库 URI"""
    if env == 'production' and os.environ.get('DATABASE_URL'):
        return os.environ.get('DATABASE_URL')
    
    config = get_db_config(env)
    return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

def get_sqlalchemy_config() -> Dict[str, Any]:
    """获取 SQLAlchemy 配置"""
    return SQLALCHEMY_CONFIG 