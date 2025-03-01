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
    """处理交易分单"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400

        # 获取原始交易记录
        db = get_db_connection()
        original_transaction_sql = """
            SELECT * FROM stock_transactions 
            WHERE id = %s AND user_id = %s
        """
        original_transaction = db.fetch_one(
            original_transaction_sql, 
            [data['transaction_id'], session['user_id']]
        )
        
        if not original_transaction:
            return jsonify({
                'success': False,
                'message': '找不到原始交易记录'
            }), 404

        # 验证分单比例总和
        total_ratio = sum(Decimal(str(split['ratio'])) for split in data['splits'])
        if total_ratio != Decimal('1'):
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
                'remarks': original_transaction['remarks']
            }

            # 使用统一计算模块处理分单
            success, result = TransactionCalculator.process_transaction(
                db_conn=db,
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
                    db_conn=db,
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
                db_conn=db,
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
        db = get_db_connection()
        
        # 查询分单记录
        sql = """
            SELECT ts.*, h.name as holder_name
            FROM transaction_splits ts
            LEFT JOIN holders h ON ts.holder_id = h.id
            WHERE ts.original_transaction_id = %s
            ORDER BY ts.id
        """
        splits = db.fetch_all(sql, [transaction_id])
        
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

def register_routes(app):
    """
    注册路由
    """
    app.register_blueprint(transaction_split_bp) 