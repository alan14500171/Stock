"""
数据库连接模块
"""
import pymysql
from pymysql.cursors import DictCursor
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        
    def connect(self, config):
        """创建数据库连接"""
        try:
            if self.connection and self.connection.open:
                try:
                    self.connection.ping(reconnect=True)
                    return True
                except:
                    self.connection.close()
                
            self.connection = pymysql.connect(
                host=config.get('host', '172.16.0.109'),
                user=config.get('user', 'root'),
                password=config.get('password', 'Zxc000123'),
                database=config.get('database', 'Stock'),
                port=config.get('port', 3306),
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=False,
                connect_timeout=10,
                read_timeout=30,
                write_timeout=30,
                max_allowed_packet=16*1024*1024,
                program_name='StockApp',
                init_command='SET SESSION time_zone="+8:00"'
            )
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
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
            
    def ensure_connection(self):
        """确保数据库连接有效"""
        try:
            if not self.connection or not self.connection.open:
                return self.connect({})
            try:
                self.connection.ping(reconnect=True)
                return True
            except:
                self.connection.close()
                return self.connect({})
        except Exception as e:
            logger.error(f"数据库重连失败: {str(e)}")
            return False
            
    def execute(self, sql, params=None):
        """执行SQL语句"""
        if not self.ensure_connection():
            return False
        cursor = None
        try:
            cursor = self.get_cursor()
            if not cursor:
                return False
            cursor.execute(sql, params or ())
            self.connection.commit()
            return True
        except Exception as e:
            if self.connection and self.connection.open:
                self.connection.rollback()
            logger.error(f"SQL执行失败: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            
    def fetch_one(self, sql, params=None):
        """查询单条记录"""
        if not self.ensure_connection():
            return None
        cursor = None
        try:
            cursor = self.get_cursor()
            if not cursor:
                return None
            cursor.execute(sql, params or ())
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            
    def fetch_all(self, sql, params=None):
        """查询多条记录"""
        if not self.ensure_connection():
            return []
        cursor = None
        try:
            cursor = self.get_cursor()
            if not cursor:
                return []
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            
    def insert(self, sql, params=None):
        """插入记录"""
        if not self.ensure_connection():
            return None
        cursor = self.get_cursor()
        if not cursor:
            return None
        try:
            cursor.execute(sql, params or ())
            last_id = cursor.lastrowid
            self.connection.commit()
            return last_id
        except Exception as e:
            if self.connection and self.connection.open:
                self.connection.rollback()
            logger.error(f"插入失败: {str(e)}")
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