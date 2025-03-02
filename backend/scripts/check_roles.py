#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_roles():
    try:
        # 检查角色表结构
        desc_sql = """
            DESCRIBE roles
        """
        table_structure = db.fetch_all(desc_sql)
        logger.info("\n角色表结构:")
        for column in table_structure:
            logger.info(f"字段: {column['Field']}, 类型: {column['Type']}, 是否可空: {column['Null']}, 默认值: {column['Default']}")
            
        # 获取所有角色
        roles_sql = "SELECT * FROM roles"
        roles = db.fetch_all(roles_sql)
        
        if not roles:
            logger.warning("\n角色表中没有数据")
            
            # 创建默认角色
            default_roles = [
                ('超级管理员', 'admin', '系统超级管理员'),
                ('普通用户', 'user', '普通用户角色'),
                ('查看者', 'viewer', '只有查看权限的角色')
            ]
            
            insert_sql = """
                INSERT INTO roles (name, code, description, status)
                VALUES (%s, %s, %s, 1)
            """
            
            for role in default_roles:
                try:
                    db.execute(insert_sql, role)
                    logger.info(f"创建角色成功: {role[0]}")
                except Exception as e:
                    logger.error(f"创建角色失败 {role[0]}: {str(e)}")
        else:
            logger.info("\n现有角色数据:")
            for role in roles:
                logger.info(f"角色数据: {role}")
    except Exception as e:
        logger.error(f"检查角色数据时发生错误: {str(e)}")

if __name__ == '__main__':
    # 初始化数据库连接
    db.init_pool()
    check_roles() 