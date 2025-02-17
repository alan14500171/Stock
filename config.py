import os
from datetime import timedelta

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    PORT = 9009
    HOST = '0.0.0.0'
    DEBUG = True
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Zxc000123@192.168.0.109:3306/Stock'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,  # 增加连接池大小
        'max_overflow': 40,  # 增加最大溢出连接数
        'pool_timeout': 60,  # 增加池等待时间
        'pool_recycle': 1800,  # 保持连接重置周期
        'pool_pre_ping': True,  # 保持连接检测
        'connect_args': {
            'connect_timeout': 30,  # 增加连接超时时间
            'read_timeout': 30,  # 增加读取超时时间
            'write_timeout': 30,  # 增加写入超时时间
            'charset': 'utf8mb4'  # 添加字符集设置
        }
    }
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 模板自动重载
    TEMPLATES_AUTO_RELOAD = True 