#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查所有用户的交易记录和分单记录
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
from models.user import User

def check_transactions():
    """检查所有用户的交易记录和分单记录"""
    try:
        # 获取所有用户
        sql_users = "SELECT id, username FROM users"
        users = db.fetch_all(sql_users)
        
        print("用户交易记录统计:")
        print("=" * 50)
        
        for user in users:
            user_id = user['id']
            username = user['username']
            
            # 查询交易记录
            sql_trans = "SELECT COUNT(*) as count FROM stock_transactions WHERE user_id = %s"
            result_trans = db.fetch_one(sql_trans, [user_id])
            trans_count = result_trans['count'] if result_trans else 0
            
            # 查询分单记录
            sql_split = """
                SELECT COUNT(*) as count 
                FROM transaction_splits ts 
                JOIN stock_transactions t ON ts.original_transaction_id = t.id 
                WHERE t.user_id = %s
            """
            result_split = db.fetch_one(sql_split, [user_id])
            split_count = result_split['count'] if result_split else 0
            
            print(f"用户 {username} (ID: {user_id}):")
            print(f"  - 交易记录数: {trans_count}")
            print(f"  - 分单记录数: {split_count}")
            
            # 如果有分单记录，显示详细信息
            if split_count > 0:
                sql_split_details = """
                    SELECT 
                        ts.id, 
                        ts.market, 
                        ts.stock_code, 
                        ts.stock_name, 
                        ts.transaction_type, 
                        ts.transaction_date,
                        ts.total_quantity,
                        ts.total_amount
                    FROM transaction_splits ts 
                    JOIN stock_transactions t ON ts.original_transaction_id = t.id 
                    WHERE t.user_id = %s
                    ORDER BY ts.transaction_date DESC
                """
                split_details = db.fetch_all(sql_split_details, [user_id])
                
                print("  - 分单详情:")
                for detail in split_details:
                    print(f"    * ID: {detail['id']}, 市场: {detail['market']}, 代码: {detail['stock_code']}, 名称: {detail['stock_name']}")
                    print(f"      类型: {detail['transaction_type']}, 日期: {detail['transaction_date']}")
                    print(f"      数量: {detail['total_quantity']}, 金额: {detail['total_amount']}")
            
            print("-" * 50)
        
    except Exception as e:
        print(f"检查交易记录失败: {str(e)}")

if __name__ == "__main__":
    check_transactions() 