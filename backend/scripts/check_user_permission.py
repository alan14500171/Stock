#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查用户alan是否有profit:stats:view权限
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

def check_user_permission():
    """检查用户alan是否有profit:stats:view权限"""
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询用户ID
        cursor.execute("SELECT id FROM users WHERE username = 'alan'")
        user = cursor.fetchone()
        
        if not user:
            print("用户alan不存在")
            return
            
        user_id = user['id']
        print(f"用户alan的ID: {user_id}")
        
        # 查询权限ID
        cursor.execute("SELECT id FROM permissions WHERE code = 'profit:stats:view'")
        permission = cursor.fetchone()
        
        if not permission:
            print("权限profit:stats:view不存在")
            return
            
        permission_id = permission['id']
        print(f"权限profit:stats:view的ID: {permission_id}")
        
        # 查询用户是否有此权限
        cursor.execute("""
            SELECT * FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            WHERE ur.user_id = %s AND rp.permission_id = %s
        """, (user_id, permission_id))
        
        has_permission = cursor.fetchone()
        print(f"用户alan是否有profit:stats:view权限: {bool(has_permission)}")
        
        if has_permission:
            print("用户alan有profit:stats:view权限")
        else:
            print("用户alan没有profit:stats:view权限")
            
            # 查询用户角色
            cursor.execute("""
                SELECT r.* FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = %s
            """, (user_id,))
            
            roles = cursor.fetchall()
            print(f"用户alan的角色: {[role['name'] for role in roles]}")
            
            # 查询角色权限
            for role in roles:
                cursor.execute("""
                    SELECT p.* FROM permissions p
                    JOIN role_permissions rp ON p.id = rp.permission_id
                    WHERE rp.role_id = %s AND p.code = 'profit:stats:view'
                """, (role['id'],))
                
                role_has_permission = cursor.fetchone()
                print(f"角色{role['name']}是否有profit:stats:view权限: {bool(role_has_permission)}")
        
        # 关闭连接
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"检查用户权限失败: {str(e)}")

if __name__ == "__main__":
    check_user_permission() 