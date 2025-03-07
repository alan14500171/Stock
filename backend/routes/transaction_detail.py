#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, current_app
from utils.db import get_db_connection
from utils.auth import login_required
import pymysql
from decimal import Decimal

transaction_detail_bp = Blueprint('transaction_detail', __name__)

@transaction_detail_bp.route('/api/transaction/details', methods=['GET'])
@login_required
def get_transaction_details():
    """
    获取交易明细数据，包括数量、单价、买入金额、移动加权平均价格、卖出金额、费用、盈亏、盈亏率等
    数据来源于transaction_splits表
    
    请求参数:
    - holder_id: 持有人ID (可选)
    - stock_code: 股票代码 (可选)
    - market: 市场 (可选)
    - start_date: 开始日期，格式YYYY-MM-DD (可选)
    - end_date: 结束日期，格式YYYY-MM-DD (可选)
    
    返回:
    {
        "success": true,
        "data": [
            {
                "id": 123,
                "transaction_date": "2023-01-01",
                "transaction_code": "T20230101001",
                "transaction_type": "buy",
                "stock_code": "00700",
                "stock_name": "腾讯控股",
                "market": "HK",
                "holder_name": "默认持有人",
                "quantity": 100,
                "price": 400.5,
                "total_amount": 40050,
                "current_avg_cost": 400.5,
                "total_fees": 200.25,
                "realized_profit": 0,
                "profit_rate": 0
            }
        ]
    }
    """
    try:
        # 获取请求参数
        holder_id = request.args.get('holder_id')
        stock_code = request.args.get('stock_code')
        market = request.args.get('market')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        # 添加用户ID条件（从会话中获取）
        user_id = request.user_id
        where_clauses.append("t.user_id = %s")
        params.append(user_id)
        
        # 添加其他过滤条件
        if holder_id:
            where_clauses.append("ts.holder_id = %s")
            params.append(holder_id)
        
        if stock_code:
            where_clauses.append("ts.stock_code = %s")
            params.append(stock_code)
        
        if market:
            where_clauses.append("ts.market = %s")
            params.append(market)
        
        if start_date:
            where_clauses.append("ts.transaction_date >= %s")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("ts.transaction_date <= %s")
            params.append(end_date)
        
        # 组合WHERE子句
        where_clause = " AND ".join(where_clauses)
        
        # 构建SQL查询
        sql = f"""
        SELECT 
            ts.id,
            ts.transaction_date,
            t.transaction_code,
            ts.transaction_type,
            ts.stock_code,
            ts.stock_name,
            ts.market,
            ts.holder_name,
            ts.total_quantity as quantity,
            CASE 
                WHEN ts.total_quantity > 0 THEN ts.total_amount / ts.total_quantity 
                ELSE 0 
            END as price,
            ts.total_amount,
            ts.current_avg_cost,
            ts.prev_avg_cost,
            ts.total_fees,
            ts.realized_profit,
            ts.profit_rate,
            ts.prev_quantity,
            ts.current_quantity,
            CASE 
                WHEN LOWER(ts.transaction_type) = 'buy' THEN ts.total_amount
                ELSE 0 
            END as buy_amount,
            CASE 
                WHEN LOWER(ts.transaction_type) = 'sell' THEN ts.total_amount
                ELSE 0 
            END as sell_amount,
            ts.net_amount,
            CASE 
                WHEN LOWER(ts.transaction_type) = 'sell' AND ts.prev_avg_cost > 0 THEN 
                    ts.total_quantity * ts.prev_avg_cost
                ELSE 0 
            END as cost_basis,
            CASE 
                WHEN LOWER(ts.transaction_type) = 'sell' AND ts.prev_avg_cost > 0 AND ts.total_quantity > 0 THEN 
                    (ts.total_amount - ts.total_quantity * ts.prev_avg_cost) / (ts.total_quantity * ts.prev_avg_cost) * 100
                ELSE 0 
            END as gross_profit_rate
        FROM 
            transaction_splits ts
        JOIN 
            stock_transactions t ON ts.original_transaction_id = t.id
        WHERE 
            {where_clause}
        ORDER BY 
            ts.transaction_date DESC, ts.id DESC
        """
        
        # 执行查询
        cursor.execute(sql, params)
        details = cursor.fetchall()
        
        # 处理结果
        result = []
        for detail in details:
            # 转换日期格式
            if detail.get('transaction_date'):
                detail['transaction_date'] = detail['transaction_date'].strftime('%Y-%m-%d')
            
            # 转换Decimal类型为float
            for key, value in detail.items():
                if isinstance(value, Decimal):
                    detail[key] = float(value)
            
            result.append(detail)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        current_app.logger.error(f"获取交易明细失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取交易明细失败: {str(e)}"
        }), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close() 