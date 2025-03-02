#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查会话中的用户ID
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

def check_session():
    """检查会话中的用户ID"""
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询用户ID
        cursor.execute("SELECT id FROM users WHERE username = 'alan'")
        user = cursor.fetchone()
        
        if user:
            print(f"用户alan的ID: {user['id']}")
        else:
            print("用户alan不存在")
            
        # 关闭连接
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"检查会话失败: {str(e)}")

if __name__ == "__main__":
    check_session() 