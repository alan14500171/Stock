"""
为用户alan添加所有权限的脚本
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from config.database import db
from config.logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def grant_alan_permissions():
    """为用户alan添加所有权限"""
    try:
        # 读取SQL文件
        sql_file_path = os.path.join(current_dir, 'grant_alan_all_permissions.sql')
        logger.info(f"SQL文件路径: {sql_file_path}")
        
        if not os.path.exists(sql_file_path):
            logger.error(f"SQL文件不存在: {sql_file_path}")
            return False
            
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            logger.info(f"SQL文件内容长度: {len(sql_content)} 字符")
        
        # 按分号分割SQL语句
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        logger.info(f"SQL语句数量: {len(sql_statements)}")
        
        # 执行每条SQL语句
        logger.info("开始为用户alan添加权限...")
        
        # 确保超级管理员角色存在
        db.execute("""
        INSERT INTO stock.roles (name, description) 
        VALUES ('超级管理员', '系统超级管理员，拥有所有权限')
        ON DUPLICATE KEY UPDATE name=name
        """)
        logger.info("确保超级管理员角色存在")
        
        # 获取超级管理员角色ID
        admin_role = db.fetch_one("SELECT id FROM stock.roles WHERE name = '超级管理员'")
        if not admin_role:
            logger.error("无法获取超级管理员角色ID")
            return False
            
        admin_role_id = admin_role['id']
        logger.info(f"超级管理员角色ID: {admin_role_id}")
        
        # 将alan用户添加到超级管理员角色
        db.execute("""
        INSERT INTO stock.user_roles (user_id, role_id)
        VALUES (3, %s)
        ON DUPLICATE KEY UPDATE user_id=user_id
        """, (admin_role_id,))
        logger.info("将alan用户添加到超级管理员角色")
        
        # 确保超级管理员角色拥有所有权限
        db.execute("""
        INSERT INTO stock.role_permissions (role_id, permission_id)
        SELECT 
            %s,
            id
        FROM 
            stock.permissions
        ON DUPLICATE KEY UPDATE role_id=role_id
        """, (admin_role_id,))
        logger.info("确保超级管理员角色拥有所有权限")
        
        # 查询确认alan用户的角色
        roles = db.fetch_all("""
        SELECT u.username, r.name as role_name
        FROM stock.users u
        JOIN stock.user_roles ur ON u.id = ur.user_id
        JOIN stock.roles r ON ur.role_id = r.id
        WHERE u.id = 3
        """)
        logger.info(f"alan用户的角色: {roles}")
        
        # 查询确认alan用户的权限数量
        permissions = db.fetch_all("""
        SELECT u.username, COUNT(DISTINCT p.id) as permission_count
        FROM stock.users u
        JOIN stock.user_roles ur ON u.id = ur.user_id
        JOIN stock.roles r ON ur.role_id = r.id
        JOIN stock.role_permissions rp ON r.id = rp.role_id
        JOIN stock.permissions p ON rp.permission_id = p.id
        WHERE u.id = 3
        GROUP BY u.username
        """)
        logger.info(f"alan用户的权限数量: {permissions}")
        
        logger.info("用户alan权限添加完成")
        return True
    except Exception as e:
        logger.error(f"为用户alan添加权限失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = grant_alan_permissions()
    if success:
        print("成功为用户alan添加所有权限")
    else:
        print("为用户alan添加权限失败，请查看日志")
        sys.exit(1) 