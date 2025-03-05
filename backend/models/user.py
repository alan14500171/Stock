"""
用户模型
"""
from datetime import datetime
import bcrypt
from config.database import db
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.username = data.get('username') if data else None
        self.password_hash = data.get('password_hash') if data else None
        self.name = data.get('name') if data else None
        self.email = data.get('email') if data else None
        self.is_active = data.get('is_active', True) if data else True
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        self.last_login = data.get('last_login') if data else None
        
    def set_password(self, password):
        """设置密码"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        self.password_hash = hashed.decode('utf-8')
        
    def check_password(self, password):
        """验证密码"""
        try:
            if not self.password_hash:
                return False
            
            # 检查是否是 Werkzeug 格式的哈希（以 pbkdf2:sha256: 或 sha1$ 等开头）
            if self.password_hash.startswith(('pbkdf2:', 'sha1$', 'sha256$', 'md5$')):
                try:
                    # 使用 Werkzeug 验证
                    from werkzeug.security import check_password_hash
                    result = check_password_hash(self.password_hash, password)
                    
                    # 如果验证成功，将密码转换为 bcrypt 格式
                    if result:
                        logger.info(f"用户 {self.username} 使用 Werkzeug 格式密码验证成功，正在转换为 bcrypt 格式")
                        self.set_password(password)
                        self.save()
                    return result
                except ValueError as e:
                    logger.error(f"Werkzeug 密码验证失败: {str(e)}")
                    return False
            else:
                # 使用 bcrypt 验证
                if isinstance(password, str):
                    password = password.encode('utf-8')
                    
                stored_hash = self.password_hash
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode('utf-8')
                    
                return bcrypt.checkpw(password, stored_hash)
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False
        
    def save(self):
        """保存用户"""
        try:
            if self.id:
                # 更新
                sql = """
                    UPDATE stock.users 
                    SET username = %s, password_hash = %s, 
                        display_name = %s, email = %s,
                        is_active = %s, last_login = %s 
                    WHERE id = %s
                """
                params = (
                    self.username, self.password_hash,
                    self.name, self.email,
                    self.is_active, self.last_login, self.id
                )
                return db.execute(sql, params)
            else:
                # 新增
                sql = """
                    INSERT INTO stock.users 
                    (username, password_hash, display_name, email, is_active, created_at) 
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """
                params = (
                    self.username, self.password_hash,
                    self.name, self.email,
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
            'name': self.name or '',
            'email': self.email or '',
            'is_active': bool(self.is_active),
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