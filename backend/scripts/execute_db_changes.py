#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
执行数据库字段更新脚本
使用方法：python execute_db_changes.py
"""

import sys
import os
import logging
import pymysql
import time
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/db_changes_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)

def ensure_log_directory():
    """确保日志目录存在"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

def get_db_connection():
    """
    获取数据库连接
    :return: 数据库连接对象
    """
    max_retries = 3
    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            logger.info("尝试连接数据库...")
            # 数据库连接配置
            conn = pymysql.connect(
                host='172.16.0.109',  # 数据库主机名
                user='root',       # 用户名
                password='Zxc000123', # 密码
                database='stock', # 数据库名
                port=3306,         # 端口号
                charset='utf8mb4', # 字符集
                cursorclass=pymysql.cursors.DictCursor, # 使用字典游标
                autocommit=False,   # 禁用自动提交
                connect_timeout=10,  # 连接超时时间
                read_timeout=30,     # 读取超时时间
                write_timeout=30     # 写入超时时间
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

def execute_sql_file(file_path):
    """
    执行SQL文件
    :param file_path: SQL文件路径
    """
    try:
        # 读取SQL文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = sql_content.split(';')
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        success_count = 0
        error_count = 0
        
        # 执行每条SQL语句
        for statement in sql_statements:
            statement = statement.strip()
            if statement:
                try:
                    logger.info(f"执行SQL: {statement}")
                    cursor.execute(statement)
                    success_count += 1
                    logger.info("SQL执行成功")
                except Exception as e:
                    error_count += 1
                    logger.error(f"SQL执行失败: {str(e)}")
                    # 不提交事务，继续执行下一条语句
        
        # 提交事务
        conn.commit()
        logger.info(f"SQL文件执行完成，成功: {success_count}，失败: {error_count}")
        
    except Exception as e:
        logger.error(f"执行SQL文件失败: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def main():
    """主函数"""
    try:
        # 确保日志目录存在
        ensure_log_directory()
        
        # SQL文件路径
        sql_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'add_database_fields.sql')
        
        # 检查SQL文件是否存在
        if not os.path.exists(sql_file_path):
            logger.error(f"SQL文件不存在: {sql_file_path}")
            return
        
        # 执行SQL文件
        logger.info(f"开始执行SQL文件: {sql_file_path}")
        execute_sql_file(sql_file_path)
        logger.info("数据库字段更新完成")
        
    except Exception as e:
        logger.error(f"执行过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main() 