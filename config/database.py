"""
数据库连接模块
"""
import pymysql
from pymysql.cursors import DictCursor

class Database:
    def __init__(self):
        self.connection = None
        
    def connect(self, config):
        """创建数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=config.get('host', '172.16.0.109'),
                user=config.get('user', 'root'),
                password=config.get('password', 'Zxc000123'),
                database=config.get('database', 'Stock'),
                port=config.get('port', 3306),
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=True
            )
            return True
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            return False
            
    def get_cursor(self):
        """获取数据库游标"""
        if not self.connection:
            return None
        return self.connection.cursor()
        
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            
    def execute(self, sql, params=None):
        """执行SQL语句"""
        cursor = self.get_cursor()
        if not cursor:
            return False
        try:
            cursor.execute(sql, params or ())
            return True
        except Exception as e:
            print(f"SQL执行失败: {str(e)}")
            return False
        finally:
            cursor.close()
            
    def fetch_one(self, sql, params=None):
        """查询单条记录"""
        cursor = self.get_cursor()
        if not cursor:
            return None
        try:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
        except Exception as e:
            print(f"查询失败: {str(e)}")
            return None
        finally:
            cursor.close()
            
    def fetch_all(self, sql, params=None):
        """查询多条记录"""
        cursor = self.get_cursor()
        if not cursor:
            return []
        try:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        except Exception as e:
            print(f"查询失败: {str(e)}")
            return []
        finally:
            cursor.close()
            
    def insert(self, sql, params=None):
        """插入记录"""
        cursor = self.get_cursor()
        if not cursor:
            return None
        try:
            cursor.execute(sql, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            self.connection.rollback()
            print(f"插入失败: {str(e)}")
            return None
        finally:
            cursor.close()

# 创建全局数据库实例
db = Database()

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
def get_db_session(app):
    """获取数据库会话"""
    return db.session 