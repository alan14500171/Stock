"""
权限模型 - 用于RBAC权限管理
"""
from datetime import datetime
from config.database import db
import logging

logger = logging.getLogger(__name__)

class Permission:
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.name = data.get('name') if data else None
        self.code = data.get('code') if data else None
        self.description = data.get('description') if data else None
        self.type = data.get('type') if data else None
        self.parent_id = data.get('parent_id') if data else None
        self.path = data.get('path') if data else None
        self.level = data.get('level') if data else None
        self.sort_order = data.get('sort_order') if data else None
        self.is_menu = data.get('is_menu') if data else None
        self.icon = data.get('icon') if data else None
        self.component = data.get('component') if data else None
        self.route_path = data.get('route_path') if data else None
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        self.updated_at = data.get('updated_at') if data else datetime.utcnow()
        
    def save(self):
        """保存权限"""
        try:
            if self.id:
                # 更新
                sql = """
                    UPDATE stock.permissions 
                    SET name = %s, code = %s, description = %s, type = %s, parent_id = %s,
                        path = %s, level = %s, sort_order = %s, is_menu = %s,
                        icon = %s, component = %s, route_path = %s, updated_at = NOW() 
                    WHERE id = %s
                """
                params = (
                    self.name, self.code, self.description, self.type, self.parent_id,
                    self.path, self.level, self.sort_order, self.is_menu,
                    self.icon, self.component, self.route_path, self.id
                )
                return db.execute(sql, params)
            else:
                # 新增
                sql = """
                    INSERT INTO stock.permissions 
                    (name, code, description, type, parent_id, path, level, sort_order, 
                     is_menu, icon, component, route_path, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """
                params = (
                    self.name, self.code, self.description, self.type, self.parent_id,
                    self.path, self.level, self.sort_order, self.is_menu,
                    self.icon, self.component, self.route_path
                )
                self.id = db.insert(sql, params)
                
                # 更新路径
                if self.id:
                    self._update_path()
                    
                return bool(self.id)
        except Exception as e:
            logger.error(f"保存权限失败: {str(e)}")
            return False
    
    def _update_path(self):
        """更新权限路径"""
        try:
            if self.parent_id:
                parent = Permission.get_by_id(self.parent_id)
                if parent:
                    self.path = f"{parent.path}/{self.id}"
                    self.level = parent.level + 1
                else:
                    self.path = str(self.id)
                    self.level = 0
            else:
                self.path = str(self.id)
                self.level = 0
                
            # 更新数据库
            sql = "UPDATE stock.permissions SET path = %s, level = %s WHERE id = %s"
            db.execute(sql, (self.path, self.level, self.id))
            
            # 递归更新子权限
            self._update_children_path()
            
            return True
        except Exception as e:
            logger.error(f"更新权限路径失败: {str(e)}")
            return False
    
    def _update_children_path(self):
        """递归更新子权限路径"""
        try:
            # 获取所有子权限
            children = Permission.get_children(self.id)
            
            for child in children:
                child.path = f"{self.path}/{child.id}"
                child.level = self.level + 1
                
                # 更新数据库
                sql = "UPDATE stock.permissions SET path = %s, level = %s WHERE id = %s"
                db.execute(sql, (child.path, child.level, child.id))
                
                # 递归更新子权限的子权限
                child._update_children_path()
                
            return True
        except Exception as e:
            logger.error(f"递归更新子权限路径失败: {str(e)}")
            return False
            
    def delete(self):
        """删除权限"""
        try:
            # 检查是否有子权限
            children = Permission.get_children(self.id)
            if children:
                logger.error(f"权限 {self.name} 有子权限，无法删除")
                return False
                
            # 先删除角色-权限关联
            sql_delete_role_permissions = """
                DELETE FROM stock.role_permissions WHERE permission_id = %s
            """
            db.execute(sql_delete_role_permissions, (self.id,))
            
            # 最后删除权限
            sql = "DELETE FROM stock.permissions WHERE id = %s"
            return db.execute(sql, (self.id,))
        except Exception as e:
            logger.error(f"删除权限失败: {str(e)}")
            return False
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'type': self.type,
            'parent_id': self.parent_id,
            'path': self.path,
            'level': self.level,
            'sort_order': self.sort_order,
            'is_menu': self.is_menu,
            'icon': self.icon,
            'component': self.component,
            'route_path': self.route_path,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        
    @staticmethod
    def get_all():
        """获取所有权限"""
        try:
            sql = "SELECT * FROM permissions ORDER BY sort_order, id"
            data = db.fetch_all(sql)
            return [Permission(item) for item in data]
        except Exception as e:
            logger.error(f"获取所有权限失败: {str(e)}")
            return []
            
    @staticmethod
    def get_by_id(permission_id):
        """根据ID获取权限"""
        try:
            sql = "SELECT * FROM permissions WHERE id = %s"
            data = db.fetch_one(sql, (permission_id,))
            return Permission(data) if data else None
        except Exception as e:
            logger.error(f"获取权限失败: {str(e)}")
            return None
            
    @staticmethod
    def get_by_code(code):
        """根据代码获取权限"""
        try:
            sql = "SELECT * FROM permissions WHERE code = %s"
            data = db.fetch_one(sql, (code,))
            return Permission(data) if data else None
        except Exception as e:
            logger.error(f"获取权限失败: {str(e)}")
            return None
            
    @staticmethod
    def get_role_permissions(role_id):
        """获取角色的所有权限"""
        try:
            sql = """
                SELECT p.* FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = %s
                ORDER BY p.sort_order, p.id
            """
            data = db.fetch_all(sql, (role_id,))
            return [Permission(item) for item in data]
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            return []
            
    @staticmethod
    def get_user_permissions(user_id):
        """获取用户的所有权限"""
        try:
            sql = """
                SELECT DISTINCT p.* FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY p.sort_order, p.id
            """
            data = db.fetch_all(sql, (user_id,))
            return [Permission(item) for item in data]
        except Exception as e:
            logger.error(f"获取用户权限失败: {str(e)}")
            return []
            
    @staticmethod
    def get_permission_tree():
        """获取权限树"""
        try:
            # 获取所有权限
            permissions = Permission.get_all()
            
            # 构建权限树
            tree = []
            permission_map = {}
            
            # 先构建映射
            for permission in permissions:
                permission_map[permission.id] = permission.to_dict()
                permission_map[permission.id]['children'] = []
                
            # 构建树结构
            for permission in permissions:
                if permission.parent_id is None or permission.parent_id == 0:
                    # 顶级权限
                    tree.append(permission_map[permission.id])
                else:
                    # 子权限
                    parent = permission_map.get(permission.parent_id)
                    if parent:
                        parent['children'].append(permission_map[permission.id])
                        
            return tree
        except Exception as e:
            logger.error(f"获取权限树失败: {str(e)}")
            return []
            
    @staticmethod
    def get_children(parent_id):
        """获取子权限"""
        try:
            sql = """
                SELECT * FROM stock.permissions 
                WHERE parent_id = %s
                ORDER BY sort_order, name
            """
            data = db.fetch_all(sql, (parent_id,))
            return [Permission(item) for item in data]
        except Exception as e:
            logger.error(f"获取子权限失败: {str(e)}")
            return []
            
    @staticmethod
    def get_by_path(path):
        """根据路径获取权限"""
        try:
            sql = "SELECT * FROM stock.permissions WHERE path = %s"
            data = db.fetch_one(sql, (path,))
            return Permission(data) if data else None
        except Exception as e:
            logger.error(f"根据路径获取权限失败: {str(e)}")
            return None

class RolePermission:
    """角色权限关联模型"""
    
    @staticmethod
    def assign_permissions_to_role(role_id, permission_ids):
        """为角色分配权限"""
        try:
            # 先删除角色的所有权限
            delete_sql = "DELETE FROM role_permissions WHERE role_id = %s"
            db.execute(delete_sql, (role_id,))
            
            # 如果没有权限需要分配，直接返回成功
            if not permission_ids:
                return True
                
            # 批量插入新权限
            values = []
            params = []
            
            for permission_id in permission_ids:
                values.append("(%s, %s)")
                params.extend([role_id, permission_id])
                
            if values:
                insert_sql = f"""
                    INSERT INTO role_permissions (role_id, permission_id)
                    VALUES {', '.join(values)}
                """
                return db.execute(insert_sql, params)
            
            return True
        except Exception as e:
            logger.error(f"为角色分配权限失败: {str(e)}")
            return False 