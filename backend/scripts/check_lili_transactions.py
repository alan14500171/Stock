#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import Database

def check_lili_transactions():
    """检查用户lili的交易记录和分单记录"""
    db = Database()
    
    # 获取lili用户ID
    user_sql = "SELECT id, username FROM stock.users WHERE username = 'lili'"
    user = db.fetch_one(user_sql)
    
    if not user:
        print("未找到用户lili")
        return
    
    user_id = user['id']
    print(f"用户lili的ID是: {user_id}")
    
    # 检查lili的交易记录
    transactions_sql = """
    SELECT id, market, stock_code, stock_name, transaction_type, transaction_date, 
           quantity, amount, user_id
    FROM stock.stock_transactions
    WHERE user_id = %s
    ORDER BY transaction_date DESC
    LIMIT 20
    """
    
    transactions = db.fetch_all(transactions_sql, [user_id])
    print(f"\n用户lili的交易记录数量: {len(transactions)}")
    for t in transactions:
        print(f"ID: {t['id']}, 市场: {t['market']}, 代码: {t['stock_code']}, "
              f"名称: {t['stock_name']}, 类型: {t['transaction_type']}, "
              f"日期: {t['transaction_date']}, 数量: {t['quantity']}, 金额: {t['amount']}")
    
    # 检查lili作为持有人的分单记录
    splits_as_holder_sql = """
    SELECT ts.id, ts.market, ts.stock_code, ts.stock_name, ts.transaction_type, 
           ts.transaction_date, ts.total_quantity, ts.total_amount, 
           ts.holder_id, ts.holder_name, t.user_id, u.username as owner_username
    FROM stock.transaction_splits ts
    JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
    JOIN stock.users u ON t.user_id = u.id
    WHERE ts.holder_id = %s
    ORDER BY ts.transaction_date DESC
    LIMIT 20
    """
    
    splits_as_holder = db.fetch_all(splits_as_holder_sql, [user_id])
    print(f"\n用户lili作为持有人的分单记录数量: {len(splits_as_holder)}")
    for s in splits_as_holder:
        print(f"ID: {s['id']}, 市场: {s['market']}, 代码: {s['stock_code']}, "
              f"名称: {s['stock_name']}, 类型: {s['transaction_type']}, "
              f"日期: {s['transaction_date']}, 数量: {s['total_quantity']}, 金额: {s['total_amount']}, "
              f"原始交易用户: {s['owner_username']} (ID: {s['user_id']})")
    
    # 检查lili作为交易创建者的分单记录
    splits_as_creator_sql = """
    SELECT ts.id, ts.market, ts.stock_code, ts.stock_name, ts.transaction_type, 
           ts.transaction_date, ts.total_quantity, ts.total_amount, 
           ts.holder_id, ts.holder_name, t.user_id, 
           h.username as holder_username
    FROM stock.transaction_splits ts
    JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
    LEFT JOIN stock.users h ON ts.holder_id = h.id
    WHERE t.user_id = %s AND ts.holder_id != %s
    ORDER BY ts.transaction_date DESC
    LIMIT 20
    """
    
    splits_as_creator = db.fetch_all(splits_as_creator_sql, [user_id, user_id])
    print(f"\n用户lili作为交易创建者的分单记录数量: {len(splits_as_creator)}")
    for s in splits_as_creator:
        holder_name = s['holder_username'] or s['holder_name']
        print(f"ID: {s['id']}, 市场: {s['market']}, 代码: {s['stock_code']}, "
              f"名称: {s['stock_name']}, 类型: {s['transaction_type']}, "
              f"日期: {s['transaction_date']}, 数量: {s['total_quantity']}, 金额: {s['total_amount']}, "
              f"持有人: {holder_name} (ID: {s['holder_id']})")
    
    # 检查交易编号P-892469的分单记录
    transaction_code_sql = """
    SELECT ts.id, ts.market, ts.stock_code, ts.stock_name, ts.transaction_type, 
           ts.transaction_date, ts.total_quantity, ts.total_amount, 
           ts.holder_id, ts.holder_name, t.user_id, t.transaction_code,
           u.username as owner_username, h.username as holder_username
    FROM stock.transaction_splits ts
    JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
    JOIN stock.users u ON t.user_id = u.id
    LEFT JOIN stock.users h ON ts.holder_id = h.id
    WHERE t.transaction_code = 'P-892469'
    ORDER BY ts.id
    """
    
    transaction_code_records = db.fetch_all(transaction_code_sql)
    print(f"\n交易编号P-892469的分单记录数量: {len(transaction_code_records)}")
    for r in transaction_code_records:
        holder_name = r['holder_username'] or r['holder_name']
        print(f"ID: {r['id']}, 市场: {r['market']}, 代码: {r['stock_code']}, "
              f"名称: {r['stock_name']}, 类型: {r['transaction_type']}, "
              f"日期: {r['transaction_date']}, 数量: {r['total_quantity']}, 金额: {r['total_amount']}, "
              f"交易创建者: {r['owner_username']} (ID: {r['user_id']}), "
              f"持有人: {holder_name} (ID: {r['holder_id']})")

if __name__ == "__main__":
    check_lili_transactions() 