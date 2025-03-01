#!/usr/bin/env python3
"""
初始化RBAC权限管理相关的数据库表
"""
import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_rbac():
    """初始化RBAC权限管理相关的数据库表"""
    try:
        # 读取SQL文件
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_rbac_tables.sql')
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        # 执行SQL
        db.execute_script(sql)
        logger.info("RBAC权限管理相关的数据库表初始化成功")
        
        # 为现有用户分配角色
        assign_roles_to_existing_users()
        
        return True
    except Exception as e:
        logger.error(f"初始化RBAC权限管理相关的数据库表失败: {str(e)}")
        return False
        
def assign_roles_to_existing_users():
    """为现有用户分配角色"""
    try:
        # 获取所有用户
        users = db.fetch_all("SELECT id FROM stock.users")
        
        # 获取超级管理员角色ID
        admin_role = db.fetch_one("SELECT id FROM stock.roles WHERE name = '超级管理员'")
        if not admin_role:
            logger.error("未找到超级管理员角色")
            return False
            
        admin_role_id = admin_role['id']
        
        # 为每个用户分配超级管理员角色
        for user in users:
            user_id = user['id']
            # 检查是否已经分配了角色
            existing = db.fetch_one(
                "SELECT id FROM stock.user_roles WHERE user_id = %s AND role_id = %s",
                (user_id, admin_role_id)
            )
            
            if not existing:
                db.execute(
                    "INSERT INTO stock.user_roles (user_id, role_id) VALUES (%s, %s)",
                    (user_id, admin_role_id)
                )
                logger.info(f"为用户 {user_id} 分配超级管理员角色")
                
        logger.info("为现有用户分配角色成功")
        return True
    except Exception as e:
        logger.error(f"为现有用户分配角色失败: {str(e)}")
        return False

if __name__ == "__main__":
    init_rbac() 