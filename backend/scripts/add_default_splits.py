#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
为数据库中已有的交易数据添加默认分单记录
使用方法：python add_default_splits.py
"""

import sys
import os
import logging
import pymysql
from datetime import datetime
import decimal

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import get_db_connection
from config.database import db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/add_default_splits_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)

def ensure_log_directory():
    """确保日志目录存在"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

def get_transactions_without_splits():
    """获取没有分单记录的交易"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询没有分单记录的交易
        query = """
        SELECT t.*, s.code_name as stock_name, u.id as user_id
        FROM stock_transactions t
        LEFT JOIN stocks s ON t.stock_code = s.code AND t.market = s.market
        LEFT JOIN users u ON t.user_id = u.id
        WHERE NOT EXISTS (
            SELECT 1 FROM transaction_splits ts 
            WHERE ts.original_transaction_id = t.id
        )
        ORDER BY t.transaction_date, t.id
        """
        
        cursor.execute(query)
        transactions = cursor.fetchall()
        
        logger.info(f"找到 {len(transactions)} 条没有分单记录的交易")
        return transactions
    
    except Exception as e:
        logger.error(f"获取交易记录失败: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_default_holder(user_id):
    """获取用户的默认持有人"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询用户的默认持有人（取第一个）
        query = """
        SELECT id, name FROM holders 
        WHERE user_id = %s 
        LIMIT 1
        """
        
        cursor.execute(query, (user_id,))
        holder = cursor.fetchone()
        
        if not holder:
            logger.warning(f"用户 {user_id} 没有关联的持有人")
        
        return holder
    
    except Exception as e:
        logger.error(f"获取默认持有人失败: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_holder_holdings(holder_id, stock_code, market):
    """获取持有人的持仓信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询持有人的持仓信息
        query = """
        SELECT 
            SUM(CASE WHEN transaction_type = 'buy' THEN total_quantity ELSE -total_quantity END) as current_quantity,
            SUM(CASE WHEN transaction_type = 'buy' THEN total_amount ELSE -total_amount END) as current_cost
        FROM transaction_splits
        WHERE holder_id = %s AND stock_code = %s AND market = %s
        GROUP BY holder_id, stock_code, market
        """
        
        cursor.execute(query, (holder_id, stock_code, market))
        holding = cursor.fetchone()
        
        return holding
    
    except Exception as e:
        logger.error(f"获取持仓信息失败: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_default_split(transaction, holder):
    """为交易创建默认分单记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取持有人当前持仓信息
        holding = get_holder_holdings(holder['id'], transaction['stock_code'], transaction['market'])
        
        # 初始化持仓相关变量
        prev_quantity = 0
        prev_cost = 0
        prev_avg_cost = 0
        current_quantity = 0
        current_cost = 0
        current_avg_cost = 0
        running_quantity = 0
        running_cost = 0
        realized_profit = 0
        profit_rate = 0
        
        # 如果有持仓数据，计算相关字段
        if holding:
            prev_quantity = float(holding.get('current_quantity', 0) or 0)
            prev_cost = float(holding.get('current_cost', 0) or 0)
            
            # 计算平均成本
            if prev_quantity > 0:
                prev_avg_cost = prev_cost / prev_quantity
            
            # 根据交易类型计算交易后持仓
            if transaction['transaction_type'].lower() == 'buy':
                current_quantity = prev_quantity + float(transaction['total_quantity'])
                current_cost = prev_cost + float(transaction['total_amount'])
                
                # 计算新的平均成本
                if current_quantity > 0:
                    current_avg_cost = current_cost / current_quantity
                
                running_quantity = current_quantity
                running_cost = current_cost
            else:  # sell
                current_quantity = prev_quantity - float(transaction['total_quantity'])
                
                # 计算已实现盈亏
                if prev_quantity > 0 and prev_avg_cost > 0:
                    realized_profit = float(transaction['total_amount']) - (float(transaction['total_quantity']) * prev_avg_cost)
                    profit_rate = (realized_profit / (float(transaction['total_quantity']) * prev_avg_cost)) * 100
                
                # 计算剩余成本
                if prev_quantity > 0:
                    current_cost = prev_cost * (current_quantity / prev_quantity)
                else:
                    current_cost = 0
                
                # 保持平均成本不变
                current_avg_cost = prev_avg_cost
                
                running_quantity = current_quantity
                running_cost = current_cost
        else:
            # 如果没有持仓数据，根据交易类型初始化
            if transaction['transaction_type'].lower() == 'buy':
                current_quantity = float(transaction['total_quantity'])
                current_cost = float(transaction['total_amount'])
                
                if current_quantity > 0:
                    current_avg_cost = current_cost / current_quantity
                
                running_quantity = current_quantity
                running_cost = current_cost
            else:  # sell
                # 卖出但没有持仓，这是一种异常情况
                logger.warning(f"异常情况: 持有人{holder['name']}卖出股票{transaction['stock_code']}但没有持仓记录")
                
                # 仍然记录为负持仓
                current_quantity = -float(transaction['total_quantity'])
                current_cost = -float(transaction['total_amount'])
                current_avg_cost = 0
                running_quantity = current_quantity
                running_cost = current_cost
        
        # 计算总费用
        total_fees = (
            float(transaction.get('broker_fee', 0) or 0) +
            float(transaction.get('stamp_duty', 0) or 0) +
            float(transaction.get('transaction_levy', 0) or 0) +
            float(transaction.get('trading_fee', 0) or 0) +
            float(transaction.get('deposit_fee', 0) or 0)
        )
        
        # 计算净金额
        if transaction['transaction_type'].lower() == 'buy':
            net_amount = float(transaction['total_amount']) + total_fees
        else:  # sell
            net_amount = float(transaction['total_amount']) - total_fees
        
        # 插入分单记录
        insert_query = """
        INSERT INTO transaction_splits (
            original_transaction_id, holder_id, holder_name, split_ratio,
            transaction_date, stock_id, stock_code, stock_name, market,
            transaction_code, transaction_type, total_amount, total_quantity,
            broker_fee, stamp_duty, transaction_levy, trading_fee, deposit_fee,
            prev_quantity, prev_cost, prev_avg_cost,
            current_quantity, current_cost, current_avg_cost,
            total_fees, net_amount, running_quantity, running_cost,
            realized_profit, profit_rate, exchange_rate, remarks
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        cursor.execute(insert_query, (
            transaction['id'], holder['id'], holder['name'], 1.0,  # 100%的分配比例
            transaction['transaction_date'], transaction.get('stock_id', 0), 
            transaction['stock_code'], transaction['stock_name'], 
            transaction['market'], transaction['transaction_code'],
            transaction['transaction_type'], transaction['total_amount'], transaction['total_quantity'],
            transaction.get('broker_fee', 0), transaction.get('stamp_duty', 0), 
            transaction.get('transaction_levy', 0), transaction.get('trading_fee', 0), 
            transaction.get('deposit_fee', 0), 
            prev_quantity, prev_cost, prev_avg_cost,
            current_quantity, current_cost, current_avg_cost,
            total_fees, net_amount, running_quantity, running_cost,
            realized_profit, profit_rate,
            transaction.get('exchange_rate', 1.0), 
            "系统自动创建的100%分单"
        ))
        
        # 提交事务
        conn.commit()
        
        logger.info(f"为交易 {transaction['id']} 创建了默认分单记录")
        return True
    
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"创建默认分单记录失败: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """主函数"""
    ensure_log_directory()
    logger.info("开始为交易数据添加默认分单记录")
    
    # 获取没有分单记录的交易
    transactions = get_transactions_without_splits()
    
    if not transactions:
        logger.info("没有找到需要添加分单记录的交易")
        return
    
    # 为每个交易创建默认分单记录
    success_count = 0
    fail_count = 0
    
    for transaction in transactions:
        # 获取用户的默认持有人
        holder = get_default_holder(transaction['user_id'])
        
        if not holder:
            logger.warning(f"交易 {transaction['id']} 的用户 {transaction['user_id']} 没有关联的持有人，跳过")
            fail_count += 1
            continue
        
        # 创建默认分单记录
        if create_default_split(transaction, holder):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"处理完成: 成功 {success_count} 条, 失败 {fail_count} 条")

if __name__ == "__main__":
    main() 