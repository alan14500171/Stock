#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db

def get_affected_transactions(user_id=None, stock_code=None, market=None, transaction_date=None):
    """
    获取受影响的交易记录
    
    Args:
        user_id: 用户ID
        stock_code: 股票代码
        market: 市场
        transaction_date: 交易日期
        
    Returns:
        list: 交易记录列表
    """
    sql = """
        SELECT id, current_quantity, current_cost
        FROM stock.stock_transactions
        WHERE 1=1
    """
    params = []
    
    if user_id:
        sql += " AND user_id = %s"
        params.append(user_id)
        
    if stock_code:
        sql += " AND stock_code = %s"
        params.append(stock_code)
        
    if market:
        sql += " AND market = %s"
        params.append(market)
        
    if transaction_date:
        sql += " AND transaction_date >= %s"
        params.append(transaction_date)
        
    sql += " ORDER BY transaction_date, id"
    
    return db.fetch_all(sql, params)

def update_running_fields(user_id=None, stock_code=None, market=None, transaction_date=None):
    """
    更新交易记录的running_quantity和running_cost字段
    
    Args:
        user_id: 用户ID，如果提供则只更新该用户的记录
        stock_code: 股票代码，如果提供则只更新该股票的记录
        market: 市场，如果提供则只更新该市场的记录
        transaction_date: 交易日期，如果提供则只更新该日期及之后的记录
        
    Returns:
        bool: 是否成功
    """
    try:
        # 获取需要更新的交易记录
        transactions = get_affected_transactions(user_id, stock_code, market, transaction_date)
        
        if not transactions:
            return True
        
        # 开始事务
        db.execute("START TRANSACTION")
        
        try:
            success = 0
            failed = 0
            
            for trans in transactions:
                try:
                    # 更新running_quantity和running_cost字段
                    update_sql = """
                        UPDATE stock.stock_transactions
                        SET running_quantity = %s,
                            running_cost = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    
                    result = db.execute(update_sql, [
                        trans['current_quantity'],
                        trans['current_cost'],
                        trans['id']
                    ])
                    
                    if result:
                        success += 1
                    else:
                        failed += 1
                        
                except Exception:
                    failed += 1
            
            # 提交事务
            db.execute("COMMIT")
            return True
            
        except Exception:
            db.execute("ROLLBACK")
            return False
            
    except Exception:
        return False

def main():
    """主函数"""
    # 如果命令行参数提供了过滤条件，则使用过滤条件
    user_id = None
    stock_code = None
    market = None
    transaction_date = None
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--user='):
                user_id = arg.split('=')[1]
            elif arg.startswith('--stock='):
                stock_code = arg.split('=')[1]
            elif arg.startswith('--market='):
                market = arg.split('=')[1]
            elif arg.startswith('--date='):
                transaction_date = arg.split('=')[1]
    
    update_running_fields(user_id, stock_code, market, transaction_date)

if __name__ == '__main__':
    main() 