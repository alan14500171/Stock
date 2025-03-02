#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
添加profit:stats:view权限并分配给admin角色
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
from models.permission import Permission
from models.role import Role

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_profit_stats_view_permission():
    """添加profit:stats:view权限并分配给admin角色"""
    try:
        # 检查权限是否已存在
        profit_stats_view = Permission.get_by_code('profit:stats:view')
        
        if profit_stats_view:
            logger.info(f"profit:stats:view权限已存在，ID: {profit_stats_view.id}")
        else:
            # 获取profit:stats权限作为父权限
            profit_stats = Permission.get_by_code('profit:stats')
            
            if not profit_stats:
                # 如果profit:stats不存在，先获取profit权限
                profit = Permission.get_by_code('profit')
                
                if not profit:
                    # 如果profit权限不存在，创建它
                    logger.info("创建profit权限")
                    sql = """
                    INSERT INTO permissions (name, code, description, type, parent_id, path, level, sort_order, is_menu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    profit_id = db.insert(sql, [
                        '收益统计', 'profit', '收益统计模块', 1, 
                        None, '', 1, 
                        3, 1
                    ])
                    profit = Permission.get_by_id(profit_id)
                    logger.info(f"创建profit权限成功，ID: {profit_id}")
                
                # 创建profit:stats权限
                logger.info("创建profit:stats权限")
                sql = """
                INSERT INTO permissions (name, code, description, type, parent_id, path, level, sort_order, is_menu)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                profit_stats_id = db.insert(sql, [
                    '收益统计', 'profit:stats', '收益统计功能', 2, 
                    profit.id, f"{profit.path}/{profit.id}", profit.level + 1, 
                    1, 1
                ])
                profit_stats = Permission.get_by_id(profit_stats_id)
                logger.info(f"创建profit:stats权限成功，ID: {profit_stats_id}")
            
            # 添加profit:stats:view权限
            logger.info("创建profit:stats:view权限")
            sql = """
            INSERT INTO permissions (name, code, description, type, parent_id, path, level, sort_order, is_menu)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            profit_stats_view_id = db.insert(sql, [
                '查看收益统计', 'profit:stats:view', '查看收益统计权限', 3, 
                profit_stats.id, f"{profit_stats.path}/{profit_stats.id}", profit_stats.level + 1, 
                1, 0
            ])
            profit_stats_view = Permission.get_by_id(profit_stats_view_id)
            logger.info(f"创建profit:stats:view权限成功，ID: {profit_stats_view_id}")
        
        # 分配给admin角色
        admin_role = Role.find_by_name('admin')
        if admin_role:
            # 检查是否已分配
            sql = "SELECT * FROM role_permissions WHERE role_id = %s AND permission_id = %s"
            existing = db.fetch_one(sql, [admin_role.id, profit_stats_view.id])
            
            if existing:
                logger.info(f"admin角色已有profit:stats:view权限")
            else:
                # 分配权限
                sql = "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)"
                db.execute(sql, [admin_role.id, profit_stats_view.id])
                logger.info(f"已将profit:stats:view权限分配给admin角色")
        else:
            logger.error("未找到admin角色")
            
        # 分配给user角色
        user_role = Role.find_by_name('user')
        if user_role:
            # 检查是否已分配
            sql = "SELECT * FROM role_permissions WHERE role_id = %s AND permission_id = %s"
            existing = db.fetch_one(sql, [user_role.id, profit_stats_view.id])
            
            if existing:
                logger.info(f"user角色已有profit:stats:view权限")
            else:
                # 分配权限
                sql = "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)"
                db.execute(sql, [user_role.id, profit_stats_view.id])
                logger.info(f"已将profit:stats:view权限分配给user角色")
        else:
            logger.error("未找到user角色")
            
        logger.info("权限添加和分配完成")
        return True
    except Exception as e:
        logger.error(f"添加权限失败: {str(e)}")
        return False

if __name__ == "__main__":
    add_profit_stats_view_permission() 