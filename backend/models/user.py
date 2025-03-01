"""
用户模型
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import db
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.username = data.get('username') if data else None
        self.password_hash = data.get('password_hash') if data else None
        self.is_active = data.get('is_active', True) if data else True
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        self.last_login = data.get('last_login') if data else None
        
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
        
    def save(self):
        """保存用户"""
        try:
            if self.id:
                # 更新
                sql = """
                    UPDATE stock.users 
                    SET username = %s, password_hash = %s, 
                        is_active = %s, last_login = %s 
                    WHERE id = %s
                """
                params = (
                    self.username, self.password_hash,
                    self.is_active, self.last_login, self.id
                )
                return db.execute(sql, params)
            else:
                # 新增
                sql = """
                    INSERT INTO stock.users 
                    (username, password_hash, is_active, created_at) 
                    VALUES (%s, %s, %s, NOW())
                """
                params = (
                    self.username, self.password_hash,
                    self.is_active
                )
                self.id = db.insert(sql, params)
                return bool(self.id)
        except Exception as e:
            logger.error(f"保存用户失败: {str(e)}")
            return False
            
    def update_last_login(self):
        """更新最后登录时间"""
        try:
            self.last_login = datetime.utcnow()
            sql = "UPDATE stock.users SET last_login = %s WHERE id = %s"
            return db.execute(sql, (self.last_login, self.id))
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {str(e)}")
            return False
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
    @staticmethod
    def get_by_id(user_id):
        """根据ID获取用户"""
        try:
            sql = "SELECT * FROM stock.users WHERE id = %s"
            data = db.fetch_one(sql, (user_id,))
            return User(data) if data else None
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None
        
    @staticmethod
    def find_by_username(username):
        """根据用户名查找用户"""
        try:
            sql = "SELECT * FROM stock.users WHERE username = %s"
            data = db.fetch_one(sql, (username,))
            return User(data) if data else None
        except Exception as e:
            logger.error(f"查找用户失败: {str(e)}")
            return None
        
    def get_id(self):
        """Flask-Login需要的方法"""
        return str(self.id)
        
    @property
    def is_authenticated(self):
        """Flask-Login需要的属性"""
        return True
        
    @property
    def is_anonymous(self):
        """Flask-Login需要的属性"""
        return False 