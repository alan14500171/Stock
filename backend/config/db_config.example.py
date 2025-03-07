"""
数据库配置模块示例文件
请复制此文件为 db_config.py 并修改相应配置
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

def get_db_config(env: str = 'production') -> Dict[str, Any]:
    """获取数据库配置"""
    configs = {
        'development': {
            'host': 'localhost',  # 本地开发环境
            'port': 3306,
            'user': 'stockuser',
            'password': 'dev_password',
            'db': 'stock',
            'charset': 'utf8mb4'
        },
        'production': {
            'host': '192.168.1.100',  # 替换为您的实际数据库IP地址
            'port': 3306,
            'user': 'stockuser',
            'password': 'your_password',  # 替换为您的实际数据库密码
            'db': 'stock',
            'charset': 'utf8mb4'
        }
    }
    return configs.get(env, configs['development'])

def get_sqlalchemy_uri(env: str = 'production') -> str:
    """获取SQLAlchemy连接URI"""
    config = get_db_config(env)
    return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}?charset={config['charset']}"

def get_sqlalchemy_config() -> Dict[str, Any]:
    """获取SQLAlchemy配置"""
    return {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    } 