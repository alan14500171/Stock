"""
用户角色关联模型
"""
from config.database import db
import logging

logger = logging.getLogger(__name__)

class UserRole:
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.user_id = data.get('user_id') if data else None
        self.role_id = data.get('role_id') if data else None
        
    def save(self):
        """保存用户角色关联"""
        try:
            if self.id:
                # 更新
                sql = """
                    UPDATE stock.user_roles 
                    SET user_id = %s, role_id = %s 
                    WHERE id = %s
                """
                params = (self.user_id, self.role_id, self.id)
                return db.execute(sql, params)
            else:
                # 新增
                sql = """
                    INSERT INTO stock.user_roles 
                    (user_id, role_id) 
                    VALUES (%s, %s)
                """
                params = (self.user_id, self.role_id)
                self.id = db.insert(sql, params)
                return bool(self.id)
        except Exception as e:
            logger.error(f"保存用户角色关联失败: {str(e)}")
            return False
            
    def delete(self):
        """删除用户角色关联"""
        try:
            sql = "DELETE FROM stock.user_roles WHERE id = %s"
            return db.execute(sql, (self.id,))
        except Exception as e:
            logger.error(f"删除用户角色关联失败: {str(e)}")
            return False
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id
        }
        
    @staticmethod
    def get_by_id(user_role_id):
        """根据ID获取用户角色关联"""
        try:
            sql = "SELECT * FROM stock.user_roles WHERE id = %s"
            data = db.fetch_one(sql, (user_role_id,))
            return UserRole(data) if data else None
        except Exception as e:
            logger.error(f"获取用户角色关联失败: {str(e)}")
            return None
        
    @staticmethod
    def get_by_user_and_role(user_id, role_id):
        """根据用户ID和角色ID获取用户角色关联"""
        try:
            sql = "SELECT * FROM stock.user_roles WHERE user_id = %s AND role_id = %s"
            data = db.fetch_one(sql, (user_id, role_id))
            return UserRole(data) if data else None
        except Exception as e:
            logger.error(f"获取用户角色关联失败: {str(e)}")
            return None
        
    @staticmethod
    def get_by_user(user_id):
        """根据用户ID获取用户角色关联"""
        try:
            sql = "SELECT * FROM stock.user_roles WHERE user_id = %s"
            data = db.fetch_all(sql, (user_id,))
            return [UserRole(item) for item in data]
        except Exception as e:
            logger.error(f"获取用户角色关联失败: {str(e)}")
            return []
        
    @staticmethod
    def get_by_role(role_id):
        """根据角色ID获取用户角色关联"""
        try:
            sql = "SELECT * FROM stock.user_roles WHERE role_id = %s"
            data = db.fetch_all(sql, (role_id,))
            return [UserRole(item) for item in data]
        except Exception as e:
            logger.error(f"获取用户角色关联失败: {str(e)}")
            return []
            
    @staticmethod
    def delete_by_user(user_id):
        """删除用户的所有角色关联"""
        try:
            sql = "DELETE FROM stock.user_roles WHERE user_id = %s"
            return db.execute(sql, (user_id,))
        except Exception as e:
            logger.error(f"删除用户角色关联失败: {str(e)}")
            return False
            
    @staticmethod
    def delete_by_role(role_id):
        """删除角色的所有用户关联"""
        try:
            sql = "DELETE FROM stock.user_roles WHERE role_id = %s"
            return db.execute(sql, (role_id,))
        except Exception as e:
            logger.error(f"删除角色用户关联失败: {str(e)}")
            return False
            
    @staticmethod
    def assign_roles_to_user(user_id, role_ids):
        """为用户分配角色"""
        try:
            # 先删除用户的所有角色关联
            UserRole.delete_by_user(user_id)
            
            # 再添加新的角色关联
            for role_id in role_ids:
                user_role = UserRole({
                    'user_id': user_id,
                    'role_id': role_id
                })
                user_role.save()
                
            return True
        except Exception as e:
            logger.error(f"为用户分配角色失败: {str(e)}")
            return False 