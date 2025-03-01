"""
角色权限关联模型
"""
from config.database import db
import logging

logger = logging.getLogger(__name__)

class RolePermission:
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.role_id = data.get('role_id') if data else None
        self.permission_id = data.get('permission_id') if data else None
        
    def save(self):
        """保存角色权限关联"""
        try:
            if self.id:
                # 更新
                sql = """
                    UPDATE stock.role_permissions 
                    SET role_id = %s, permission_id = %s 
                    WHERE id = %s
                """
                params = (self.role_id, self.permission_id, self.id)
                return db.execute(sql, params)
            else:
                # 新增
                sql = """
                    INSERT INTO stock.role_permissions 
                    (role_id, permission_id) 
                    VALUES (%s, %s)
                """
                params = (self.role_id, self.permission_id)
                self.id = db.insert(sql, params)
                return bool(self.id)
        except Exception as e:
            logger.error(f"保存角色权限关联失败: {str(e)}")
            return False
            
    def delete(self):
        """删除角色权限关联"""
        try:
            sql = "DELETE FROM stock.role_permissions WHERE id = %s"
            return db.execute(sql, (self.id,))
        except Exception as e:
            logger.error(f"删除角色权限关联失败: {str(e)}")
            return False
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'permission_id': self.permission_id
        }
        
    @staticmethod
    def get_by_id(role_permission_id):
        """根据ID获取角色权限关联"""
        try:
            sql = "SELECT * FROM stock.role_permissions WHERE id = %s"
            data = db.fetch_one(sql, (role_permission_id,))
            return RolePermission(data) if data else None
        except Exception as e:
            logger.error(f"获取角色权限关联失败: {str(e)}")
            return None
        
    @staticmethod
    def get_by_role_and_permission(role_id, permission_id):
        """根据角色ID和权限ID获取角色权限关联"""
        try:
            sql = "SELECT * FROM stock.role_permissions WHERE role_id = %s AND permission_id = %s"
            data = db.fetch_one(sql, (role_id, permission_id))
            return RolePermission(data) if data else None
        except Exception as e:
            logger.error(f"获取角色权限关联失败: {str(e)}")
            return None
        
    @staticmethod
    def get_by_role(role_id):
        """根据角色ID获取角色权限关联"""
        try:
            sql = "SELECT * FROM stock.role_permissions WHERE role_id = %s"
            data = db.fetch_all(sql, (role_id,))
            return [RolePermission(item) for item in data]
        except Exception as e:
            logger.error(f"获取角色权限关联失败: {str(e)}")
            return []
        
    @staticmethod
    def get_by_permission(permission_id):
        """根据权限ID获取角色权限关联"""
        try:
            sql = "SELECT * FROM stock.role_permissions WHERE permission_id = %s"
            data = db.fetch_all(sql, (permission_id,))
            return [RolePermission(item) for item in data]
        except Exception as e:
            logger.error(f"获取角色权限关联失败: {str(e)}")
            return []
            
    @staticmethod
    def delete_by_role(role_id):
        """删除角色的所有权限关联"""
        try:
            sql = "DELETE FROM stock.role_permissions WHERE role_id = %s"
            return db.execute(sql, (role_id,))
        except Exception as e:
            logger.error(f"删除角色权限关联失败: {str(e)}")
            return False
            
    @staticmethod
    def delete_by_permission(permission_id):
        """删除权限的所有角色关联"""
        try:
            sql = "DELETE FROM stock.role_permissions WHERE permission_id = %s"
            return db.execute(sql, (permission_id,))
        except Exception as e:
            logger.error(f"删除权限角色关联失败: {str(e)}")
            return False
            
    @staticmethod
    def assign_permissions_to_role(role_id, permission_ids):
        """为角色分配权限"""
        try:
            # 先删除角色的所有权限关联
            RolePermission.delete_by_role(role_id)
            
            # 再添加新的权限关联
            for permission_id in permission_ids:
                role_permission = RolePermission({
                    'role_id': role_id,
                    'permission_id': permission_id
                })
                role_permission.save()
                
            return True
        except Exception as e:
            logger.error(f"为角色分配权限失败: {str(e)}")
            return False 