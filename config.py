import os
from datetime import timedelta

class Config:
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Zxc000123@192.168.0.109:3306/Stock'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # 连接池大小
        'max_overflow': 20,  # 超过连接池大小外最多创建的连接数
        'pool_timeout': 30,  # 池中没有连接时的等待时间
        'pool_recycle': 1800,  # 连接重置周期，避免MySQL 8小时连接超时问题
        'pool_pre_ping': True,  # 每次连接前ping一下服务器，确保连接可用
        'connect_args': {
            'connect_timeout': 10,  # 连接超时时间
            'read_timeout': 10,  # 读取超时时间
            'write_timeout': 10  # 写入超时时间
        }
    }
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 模板自动重载
    TEMPLATES_AUTO_RELOAD = True 