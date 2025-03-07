#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from config.database import db

def reset_admin_password():
    """重置管理员用户的密码"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # 获取管理员用户
        admin_usernames = ['admin', 'alan']
        
        for username in admin_usernames:
            logger.info(f"尝试重置用户 {username} 的密码")
            
            # 查找用户
            user = User.find_by_username(username)
            
            if not user:
                logger.warning(f"用户 {username} 不存在，跳过")
                continue
            
            # 设置新密码
            new_password = "123123"  # 默认密码，建议部署后立即修改
            
            # 使用 bcrypt 设置密码
            user.set_password(new_password)
            
            # 保存用户
            if user.save():
                logger.info(f"用户 {username} 密码重置成功")
            else:
                logger.error(f"用户 {username} 密码重置失败")
        
        logger.info("密码重置操作完成")
        
    except Exception as e:
        logger.error(f"重置密码时出错: {str(e)}")

if __name__ == "__main__":
    reset_admin_password() 