"""
应用配置模块
"""

import os
from datetime import timedelta
from .db_config import get_sqlalchemy_uri, get_sqlalchemy_config

class Config:
    """基础配置类"""
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    PORT = 9099
    HOST = '127.0.0.1'
    DEBUG = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = get_sqlalchemy_uri('development')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = get_sqlalchemy_config()
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 模板自动重载
    TEMPLATES_AUTO_RELOAD = True

class DevelopmentConfig(Config):
    """开发环境配置类"""
    DEBUG = True
    HOST = '127.0.0.1'
    PORT = 9099
    
    # 开发环境数据库配置
    SQLALCHEMY_DATABASE_URI = get_sqlalchemy_uri('development')
    
    # 开发环境日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True

class TestingConfig(Config):
    """测试环境配置类"""
    TESTING = True
    DEBUG = True
    
    # 测试环境数据库配置
    SQLALCHEMY_DATABASE_URI = get_sqlalchemy_uri('testing')
    
    # 测试环境日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True

class ProductionConfig(Config):
    """生产环境配置类"""
    DEBUG = False
    
    # 生产环境数据库配置
    SQLALCHEMY_DATABASE_URI = get_sqlalchemy_uri('production')
    
    # 生产环境日志配置
    LOG_LEVEL = 'INFO'
    LOG_TO_STDOUT = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 