#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, current_app, session
from datetime import datetime
import logging
import pymysql
import json
from utils.db import get_db_connection
from utils.auth import login_required, has_permission
from services.transaction_calculator import TransactionCalculator
from decimal import Decimal

transaction_split_bp = Blueprint('transaction_split', __name__)
logger = logging.getLogger(__name__)

@transaction_split_bp.route('/api/transaction/get_by_code', methods=['GET'])
@login_required
def get_transaction_by_code():
    """
    根据交易编号获取交易记录
    允许以下用户查看：
    1. 交易创建者
    2. 分单的持有人关联的用户
    """
    transaction_code = request.args.get('transaction_code', '')
    current_user_id = session.get('user_id')
    
    # 添加详细日志
    logger.info(f"请求交易记录，交易编号: {transaction_code}")
    logger.info(f"当前session: {dict(session)}")
    logger.info(f"当前用户ID: {current_user_id}")
    
    if not transaction_code:
        return jsonify({
            'success': False,
            'message': '请提供交易编号'
        }), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查权限：是否是交易创建者或分单持有人
        auth_check_query = """
        SELECT DISTINCT st.id, st.transaction_code
        FROM stock_transactions st
        LEFT JOIN transaction_splits ts ON st.id = ts.original_transaction_id
        LEFT JOIN holders h ON ts.holder_id = h.id
        WHERE st.transaction_code = %s 
        AND (
            st.user_id = %s 
            OR h.user_id = %s 
            OR EXISTS (
                SELECT 1 
                FROM holders h2 
                WHERE h2.user_id = %s 
                AND h2.id IN (
                    SELECT holder_id 
                    FROM transaction_splits 
                    WHERE original_transaction_id = st.id
                )
            )
        )
        """
        
        # 记录查询参数
        logger.info(f"执行权限检查查询，参数: user_id={current_user_id}, transaction_code={transaction_code}")
        
        cursor.execute(auth_check_query, (transaction_code, current_user_id, current_user_id, current_user_id))
        auth_result = cursor.fetchone()
        
        # 记录权限检查结果
        logger.info(f"权限检查结果: {auth_result}")
        
        if not auth_result:
            # 记录更多信息以便调试
            debug_query = """
            SELECT 
                st.id as transaction_id,
                st.transaction_code,
                st.user_id as transaction_user_id,
                ts.id as split_id,
                h.id as holder_id,
                h.name as holder_name,
                h.user_id as holder_user_id
            FROM stock_transactions st
            LEFT JOIN transaction_splits ts ON st.id = ts.original_transaction_id
            LEFT JOIN holders h ON ts.holder_id = h.id
            WHERE st.transaction_code = %s
            """
            cursor.execute(debug_query, (transaction_code,))
            debug_info = cursor.fetchall()
            logger.info(f"调试信息 - 交易记录详情: {debug_info}")
            
            return jsonify({
                'success': False,
                'message': '无权查看该交易记录'
            }), 403
        
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
        
        # 获取分单记录
        splits_query = """
        SELECT ts.*, h.name as holder_name, h.user_id as holder_user_id
        FROM transaction_splits ts
        LEFT JOIN holders h ON ts.holder_id = h.id
        WHERE ts.original_transaction_id = %s
        """
        cursor.execute(splits_query, (transaction['id'],))
        splits = cursor.fetchall()
        
        # 转换日期格式
        if transaction.get('transaction_date'):
            transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d')
        
        if transaction.get('created_at'):
            transaction['created_at'] = transaction['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        if transaction.get('updated_at'):
            transaction['updated_at'] = transaction['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 添加明细和分单信息到交易记录
        transaction['details'] = details
        transaction['splits'] = splits
        
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
    """处理交易分单"""
    try:
        data = request.get_json()
        logger.info(f"收到分单请求数据: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400

        # 获取原始交易记录
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        original_transaction_sql = """
            SELECT * FROM stock_transactions 
            WHERE id = %s AND user_id = %s
        """
        logger.info(f"查询原始交易记录: id={data['transaction_id']}, user_id={session['user_id']}")
        cursor.execute(original_transaction_sql, [data['transaction_id'], session['user_id']])
        original_transaction = cursor.fetchone()
        
        if not original_transaction:
            logger.warning(f"未找到原始交易记录: id={data['transaction_id']}, user_id={session['user_id']}")
            return jsonify({
                'success': False,
                'message': '找不到原始交易记录'
            }), 404

        logger.info(f"找到原始交易记录: {original_transaction}")

        # 验证分单比例总和
        total_ratio = sum(Decimal(str(split['ratio'])) for split in data['splits'])
        logger.info(f"分单比例总和: {total_ratio}")
        
        if total_ratio != Decimal('1'):
            logger.warning(f"分单比例总和不等于1: {total_ratio}")
            return jsonify({
                'success': False,
                'message': '分单比例总和必须等于1'
            }), 400

        # 开始处理每个分单
        success_splits = []
        failed_splits = []
        
        for split in data['splits']:
            # 构建分单交易数据
            split_transaction = {
                'transaction_date': original_transaction['transaction_date'].strftime('%Y-%m-%d'),
                'stock_code': original_transaction['stock_code'],
                'market': original_transaction['market'],
                'transaction_type': original_transaction['transaction_type'],
                'total_quantity': Decimal(str(original_transaction['total_quantity'])) * Decimal(str(split['ratio'])),
                'total_amount': Decimal(str(original_transaction['total_amount'])) * Decimal(str(split['ratio'])),
                'broker_fee': Decimal(str(original_transaction['broker_fee'])) * Decimal(str(split['ratio'])),
                'stamp_duty': Decimal(str(original_transaction['stamp_duty'])) * Decimal(str(split['ratio'])),
                'transaction_levy': Decimal(str(original_transaction['transaction_levy'])) * Decimal(str(split['ratio'])),
                'trading_fee': Decimal(str(original_transaction['trading_fee'])) * Decimal(str(split['ratio'])),
                'deposit_fee': Decimal(str(original_transaction['deposit_fee'])) * Decimal(str(split['ratio'])),
                'split_ratio': split['ratio'],
                'remarks': original_transaction.get('remarks', '') or ''
            }

            # 使用统一计算模块处理分单
            success, result = TransactionCalculator.process_transaction(
                db_conn=conn,
                transaction_data=split_transaction,
                operation_type='split',
                holder_id=split['holder_id'],
                original_transaction_id=data['transaction_id']
            )

            if success:
                success_splits.append({
                    'holder_id': split['holder_id'],
                    'split_id': result['split_id']
                })
            else:
                failed_splits.append({
                    'holder_id': split['holder_id'],
                    'message': result.get('message', '分单处理失败')
                })

        # 如果有任何分单失败，回滚所有成功的分单
        if failed_splits:
            for split in success_splits:
                TransactionCalculator.process_transaction(
                    db_conn=conn,
                    transaction_data={'id': split['split_id']},
                    operation_type='delete',
                    holder_id=split['holder_id']
                )
            
            return jsonify({
                'success': False,
                'message': '部分分单处理失败',
                'failed_splits': failed_splits
            }), 400

        # 重新计算后续交易记录
        for split in success_splits:
            TransactionCalculator.recalculate_subsequent_transactions(
                db_conn=conn,
                stock_code=original_transaction['stock_code'],
                market=original_transaction['market'],
                start_date=original_transaction['transaction_date'].strftime('%Y-%m-%d'),
                holder_id=split['holder_id']
            )

        return jsonify({
            'success': True,
            'message': '交易分单处理成功',
            'splits': success_splits
        })

    except Exception as e:
        logger.error(f"处理交易分单时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'处理交易分单失败: {str(e)}'
        }), 500

@transaction_split_bp.route('/api/transaction/splits', methods=['GET'])
@login_required
def get_transaction_splits():
    """获取交易分单记录"""
    try:
        # 获取查询参数
        transaction_id = request.args.get('transaction_id')
        if not transaction_id:
            return jsonify({
                'success': False,
                'message': '缺少交易ID参数'
            }), 400

        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询分单记录
        sql = """
            SELECT ts.*, h.name as holder_name
            FROM transaction_splits ts
            LEFT JOIN holders h ON ts.holder_id = h.id
            WHERE ts.original_transaction_id = %s
            ORDER BY ts.id
        """
        cursor.execute(sql, [transaction_id])
        splits = cursor.fetchall()
        
        # 格式化数据
        formatted_splits = []
        for split in splits:
            formatted_splits.append({
                'id': split['id'],
                'holder_id': split['holder_id'],
                'holder_name': split['holder_name'],
                'split_ratio': float(split['split_ratio']),
                'total_quantity': float(split['total_quantity']),
                'total_amount': float(split['total_amount']),
                'realized_profit': float(split['realized_profit']),
                'profit_rate': float(split['profit_rate']),
                'current_quantity': float(split['current_quantity']),
                'current_cost': float(split['current_cost']),
                'current_avg_cost': float(split['current_avg_cost']),
                'total_fees': float(split['total_fees'])
            })
            
        return jsonify({
            'success': True,
            'splits': formatted_splits
        })
        
    except Exception as e:
        logger.error(f"获取交易分单记录时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易分单记录失败: {str(e)}'
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