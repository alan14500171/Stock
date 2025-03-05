#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pymysql
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_db_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database():
    """检查数据库是否存在，如果不存在则创建"""
    # 获取生产环境配置
    db_config = get_db_config('production')
    
    logger.info(f"尝试连接到数据库服务器: {db_config['host']}:{db_config['port']}")
    logger.info(f"用户: {db_config['user']}")
    logger.info(f"目标数据库: {db_config['db']}")
    
    try:
        # 尝试连接到MySQL服务器，不指定数据库
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config['charset']
        )
        
        logger.info("成功连接到MySQL服务器")
        
        with conn.cursor() as cursor:
            # 列出所有数据库
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            
            # 转换为列表，方便查看
            db_list = [db[0] for db in databases]
            logger.info(f"可用的数据库: {db_list}")
            
            # 检查数据库是否存在（不区分大小写）
            target_db = db_config['db']
            db_exists = False
            actual_db_name = None
            
            for db in db_list:
                if db.lower() == target_db.lower():
                    db_exists = True
                    actual_db_name = db
                    break
            
            if db_exists:
                logger.info(f"找到数据库: '{actual_db_name}'")
                
                # 如果实际数据库名称与配置中的不一致，更新配置
                if actual_db_name != target_db:
                    logger.warning(f"数据库名称大小写不一致: 配置中为 '{target_db}'，实际为 '{actual_db_name}'")
                    logger.info("尝试使用实际数据库名称连接...")
                    
                    # 尝试使用实际数据库名称
                    try:
                        cursor.execute(f"USE `{actual_db_name}`")
                        logger.info(f"成功切换到数据库 '{actual_db_name}'")
                        
                        # 列出表
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        if tables:
                            table_list = [table[0] for table in tables]
                            logger.info(f"数据库中的表: {table_list}")
                        else:
                            logger.info("数据库中没有表")
                        
                        logger.info("建议更新配置文件中的数据库名称，使其与实际名称一致")
                    except Exception as e:
                        logger.error(f"无法使用数据库 '{actual_db_name}': {str(e)}")
                        logger.info("这可能是权限问题")
            else:
                logger.warning(f"数据库 '{target_db}' 不存在")
                
                # 尝试创建数据库
                try:
                    logger.info(f"尝试创建数据库 '{target_db}'...")
                    cursor.execute(f"CREATE DATABASE `{target_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"成功创建数据库 '{target_db}'")
                except Exception as e:
                    logger.error(f"无法创建数据库: {str(e)}")
                    logger.info("这可能是权限问题，请手动创建数据库")
            
            # 检查用户权限
            try:
                cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
                grants = cursor.fetchall()
                logger.info("当前用户权限:")
                for grant in grants:
                    logger.info(f"  {grant[0]}")
                
                # 检查是否有对目标数据库的权限
                has_db_permission = False
                for grant in grants:
                    grant_str = grant[0].lower()
                    if (f"on `{target_db.lower()}`" in grant_str or 
                        f"on `{actual_db_name.lower() if actual_db_name else ''}`" in grant_str or 
                        "on *.* to" in grant_str):
                        has_db_permission = True
                        break
                
                if has_db_permission:
                    logger.info(f"用户 '{db_config['user']}' 有权限访问数据库")
                else:
                    logger.warning(f"用户 '{db_config['user']}' 可能没有足够的权限访问数据库")
                    logger.info("请检查用户权限或使用有足够权限的用户")
            except Exception as e:
                logger.error(f"检查用户权限时出错: {str(e)}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"连接数据库时出错: {str(e)}")
        logger.info("请检查数据库配置和网络连接")

if __name__ == "__main__":
    create_database() 