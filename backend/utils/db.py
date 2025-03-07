#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库连接工具模块
"""

import pymysql
import logging
import time
from pymysql.cursors import DictCursor
from config.db_config import get_db_config

logger = logging.getLogger(__name__)

def get_db_connection(env='development'):
    """
    获取数据库连接
    :param env: 环境名称 ('development', 'testing', 'production')
    :return: 数据库连接对象
    """
    max_retries = 3
    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            logger.info("尝试连接数据库...")
            # 获取数据库配置
            config = get_db_config(env)
            
            # 数据库连接配置
            conn = pymysql.connect(
                **config,
                cursorclass=DictCursor,
                autocommit=False,
                connect_timeout=10,
                read_timeout=30,
                write_timeout=30
            )
            
            # 初始化连接设置
            with conn.cursor() as cursor:
                cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
                cursor.execute("SET SESSION time_zone='+8:00'")
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            logger.info("数据库连接成功")
            return conn
        except Exception as e:
            retry_count += 1
            last_exception = e
            logger.error(f"数据库连接失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                time.sleep(1)  # 等待1秒后重试
    
    logger.error(f"数据库连接失败，已达到最大重试次数: {str(last_exception)}")
    raise last_exception 