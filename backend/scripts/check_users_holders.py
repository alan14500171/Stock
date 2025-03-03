#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import Database

def check_users_holders():
    """检查用户和持有人的对应关系"""
    db = Database()
    
    # 获取所有用户
    users_sql = "SELECT id, username, name, email FROM stock.users ORDER BY id"
    users = db.fetch_all(users_sql)
    
    print("所有用户:")
    for user in users:
        print(f"用户ID: {user['id']}, 用户名: {user['username']}, 姓名: {user['name']}, 邮箱: {user['email']}")
    
    # 获取所有持有人
    holders_sql = "SELECT id, name, user_id FROM stock.holders ORDER BY id"
    holders = db.fetch_all(holders_sql)
    
    print("\n所有持有人:")
    for holder in holders:
        print(f"持有人ID: {holder['id']}, 持有人名称: {holder['name']}, 关联用户ID: {holder['user_id']}")
    
    # 检查交易分单中的持有人ID
    holder_ids_sql = """
    SELECT DISTINCT holder_id, holder_name, COUNT(*) as count
    FROM stock.transaction_splits
    GROUP BY holder_id, holder_name
    ORDER BY holder_id
    """
    holder_ids = db.fetch_all(holder_ids_sql)
    
    print("\n交易分单中的持有人ID:")
    for holder in holder_ids:
        print(f"持有人ID: {holder['holder_id']}, 持有人名称: {holder['holder_name']}, 分单数量: {holder['count']}")
    
    # 检查用户lili的详细信息
    lili_sql = "SELECT * FROM stock.users WHERE username = 'lili'"
    lili = db.fetch_one(lili_sql)
    
    print("\n用户lili的详细信息:")
    if lili:
        for key, value in lili.items():
            print(f"{key}: {value}")
    else:
        print("未找到用户lili")
    
    # 检查持有人lili的详细信息
    holder_lili_sql = "SELECT * FROM stock.holders WHERE name = 'lili'"
    holder_lili = db.fetch_one(holder_lili_sql)
    
    print("\n持有人lili的详细信息:")
    if holder_lili:
        for key, value in holder_lili.items():
            print(f"{key}: {value}")
    else:
        print("未找到持有人lili")

if __name__ == "__main__":
    check_users_holders() 