#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db

def get_all_stock_positions():
    """获取所有不同的用户股票持仓"""
    sql = """
        SELECT DISTINCT user_id, stock_code, market
        FROM stock.stock_transactions
        ORDER BY user_id, market, stock_code
    """
    return db.fetch_all(sql)

def calculate_transaction_fees(transaction):
    """计算交易的总费用"""
    fees = [
        'broker_fee', 'transaction_levy', 'stamp_duty',
        'trading_fee', 'deposit_fee'
    ]
    return sum(Decimal(str(transaction.get(fee) or 0)) for fee in fees)

def calculate_net_amount(transaction, total_fees):
    """计算交易的净金额"""
    total_amount = Decimal(str(transaction['total_amount']))
    if transaction['transaction_type'].lower() == 'buy':
        return total_amount + total_fees
    else:
        return total_amount - total_fees

def recalculate_position(user_id, stock_code, market):
    """重新计算指定用户的指定股票的所有交易记录"""
    try:
        # 获取该股票的所有交易记录
        sql = """
            SELECT *
            FROM stock.stock_transactions
            WHERE user_id = %s
                AND stock_code = %s
                AND market = %s
            ORDER BY transaction_date, id
        """
        transactions = db.fetch_all(sql, [user_id, stock_code, market])
        
        if not transactions:
            return True
        
        # 开始事务
        db.execute("START TRANSACTION")
        
        try:
            current_quantity = Decimal('0')
            current_cost = Decimal('0')
            current_avg_cost = Decimal('0')
            
            for trans in transactions:
                # 保存更新前的状态
                prev_quantity = current_quantity
                prev_cost = current_cost
                
                # 计算总费用
                total_fees = calculate_transaction_fees(trans)
                
                # 计算净金额
                net_amount = calculate_net_amount(trans, total_fees)
                
                # 获取交易数量和金额
                total_quantity = Decimal(str(trans['total_quantity']))
                total_amount = Decimal(str(trans['total_amount']))
                
                # 初始化已实现盈亏和盈亏比率
                realized_profit = Decimal('0')
                profit_rate = Decimal('0')
                
                # 更新持仓状态
                if trans['transaction_type'].upper() == 'BUY':
                    current_quantity += total_quantity
                    current_cost += total_amount + total_fees
                else:  # SELL
                    # 计算已实现盈亏
                    if prev_quantity > 0:
                        avg_cost = prev_cost / prev_quantity
                        cost_basis = avg_cost * total_quantity
                        realized_profit = total_amount - cost_basis - total_fees
                        profit_rate = ((realized_profit / cost_basis) * 100
                                     if cost_basis > 0 else Decimal('0'))
                    
                    current_quantity -= total_quantity
                    if current_quantity > 0:
                        current_cost = current_cost * (current_quantity / prev_quantity)
                    else:
                        current_cost = Decimal('0')
                
                # 格式化数值，保留2位小数
                values = [
                    total_fees, net_amount,
                    current_quantity, current_cost,
                    realized_profit, profit_rate
                ]
                values = [v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) for v in values]
                
                # 更新数据库
                update_sql = """
                    UPDATE stock.stock_transactions
                    SET total_fees = %s,
                        net_amount = %s,
                        running_quantity = %s,
                        running_cost = %s,
                        realized_profit = %s,
                        profit_rate = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """
                db.execute(update_sql, values + [trans['id']])
            
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
    # 获取所有不同的持仓
    positions = get_all_stock_positions()
    success = 0
    failed = 0
    
    # 逐个重新计算
    for pos in positions:
        if recalculate_position(pos['user_id'], pos['stock_code'], pos['market']):
            success += 1
        else:
            failed += 1

if __name__ == '__main__':
    main() 