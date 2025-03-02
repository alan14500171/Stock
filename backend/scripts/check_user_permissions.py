#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查用户alan的权限
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from models.permission import Permission

def check_user_permissions():
    """检查用户alan的权限"""
    # 获取用户
    user = User.find_by_username('alan')
    if not user:
        print("用户alan不存在")
        return
    
    print(f"用户ID: {user.id}")
    print(f"用户名: {user.username}")
    
    # 获取用户权限
    permissions = Permission.get_user_permissions(user.id)
    print(f"用户权限数量: {len(permissions)}")
    
    # 获取profit相关权限
    profit_permissions = [p.code for p in permissions if p.code.startswith('profit')]
    print(f"profit相关权限: {json.dumps(profit_permissions, ensure_ascii=False, indent=2)}")
    
    # 检查是否有profit:stats:view权限
    has_profit_stats_view = 'profit:stats:view' in profit_permissions
    print(f"是否有profit:stats:view权限: {has_profit_stats_view}")

if __name__ == "__main__":
    check_user_permissions() 