#!/usr/bin/env python3
"""
数据库连接检查脚本
用于诊断数据库连接问题
"""
import os
import sys
import time
import socket
import pymysql
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 导入数据库配置
from config.db_config import get_db_config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_host_connectivity(host, port):
    """检查主机连通性"""
    try:
        # 尝试ping主机
        response = os.system(f"ping -c 1 -W 1 {host} > /dev/null 2>&1")
        if response == 0:
            logger.info(f"✅ 主机 {host} 可以ping通")
        else:
            logger.warning(f"⚠️ 主机 {host} 无法ping通，但这不一定意味着数据库不可访问")
        
        # 尝试TCP连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info(f"✅ 端口 {host}:{port} 可以连接")
            return True
        else:
            logger.error(f"❌ 端口 {host}:{port} 无法连接")
            return False
    except Exception as e:
        logger.error(f"❌ 检查主机连通性时出错: {str(e)}")
        return False

def list_databases(config):
    """列出所有数据库"""
    try:
        # 连接到MySQL/MariaDB服务器，不指定数据库
        logger.info(f"尝试连接到数据库服务器: {config['host']}:{config['port']}")
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset=config['charset'],
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            # 列出所有数据库
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            
            logger.info("可用的数据库:")
            for db in databases:
                logger.info(f"  - {db[0]}")
                
            # 检查目标数据库是否存在（不区分大小写）
            target_db = config['db']
            found = False
            actual_db_name = None
            
            for db in databases:
                if db[0].lower() == target_db.lower():
                    found = True
                    actual_db_name = db[0]
                    break
            
            if found:
                if actual_db_name == target_db:
                    logger.info(f"✅ 数据库 '{target_db}' 存在")
                else:
                    logger.warning(f"⚠️ 数据库存在，但大小写不一致: 配置中为 '{target_db}'，实际为 '{actual_db_name}'")
            else:
                logger.error(f"❌ 数据库 '{target_db}' 不存在")
        
        conn.close()
        return found, actual_db_name
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:  # Access denied
            logger.error(f"❌ 访问被拒绝: 用户名或密码错误 - {str(e)}")
        elif error_code == 2003:  # Can't connect
            logger.error(f"❌ 无法连接到数据库服务器: {str(e)}")
        else:
            logger.error(f"❌ 数据库操作错误: {str(e)}")
        return False, None
    except Exception as e:
        logger.error(f"❌ 列出数据库时出错: {str(e)}")
        return False, None

def check_user_permissions(config, db_name=None):
    """检查用户权限"""
    try:
        # 如果提供了数据库名称，则使用它
        if db_name:
            use_db_name = db_name
        else:
            use_db_name = config['db']
        
        # 连接到MySQL/MariaDB服务器，指定数据库
        logger.info(f"尝试连接到数据库: {config['host']}:{config['port']}/{use_db_name}")
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            db=use_db_name,
            charset=config['charset'],
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            # 检查用户权限
            cursor.execute("SHOW GRANTS")
            grants = cursor.fetchall()
            
            logger.info(f"用户 '{config['user']}' 的权限:")
            for grant in grants:
                logger.info(f"  - {grant[0]}")
            
            # 尝试执行简单查询
            try:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    logger.info(f"✅ 用户 '{config['user']}' 可以在数据库 '{use_db_name}' 上执行查询")
                    
                    # 检查表结构
                    try:
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        if tables:
                            logger.info(f"数据库 '{use_db_name}' 中的表:")
                            for table in tables:
                                logger.info(f"  - {table[0]}")
                        else:
                            logger.warning(f"⚠️ 数据库 '{use_db_name}' 中没有表")
                    except Exception as e:
                        logger.error(f"❌ 无法列出表: {str(e)}")
                    
                    return True
            except Exception as e:
                logger.error(f"❌ 用户 '{config['user']}' 无法在数据库 '{use_db_name}' 上执行查询: {str(e)}")
                return False
        
        conn.close()
        return True
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:  # Access denied
            logger.error(f"❌ 访问被拒绝: 用户名或密码错误 - {str(e)}")
        elif error_code == 1049:  # Unknown database
            logger.error(f"❌ 未知数据库 '{db_name}': {str(e)}")
        else:
            logger.error(f"❌ 数据库操作错误: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ 检查用户权限时出错: {str(e)}")
        return False

def try_create_database(config):
    """尝试创建数据库"""
    try:
        # 连接到MySQL/MariaDB服务器，不指定数据库
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset=config['charset'],
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            # 尝试创建数据库
            db_name = config['db']
            logger.info(f"尝试创建数据库 '{db_name}'...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"✅ 成功创建数据库 '{db_name}'")
            return True
        
        conn.close()
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:  # Access denied
            logger.error(f"❌ 无法创建数据库: 权限不足 - {str(e)}")
        else:
            logger.error(f"❌ 创建数据库时出错: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ 创建数据库时出错: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='检查数据库连接')
    parser.add_argument('--env', default='production', help='环境 (development, production)')
    parser.add_argument('--create', action='store_true', help='如果数据库不存在，尝试创建')
    args = parser.parse_args()
    
    logger.info(f"正在检查 {args.env} 环境的数据库连接...")
    
    # 获取数据库配置
    config = get_db_config(args.env)
    logger.info(f"数据库配置: {config}")
    
    # 检查主机连通性
    if not check_host_connectivity(config['host'], config['port']):
        logger.error("❌ 无法连接到数据库主机，请检查网络配置")
        return
    
    # 列出数据库
    db_exists, actual_db_name = list_databases(config)
    
    # 如果数据库不存在且指定了创建选项，尝试创建
    if not db_exists and args.create:
        if try_create_database(config):
            db_exists = True
            actual_db_name = config['db']
    
    # 检查用户权限
    if db_exists:
        check_user_permissions(config, actual_db_name)
    
    logger.info("数据库连接检查完成")

if __name__ == "__main__":
    main() 