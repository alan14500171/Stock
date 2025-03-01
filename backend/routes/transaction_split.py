#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, current_app, session
from datetime import datetime
import logging
import pymysql
import json
from utils.db import get_db_connection
from utils.auth import login_required, has_permission

transaction_split_bp = Blueprint('transaction_split', __name__)

@transaction_split_bp.route('/api/transaction/get_by_code', methods=['GET'])
@login_required
def get_transaction_by_code():
    """
    根据交易编号获取交易记录
    """
    transaction_code = request.args.get('transaction_code', '')
    
    if not transaction_code:
        return jsonify({
            'success': False,
            'message': '请提供交易编号'
        }), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询交易记录
        query = """
        SELECT t.*, s.code_name as stock_name 
        FROM stock_transactions t
        LEFT JOIN stocks s ON t.stock_code = s.code AND t.market = s.market
        WHERE t.transaction_code = %s
        """
        cursor.execute(query, (transaction_code,))
        transaction = cursor.fetchone()
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '未找到交易记录'
            }), 404
        
        # 获取交易明细
        detail_query = """
        SELECT *
        FROM stock_transaction_details
        WHERE transaction_id = %s
        """
        cursor.execute(detail_query, (transaction['id'],))
        details = cursor.fetchall()
        
        # 转换日期格式
        if transaction.get('transaction_date'):
            transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d')
        
        if transaction.get('created_at'):
            transaction['created_at'] = transaction['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        if transaction.get('updated_at'):
            transaction['updated_at'] = transaction['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 添加明细到交易记录
        transaction['details'] = details
        
        return jsonify({
            'success': True,
            'data': transaction
        })
        
    except Exception as e:
        current_app.logger.error(f"获取交易记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易记录失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@transaction_split_bp.route('/api/transaction/get_users', methods=['GET'])
@login_required
def get_users():
    """
    获取持有人列表，用于分单选择
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询持有人列表
        query = """
        SELECT id, name as display_name, type
        FROM holders
        WHERE status = 1
        ORDER BY name
        """
        cursor.execute(query)
        holders = cursor.fetchall()
        
        # 处理时间格式
        return jsonify({
            'success': True,
            'data': holders
        })
        
    except Exception as e:
        current_app.logger.error(f"获取持有人列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取持有人列表失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@transaction_split_bp.route('/api/transaction/split', methods=['POST'])
@login_required
def split_transaction():
    """
    分割交易记录
    """
    # 检查权限
    user_id = session.get('user_id')
    if not has_permission(user_id, 'transaction:split:add'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
        
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': '请提供数据'
        }), 400
    
    original_transaction_id = data.get('original_transaction_id')
    split_data = data.get('split_data', [])
    
    if not original_transaction_id:
        return jsonify({
            'success': False,
            'message': '请提供原始交易ID'
        }), 400
    
    if not split_data or not isinstance(split_data, list) or len(split_data) == 0:
        return jsonify({
            'success': False,
            'message': '请提供分单数据'
        }), 400
    
    # 验证总分配比例是否为100%
    total_ratio = sum(item.get('split_ratio', 0) for item in split_data)
    if abs(total_ratio - 1.0) > 0.0001:  # 允许0.01%的误差
        return jsonify({
            'success': False,
            'message': f'总分配比例必须为100%，当前为{total_ratio*100:.2f}%'
        }), 400
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取原始交易记录
        query = """
        SELECT t.*, s.code_name as stock_name 
        FROM stock_transactions t
        LEFT JOIN stocks s ON t.stock_code = s.code AND t.market = s.market
        WHERE t.id = %s
        """
        cursor.execute(query, (original_transaction_id,))
        original_transaction = cursor.fetchone()
        
        if not original_transaction:
            return jsonify({
                'success': False,
                'message': '未找到原始交易记录'
            }), 404
            
        # 记录原始交易记录的内容
        current_app.logger.info(f"获取到原始交易记录: ID={original_transaction_id}, 交易编号={original_transaction.get('transaction_code')}")
        current_app.logger.info(f"原始交易记录字段: {', '.join(original_transaction.keys())}")
        
        # 检查关键字段是否存在
        if 'stock_id' not in original_transaction:
            current_app.logger.warning(f"原始交易记录缺少stock_id字段，将使用默认值0")
        
        # 开始事务
        conn.begin()
        
        # 检查是否已经存在分单记录
        check_query = """
        SELECT COUNT(*) as count FROM transaction_splits
        WHERE original_transaction_id = %s
        """
        cursor.execute(check_query, (original_transaction_id,))
        result = cursor.fetchone()
        
        if result and result['count'] > 0:
            # 先删除已有的分单记录
            delete_query = """
            DELETE FROM transaction_splits
            WHERE original_transaction_id = %s
            """
            cursor.execute(delete_query, (original_transaction_id,))
        
        # 插入新的分单记录
        insert_query = """
        INSERT INTO transaction_splits (
            original_transaction_id, holder_id, holder_name, split_ratio,
            transaction_date, stock_id, stock_code, stock_name, market,
            transaction_code, transaction_type, total_amount, total_quantity,
            broker_fee, stamp_duty, transaction_levy, trading_fee, deposit_fee,
            prev_quantity, prev_cost, prev_avg_cost,
            current_quantity, current_cost, current_avg_cost,
            total_fees, net_amount, running_quantity, running_cost,
            realized_profit, profit_rate, exchange_rate, remarks, avg_price
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        split_ids = []
        for item in split_data:
            split_ratio = item.get('split_ratio', 0)
            holder_id = item.get('holder_id')
            holder_name = item.get('holder_name', '')
            
            # 记录当前处理的分单项
            current_app.logger.info(f"处理分单项: 持有人ID={holder_id}, 持有人名称={holder_name}, 分配比例={split_ratio}")
            
            # 如果没有提供持有人名称，尝试从数据库获取
            if not holder_name and holder_id:
                try:
                    holder_query = "SELECT name FROM holders WHERE id = %s"
                    cursor.execute(holder_query, (holder_id,))
                    holder_result = cursor.fetchone()
                    if holder_result:
                        holder_name = holder_result['name']
                        current_app.logger.info(f"从数据库获取持有人名称: {holder_name}")
                except Exception as e:
                    current_app.logger.error(f"获取持有人名称失败: {str(e)}")
            
            # 确保持有人名称不为空
            if not holder_name:
                holder_name = f"持有人ID: {holder_id}"
                current_app.logger.warning(f"使用默认持有人名称: {holder_name}")
            
            # 计算分摊后的值
            split_quantity = int(original_transaction['total_quantity'] * split_ratio)
            
            # 确保所有金额类型为float，避免Decimal和float混合运算
            total_amount = float(original_transaction['total_amount'])
            broker_fee = float(original_transaction['broker_fee']) if original_transaction['broker_fee'] else 0
            stamp_duty = float(original_transaction['stamp_duty']) if original_transaction['stamp_duty'] else 0
            transaction_levy = float(original_transaction['transaction_levy']) if original_transaction['transaction_levy'] else 0
            trading_fee = float(original_transaction['trading_fee']) if original_transaction['trading_fee'] else 0
            deposit_fee = float(original_transaction['deposit_fee']) if original_transaction['deposit_fee'] else 0
            
            split_amount = total_amount * split_ratio
            split_broker_fee = broker_fee * split_ratio
            split_stamp_duty = stamp_duty * split_ratio
            split_transaction_levy = transaction_levy * split_ratio
            split_trading_fee = trading_fee * split_ratio
            split_deposit_fee = deposit_fee * split_ratio
            
            # 计算平均价格
            split_avg_price = split_amount / split_quantity if split_quantity > 0 else 0
            
            # 计算总费用和净金额
            split_total_fees = split_broker_fee + split_stamp_duty + split_transaction_levy + split_trading_fee + split_deposit_fee
            
            if original_transaction['transaction_type'].lower() == 'buy':
                split_net_amount = split_amount + split_total_fees
            else:  # sell
                split_net_amount = split_amount - split_total_fees
            
            # 记录即将插入的分单记录数据
            current_app.logger.info(f"准备插入分单记录: 持有人={holder_name}, 股票={original_transaction.get('stock_code')}, 市场={original_transaction.get('market')}")
            current_app.logger.info(f"分单数据: 数量={split_quantity}, 金额={split_amount}, 平均价格={split_avg_price}, 净额={split_net_amount}")
            
            # 获取持有人当前持仓信息
            holding_query = """
            SELECT 
                SUM(CASE WHEN transaction_type = 'buy' THEN total_quantity ELSE -total_quantity END) as current_quantity,
                SUM(CASE WHEN transaction_type = 'buy' THEN total_amount ELSE -total_amount END) as current_cost
            FROM transaction_splits
            WHERE holder_id = %s AND stock_code = %s AND market = %s
            GROUP BY holder_id, stock_code, market
            """
            
            cursor.execute(holding_query, (holder_id, original_transaction['stock_code'], original_transaction['market']))
            holding_data = cursor.fetchone()
            
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
            if holding_data:
                prev_quantity = float(holding_data.get('current_quantity', 0) or 0)
                prev_cost = float(holding_data.get('current_cost', 0) or 0)
                
                # 计算平均成本
                if prev_quantity > 0:
                    prev_avg_cost = prev_cost / prev_quantity
                
                # 根据交易类型计算交易后持仓
                if original_transaction['transaction_type'].lower() == 'buy':
                    current_quantity = prev_quantity + split_quantity
                    current_cost = prev_cost + split_amount
                    
                    # 计算新的平均成本
                    if current_quantity > 0:
                        current_avg_cost = current_cost / current_quantity
                    
                    running_quantity = current_quantity
                    running_cost = current_cost
                else:  # sell
                    current_quantity = prev_quantity - split_quantity
                    
                    # 计算已实现盈亏
                    if prev_quantity > 0 and prev_avg_cost > 0:
                        realized_profit = split_amount - (split_quantity * prev_avg_cost)
                        profit_rate = (realized_profit / (split_quantity * prev_avg_cost)) * 100
                    
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
                if original_transaction['transaction_type'].lower() == 'buy':
                    current_quantity = split_quantity
                    current_cost = split_amount
                    
                    if current_quantity > 0:
                        current_avg_cost = current_cost / current_quantity
                    
                    running_quantity = current_quantity
                    running_cost = current_cost
                else:  # sell
                    # 卖出但没有持仓，这是一种异常情况
                    current_app.logger.warning(f"异常情况: 持有人{holder_name}卖出股票{original_transaction['stock_code']}但没有持仓记录")
                    
                    # 仍然记录为负持仓
                    current_quantity = -split_quantity
                    current_cost = -split_amount
                    current_avg_cost = 0
                    running_quantity = current_quantity
                    running_cost = current_cost
            
            # 插入分单记录
            cursor.execute(insert_query, (
                original_transaction_id, holder_id, holder_name, split_ratio,
                original_transaction['transaction_date'], original_transaction.get('stock_id', 0), 
                original_transaction['stock_code'], original_transaction['stock_name'], 
                original_transaction['market'], original_transaction['transaction_code'],
                original_transaction['transaction_type'], split_amount, split_quantity,
                split_broker_fee, split_stamp_duty, split_transaction_levy, split_trading_fee, 
                split_deposit_fee, 
                prev_quantity, prev_cost, prev_avg_cost,
                current_quantity, current_cost, current_avg_cost,
                split_total_fees, split_net_amount, running_quantity, running_cost,
                realized_profit, profit_rate,
                original_transaction.get('exchange_rate', 1.0), 
                f"分单自交易编号: {original_transaction['transaction_code']}",
                split_avg_price
            ))
            
            split_ids.append(cursor.lastrowid)
        
        # 提交事务
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': '交易分单成功',
            'data': {
                'split_ids': split_ids
            }
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        current_app.logger.error(f"交易分单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'交易分单失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@transaction_split_bp.route('/api/transaction/splits', methods=['GET'])
@login_required
def get_transaction_splits():
    """
    获取分单记录列表
    """
    try:
        # 解析查询参数
        original_transaction_id = request.args.get('original_transaction_id')
        holder_id = request.args.get('holder_id')
        stock_code = request.args.get('stock_code')
        market = request.args.get('market')
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询语句
        query = """
        SELECT ts.*, t.transaction_code as original_transaction_code
        FROM transaction_splits ts
        LEFT JOIN stock_transactions t ON ts.original_transaction_id = t.id
        WHERE 1=1
        """
        params = []
        
        if original_transaction_id:
            query += " AND ts.original_transaction_id = %s"
            params.append(original_transaction_id)
        
        if holder_id:
            query += " AND ts.holder_id = %s"
            params.append(holder_id)
        
        if stock_code:
            query += " AND ts.stock_code = %s"
            params.append(stock_code)
        
        if market:
            query += " AND ts.market = %s"
            params.append(market)
        
        # 添加排序
        query += " ORDER BY ts.transaction_date DESC, ts.id DESC"
        
        # 执行查询
        cursor.execute(query, tuple(params))
        splits = cursor.fetchall()
        
        # 处理日期格式
        for split in splits:
            if split.get('transaction_date'):
                split['transaction_date'] = split['transaction_date'].strftime('%Y-%m-%d')
            if split.get('created_at'):
                split['created_at'] = split['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if split.get('updated_at'):
                split['updated_at'] = split['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'data': {
                'items': splits,
                'total': len(splits)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取分单记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取分单记录失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def register_routes(app):
    """
    注册路由
    """
    app.register_blueprint(transaction_split_bp) 