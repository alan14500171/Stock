#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.db import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_user_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. 检查用户信息
        logger.info("检查用户信息...")
        cursor.execute("""
            SELECT id, username, display_name, is_active 
            FROM users 
            WHERE username = 'lili'
        """)
        user = cursor.fetchone()
        if user:
            logger.info(f"用户信息: {user}")
            user_id = user['id']
            
            # 2. 检查持有人信息
            logger.info("\n检查持有人信息...")
            cursor.execute("""
                SELECT id, name, user_id, status 
                FROM holders 
                WHERE user_id = %s OR name = 'lili'
            """, (user_id,))
            holders = cursor.fetchall()
            logger.info(f"关联的持有人: {holders}")
            
            # 3. 检查分单记录
            logger.info("\n检查分单记录...")
            cursor.execute("""
                SELECT ts.*, h.name as holder_name, h.user_id as holder_user_id,
                       st.transaction_code, st.user_id as transaction_user_id
                FROM transaction_splits ts
                JOIN holders h ON ts.holder_id = h.id
                JOIN stock_transactions st ON ts.original_transaction_id = st.id
                WHERE h.user_id = %s
            """, (user_id,))
            splits = cursor.fetchall()
            logger.info(f"相关的分单记录: {splits}")
            
        else:
            logger.error("未找到用户 lili")
            
    except Exception as e:
        logger.error(f"检查数据时发生错误: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    check_user_data() 