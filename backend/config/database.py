"""
数据库连接模块
"""
import pymysql
from pymysql.cursors import DictCursor
import logging
import time
import queue
import threading
from contextlib import contextmanager
from .db_config import get_db_config

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    def __init__(self, env='development', pool_size=5):
        self.config = get_db_config(env)
        self.pool_size = pool_size
        self.pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.active_connections = set()
        self.init_pool()
        
    def init_pool(self):
        """初始化连接池"""
        for _ in range(self.pool_size):
            conn = self.create_connection()
            if conn:
                self.pool.put(conn)
                
    def create_connection(self):
        """创建新的数据库连接"""
        try:
            connection = pymysql.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                port=self.config['port'],
                charset=self.config['charset'],
                cursorclass=DictCursor,
                autocommit=True,
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30,
                max_allowed_packet=16*1024*1024,
                program_name='StockApp',
                init_command='SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
            )
            
            # 初始化连接设置
            with connection.cursor() as cursor:
                cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
                cursor.execute("SET SESSION time_zone='+8:00'")
                cursor.execute("SET SESSION group_concat_max_len=1000000")
                cursor.execute("SET SESSION wait_timeout=28800")
                cursor.execute("SET SESSION interactive_timeout=28800")
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.execute("SET character_set_connection=utf8mb4")
                cursor.execute("SET collation_connection=utf8mb4_unicode_ci")
                
            return connection
        except Exception as e:
            logger.error(f"创建数据库连接失败: {str(e)}")
            return None
            
    def get_connection(self, timeout=5):
        """获取连接，如果池中没有可用连接则等待"""
        try:
            connection = self.pool.get(timeout=timeout)
            try:
                connection.ping(reconnect=True)
                self.active_connections.add(connection)
                return connection
            except:
                # 如果连接已失效，创建新连接
                connection = self.create_connection()
                if connection:
                    self.active_connections.add(connection)
                    return connection
                raise
        except queue.Empty:
            # 如果等待超时，创建新连接
            connection = self.create_connection()
            if connection:
                self.active_connections.add(connection)
                return connection
            raise Exception("无法获取数据库连接")
            
    def return_connection(self, connection):
        """归还连接到连接池"""
        if connection:
            try:
                connection.ping(reconnect=True)
                self.pool.put(connection, timeout=1)
            except:
                try:
                    connection.close()
                except:
                    pass
                # 创建新连接补充到池中
                new_conn = self.create_connection()
                if new_conn:
                    self.pool.put(new_conn, timeout=1)
            finally:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

    def close_all(self):
        """关闭所有连接"""
        # 关闭活动连接
        for conn in list(self.active_connections):
            try:
                conn.close()
                self.active_connections.remove(conn)
            except:
                pass

        # 清空连接池
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                try:
                    conn.close()
                except:
                    pass
            except queue.Empty:
                break

class Database:
    def __init__(self, env='development'):
        self.pool = None
        self.max_retries = 3
        self.retry_delay = 1
        self.env = env
        
    def init_pool(self, env=None):
        """初始化连接池"""
        if env:
            self.env = env
        self.pool = DatabaseConnectionPool(env=self.env, pool_size=5)
        
    def ensure_pool(self):
        """确保连接池已初始化"""
        if not self.pool:
            self.init_pool()

    def is_connected(self):
        """检查数据库连接状态"""
        if not self.pool:
            return False
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {str(e)}")
            return False

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        finally:
            if connection:
                self.pool.return_connection(connection)
            
    def execute(self, sql, params=None):
        """执行SQL语句"""
        self.ensure_pool()
        for attempt in range(self.max_retries):
            with self.get_connection() as connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(sql, params or ())
                        connection.commit()
                        return True
                except Exception as e:
                    logger.error(f"SQL执行尝试 {attempt + 1} 失败: {str(e)}")
                    try:
                        connection.rollback()
                    except:
                        pass
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return False
        return False
        
    def fetch_one(self, sql, params=None):
        """查询单条记录"""
        self.ensure_pool()
        for attempt in range(self.max_retries):
            with self.get_connection() as connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(sql, params or ())
                        return cursor.fetchone()
                except Exception as e:
                    logger.error(f"查询尝试 {attempt + 1} 失败: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
        return None
        
    def fetch_all(self, sql, params=None):
        """查询多条记录"""
        self.ensure_pool()
        for attempt in range(self.max_retries):
            with self.get_connection() as connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(sql, params or ())
                        return cursor.fetchall()
                except Exception as e:
                    logger.error(f"查询尝试 {attempt + 1} 失败: {str(e)}")
                    logger.error(f"SQL: {sql}")
                    logger.error(f"参数: {params}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return []
        return []
        
    def insert(self, sql, params=None):
        """插入记录"""
        self.ensure_pool()
        for attempt in range(self.max_retries):
            with self.get_connection() as connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(sql, params or ())
                        last_id = cursor.lastrowid
                        connection.commit()
                        return last_id
                except Exception as e:
                    logger.error(f"插入尝试 {attempt + 1} 失败: {str(e)}")
                    try:
                        connection.rollback()
                    except:
                        pass
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
        return None

    def close(self):
        """关闭数据库连接池"""
        if self.pool:
            self.pool.close_all()

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