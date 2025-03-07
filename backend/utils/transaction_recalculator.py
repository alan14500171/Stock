#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易记录重新计算工具

该模块提供了重新计算transaction_splits表中字段的功能，
可以在添加交易记录、修改交易记录、删除交易记录、交易记录分单后调用，
确保所有相关字段的计算准确性。
"""

import logging
import pymysql
from datetime import datetime
import decimal
from collections import defaultdict
import os

from utils.db import get_db_connection

# 配置日志
logger = logging.getLogger(__name__)

def ensure_log_directory():
    """确保日志目录存在"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

def get_transaction_splits(holder_id=None, stock_code=None, market=None, start_date=None, transaction_id=None):
    """
    获取交易分单记录，按持有人、股票、交易日期和ID排序
    
    Args:
        holder_id (int, optional): 持有人ID
        stock_code (str, optional): 股票代码
        market (str, optional): 市场
        start_date (date, optional): 开始日期
        transaction_id (int, optional): 交易ID
        
    Returns:
        list: 交易分单记录列表
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if transaction_id:
            # 获取指定交易的信息，用于确定后续查询条件
            cursor.execute("""
                SELECT holder_id, market, stock_code, transaction_date 
                FROM transaction_splits 
                WHERE id = %s
            """, [transaction_id])
            transaction = cursor.fetchone()
            
            if not transaction:
                logger.error(f"未找到ID为 {transaction_id} 的交易记录")
                return []
            
            # 使用该交易的信息查询同一持有人同一股票在该日期及之后的所有交易
            where_clauses.append("ts.holder_id = %s")
            where_clauses.append("ts.market = %s")
            where_clauses.append("ts.stock_code = %s")
            where_clauses.append("(ts.transaction_date >= %s)")
            params.extend([
                transaction['holder_id'], 
                transaction['market'], 
                transaction['stock_code'], 
                transaction['transaction_date']
            ])
        else:
            # 根据提供的筛选条件构建查询
            if holder_id:
                where_clauses.append("ts.holder_id = %s")
                params.append(holder_id)
            
            if stock_code and market:
                where_clauses.append("ts.stock_code = %s")
                where_clauses.append("ts.market = %s")
                params.extend([stock_code, market])
            
            if start_date:
                where_clauses.append("ts.transaction_date >= %s")
                params.append(start_date)
        
        # 组合WHERE子句
        where_clause = " AND ".join(where_clauses) if where_clauses else ""
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        # 查询交易分单记录
        query = f"""
        SELECT ts.*, t.user_id
        FROM transaction_splits ts
        JOIN stock_transactions t ON ts.original_transaction_id = t.id
        {where_clause}
        ORDER BY ts.holder_id, ts.market, ts.stock_code, ts.transaction_date, ts.id
        """
        
        cursor.execute(query, params)
        splits = cursor.fetchall()
        
        logger.info(f"找到 {len(splits)} 条交易分单记录")
        return splits
    
    except Exception as e:
        logger.error(f"获取交易分单记录失败: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def batch_update_transaction_splits(updates):
    """
    批量更新交易分单记录
    
    Args:
        updates (list): 更新数据列表，每项为(split_id, updated_fields)元组
        
    Returns:
        int: 成功更新的记录数
    """
    if not updates:
        return 0
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        success_count = 0
        
        # 使用事务批量更新
        for split_id, updated_fields in updates:
            try:
                # 构建更新SQL
                set_clause = ", ".join([f"{field} = %s" for field in updated_fields.keys()])
                update_query = f"""
                UPDATE transaction_splits
                SET {set_clause}
                WHERE id = %s
                """
                
                # 构建参数列表
                params = list(updated_fields.values()) + [split_id]
                
                # 执行更新
                cursor.execute(update_query, params)
                success_count += 1
            except Exception as e:
                logger.error(f"更新交易分单记录 {split_id} 失败: {str(e)}")
        
        # 提交事务
        conn.commit()
        
        return success_count
    
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"批量更新交易分单记录失败: {str(e)}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_previous_state(holder_id, market, stock_code, transaction_date, transaction_id=None):
    """
    获取指定交易之前的持仓状态
    
    Args:
        holder_id (int): 持有人ID
        market (str): 市场
        stock_code (str): 股票代码
        transaction_date (date): 交易日期
        transaction_id (int, optional): 交易ID
        
    Returns:
        dict: 之前的持仓状态
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        where_clause = """
        WHERE holder_id = %s
        AND market = %s
        AND stock_code = %s
        AND (
            transaction_date < %s
            OR (transaction_date = %s AND id < %s)
        )
        """
        params = [holder_id, market, stock_code, transaction_date, transaction_date]
        
        if transaction_id:
            params.append(transaction_id)
        else:
            # 如果没有提供交易ID，则查询该日期之前的所有记录
            where_clause = """
            WHERE holder_id = %s
            AND market = %s
            AND stock_code = %s
            AND transaction_date < %s
            """
            params = [holder_id, market, stock_code, transaction_date]
        
        # 查询同一持有人同一股票在该交易之前的最后一条记录
        query = f"""
        SELECT current_quantity as quantity, current_cost as cost, current_avg_cost as avg_cost
        FROM transaction_splits
        {where_clause}
        ORDER BY transaction_date DESC, id DESC
        LIMIT 1
        """
        
        cursor.execute(query, params)
        prev_state = cursor.fetchone()
        
        if prev_state:
            logger.info(f"找到之前的持仓状态: 数量={prev_state['quantity']}, 成本={prev_state['cost']}, 平均成本={prev_state['avg_cost']}")
            return prev_state
        else:
            logger.info("没有找到之前的持仓状态，使用初始值")
            return {'quantity': 0, 'cost': 0, 'avg_cost': 0}
    
    except Exception as e:
        logger.error(f"获取之前的持仓状态失败: {str(e)}")
        return {'quantity': 0, 'cost': 0, 'avg_cost': 0}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_original_transactions():
    """
    更新原始交易记录，使其与分单记录保持一致
    
    Returns:
        int: 更新的记录数
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新原始交易记录的avg_price字段
        update_query = """
        UPDATE stock_transactions t
        JOIN (
            SELECT 
                original_transaction_id,
                SUM(total_amount) / SUM(total_quantity) as avg_price
            FROM transaction_splits
            GROUP BY original_transaction_id
        ) ts ON t.id = ts.original_transaction_id
        SET t.avg_price = ts.avg_price
        WHERE t.total_quantity > 0
        """
        
        cursor.execute(update_query)
        affected_rows = cursor.rowcount
        
        conn.commit()
        
        logger.info(f"更新了 {affected_rows} 条原始交易记录")
        return affected_rows
    
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"更新原始交易记录失败: {str(e)}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def recalculate_transaction_splits(holder_id=None, stock_code=None, market=None, start_date=None, transaction_id=None, update_original=False):
    """
    重新计算交易分单记录的字段
    
    该函数可以在添加交易记录、修改交易记录、删除交易记录、交易记录分单后调用，
    确保所有相关字段的计算准确性。
    
    Args:
        holder_id (int, optional): 持有人ID，不指定则处理所有记录
        stock_code (str, optional): 股票代码，需要同时指定市场
        market (str, optional): 股票市场，需要同时指定股票代码
        start_date (date, optional): 开始日期，只处理该日期及之后的记录
        transaction_id (int, optional): 交易ID，只处理该交易及其后续交易
        update_original (bool, optional): 是否同时更新原始交易记录
        
    Returns:
        tuple: (total_count, success_count, fail_count)
    """
    # 确保日志目录存在
    ensure_log_directory()
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始重新计算交易分单记录字段 - {start_time}")
    
    # 记录筛选条件
    if holder_id:
        logger.info(f"只处理持有人ID为 {holder_id} 的记录")
    
    if stock_code and market:
        logger.info(f"只处理股票代码为 {market}-{stock_code} 的记录")
    
    if start_date:
        logger.info(f"只处理 {start_date} 及之后的记录")
    
    if transaction_id:
        logger.info(f"只处理交易ID为 {transaction_id} 及其后续交易")
    
    # 获取交易分单记录
    splits = get_transaction_splits(holder_id, stock_code, market, start_date, transaction_id)
    
    if not splits:
        logger.info("没有找到交易分单记录")
        return (0, 0, 0)
    
    # 按持有人和股票分组
    holder_stock_groups = defaultdict(list)
    for split in splits:
        key = (split['holder_id'], split['market'], split['stock_code'])
        holder_stock_groups[key].append(split)
    
    logger.info(f"共有 {len(holder_stock_groups)} 个持有人-股票组合")
    
    # 处理每个持有人-股票组合
    total_count = 0
    success_count = 0
    fail_count = 0
    
    for (holder_id, market, stock_code), group_splits in holder_stock_groups.items():
        logger.info(f"处理持有人 {holder_id} 的 {market}-{stock_code} 股票")
        
        # 按交易日期和ID排序
        group_splits.sort(key=lambda x: (x['transaction_date'], x['id']))
        
        # 获取第一条记录的前一状态
        first_split = group_splits[0]
        prev_state = get_previous_state(
            first_split['holder_id'], 
            first_split['market'], 
            first_split['stock_code'], 
            first_split['transaction_date']
        )
        
        # 初始化持仓状态
        running_quantity = prev_state.get('quantity', 0)
        running_cost = prev_state.get('cost', 0)
        
        # 批量更新缓存
        batch_updates = []
        batch_size = 100  # 每100条记录批量提交一次
        
        # 处理每条交易分单记录
        for split in group_splits:
            total_count += 1
            
            try:
                # 获取交易数据
                transaction_type = split['transaction_type'].lower()
                total_quantity = float(split['total_quantity'])
                total_amount = float(split['total_amount'])
                
                # 计算总费用
                total_fees = (
                    float(split.get('broker_fee', 0) or 0) +
                    float(split.get('stamp_duty', 0) or 0) +
                    float(split.get('transaction_levy', 0) or 0) +
                    float(split.get('trading_fee', 0) or 0) +
                    float(split.get('deposit_fee', 0) or 0)
                )
                
                # 计算交易前状态
                prev_quantity = running_quantity
                prev_cost = running_cost
                prev_avg_cost = prev_cost / prev_quantity if prev_quantity > 0 else 0
                
                # 计算交易后状态
                if transaction_type == 'buy':
                    current_quantity = prev_quantity + total_quantity
                    
                    # 买入成本应包含交易费用
                    buy_cost_with_fees = total_amount + total_fees
                    current_cost = prev_cost + buy_cost_with_fees
                    
                    # 计算新的平均成本（包含费用）
                    current_avg_cost = current_cost / current_quantity if current_quantity > 0 else 0
                    
                    # 更新累计状态
                    running_quantity = current_quantity
                    running_cost = current_cost
                    
                    # 买入没有已实现盈亏
                    realized_profit = 0
                    profit_rate = 0
                    
                    # 计算净金额 - 买入是负数（支出）
                    net_amount = -(total_amount + total_fees)
                else:  # sell
                    current_quantity = prev_quantity - total_quantity
                    
                    # 计算已实现盈亏
                    realized_profit = 0
                    profit_rate = 0
                    
                    if prev_quantity > 0 and prev_avg_cost > 0:
                        # 卖出收入 - 买入成本（包含费用的平均成本） - 卖出费用
                        buy_cost = total_quantity * prev_avg_cost
                        realized_profit = total_amount - buy_cost - total_fees
                        
                        # 计算盈亏率
                        if buy_cost > 0:
                            profit_rate = (realized_profit / buy_cost) * 100
                    
                    # 计算剩余成本
                    if prev_quantity > 0:
                        current_cost = prev_cost * (current_quantity / prev_quantity) if current_quantity > 0 else 0
                    else:
                        current_cost = 0
                    
                    # 更新平均成本
                    current_avg_cost = current_cost / current_quantity if current_quantity > 0 else 0
                    
                    # 更新累计状态
                    running_quantity = current_quantity
                    running_cost = current_cost
                    
                    # 计算净金额
                    net_amount = total_amount - total_fees
                
                # 更新字段
                updated_fields = {
                    'prev_quantity': prev_quantity,
                    'prev_cost': prev_cost,
                    'prev_avg_cost': prev_avg_cost,
                    'current_quantity': current_quantity,
                    'current_cost': current_cost,
                    'current_avg_cost': current_avg_cost,
                    'total_fees': total_fees,
                    'net_amount': net_amount,
                    'running_quantity': running_quantity,
                    'running_cost': running_cost,
                    'realized_profit': realized_profit,
                    'profit_rate': profit_rate
                }
                
                # 添加到批量更新列表
                batch_updates.append((split['id'], updated_fields))
                
                # 每达到批量大小就提交一次
                if len(batch_updates) >= batch_size:
                    batch_success = batch_update_transaction_splits(batch_updates)
                    success_count += batch_success
                    fail_count += len(batch_updates) - batch_success
                    batch_updates = []
                    logger.info(f"已处理 {total_count} 条记录，成功 {success_count} 条，失败 {fail_count} 条")
            
            except Exception as e:
                fail_count += 1
                logger.error(f"处理交易分单记录 {split['id']} 时发生错误: {str(e)}")
        
        # 处理剩余的批量更新
        if batch_updates:
            batch_success = batch_update_transaction_splits(batch_updates)
            success_count += batch_success
            fail_count += len(batch_updates) - batch_success
    
    # 是否同时更新原始交易记录
    if update_original:
        logger.info("开始更新原始交易记录")
        update_original_transactions()
    
    # 记录结束时间和处理时间
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"处理完成: 总计 {total_count} 条, 成功 {success_count} 条, 失败 {fail_count} 条, 耗时 {duration:.2f} 秒")
    
    return (total_count, success_count, fail_count)

if __name__ == '__main__':
    # 确保日志目录存在
    ensure_log_directory()
    
    print("开始重新计算所有交易记录...")
    
    try:
        # 重新计算所有交易分单记录
        total, success, fail = recalculate_transaction_splits(update_original=True)
        
        print(f"\n重新计算完成:")
        print(f"总计处理记录: {total}")
        print(f"成功处理: {success}")
        print(f"失败处理: {fail}")
        
    except Exception as e:
        print(f"重新计算过程中发生错误: {str(e)}") 