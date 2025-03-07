"""
配置包
包含应用的所有配置相关模块
"""

from .config import Config, DevelopmentConfig, TestingConfig, ProductionConfig, config
from .database import db, init_db

__all__ = [
    'Config',
    'DevelopmentConfig',
    'TestingConfig',
    'ProductionConfig',
    'config',
    'db',
    'init_db'
] 