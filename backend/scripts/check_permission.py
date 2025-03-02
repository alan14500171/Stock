#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查profit:stats:view权限是否存在
"""

import sys
import os
import pymysql
from pymysql.cursors import DictCursor

# 数据库配置
DB_CONFIG = {
    'host': '118.101.108.48',
    'user': 'root',
    'password': 'Zxc000123',
    'port': 3306,
    'database': 'stock',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

def check_permission():
    """检查profit:stats:view权限是否存在"""
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询权限
        cursor.execute("SELECT * FROM permissions WHERE code = 'profit:stats:view'")
        permission = cursor.fetchone()
        
        if permission:
            print(f"权限存在，ID: {permission['id']}")
            
            # 查询admin角色是否有此权限
            cursor.execute("""
                SELECT * FROM role_permissions rp
                JOIN roles r ON rp.role_id = r.id
                WHERE r.name = 'admin' AND rp.permission_id = %s
            """, (permission['id'],))
            
            admin_has_permission = cursor.fetchone()
            print(f"admin角色是否有此权限: {bool(admin_has_permission)}")
            
            # 查询alan用户是否有此权限
            cursor.execute("""
                SELECT * FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                JOIN users u ON ur.user_id = u.id
                WHERE u.username = 'alan' AND r.name = 'admin'
            """)
            
            alan_is_admin = cursor.fetchone()
            print(f"alan用户是否是admin角色: {bool(alan_is_admin)}")
            
            if alan_is_admin:
                print("alan用户应该有profit:stats:view权限")
            else:
                print("alan用户可能没有profit:stats:view权限")
        else:
            print("权限不存在")
            
        # 关闭连接
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"检查权限失败: {str(e)}")

if __name__ == "__main__":
    check_permission() 