"""
角色模型 - 用于RBAC权限管理
"""
from datetime import datetime
from config.database import db
import logging

logger = logging.getLogger(__name__)

class Role:
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.name = data.get('name') if data else None
        self.description = data.get('description') if data else None
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        self.updated_at = data.get('updated_at') if data else datetime.utcnow()
        
    def save(self):
        """保存角色"""
        try:
            if self.id:
                # 更新
                sql = """
                    UPDATE stock.roles 
                    SET name = %s, description = %s, updated_at = NOW() 
                    WHERE id = %s
                """
                params = (self.name, self.description, self.id)
                return db.execute(sql, params)
            else:
                # 新增
                sql = """
                    INSERT INTO stock.roles 
                    (name, description, created_at, updated_at) 
                    VALUES (%s, %s, NOW(), NOW())
                """
                params = (self.name, self.description)
                self.id = db.insert(sql, params)
                return bool(self.id)
        except Exception as e:
            logger.error(f"保存角色失败: {str(e)}")
            return False
            
    def delete(self):
        """删除角色"""
        try:
            # 先删除角色-权限关联
            sql_delete_role_permissions = """
                DELETE FROM stock.role_permissions WHERE role_id = %s
            """
            db.execute(sql_delete_role_permissions, (self.id,))
            
            # 再删除用户-角色关联
            sql_delete_user_roles = """
                DELETE FROM stock.user_roles WHERE role_id = %s
            """
            db.execute(sql_delete_user_roles, (self.id,))
            
            # 最后删除角色
            sql = "DELETE FROM stock.roles WHERE id = %s"
            return db.execute(sql, (self.id,))
        except Exception as e:
            logger.error(f"删除角色失败: {str(e)}")
            return False
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    @staticmethod
    def get_by_id(role_id):
        """根据ID获取角色"""
        try:
            sql = "SELECT * FROM stock.roles WHERE id = %s"
            data = db.fetch_one(sql, (role_id,))
            return Role(data) if data else None
        except Exception as e:
            logger.error(f"获取角色失败: {str(e)}")
            return None
        
    @staticmethod
    def get_all():
        """获取所有角色"""
        try:
            sql = "SELECT * FROM stock.roles ORDER BY name"
            data = db.fetch_all(sql)
            return [Role(item) for item in data]
        except Exception as e:
            logger.error(f"获取所有角色失败: {str(e)}")
            return []
            
    @staticmethod
    def find_by_name(name):
        """根据名称查找角色"""
        try:
            sql = "SELECT * FROM stock.roles WHERE name = %s"
            data = db.fetch_one(sql, (name,))
            return Role(data) if data else None
        except Exception as e:
            logger.error(f"查找角色失败: {str(e)}")
            return None
            
    @staticmethod
    def get_user_roles(user_id):
        """获取用户的所有角色"""
        try:
            sql = """
                SELECT r.* FROM stock.roles r
                JOIN stock.user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = %s
            """
            data = db.fetch_all(sql, (user_id,))
            return [Role(item) for item in data]
        except Exception as e:
            logger.error(f"获取用户角色失败: {str(e)}")
            return [] 