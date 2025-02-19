from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from config.database import db
from datetime import datetime
from models import Stock, StockTransaction
from utils.exchange_rate import get_exchange_rate
from services.currency_checker import CurrencyChecker
import json
import logging

profit_bp = Blueprint('profit', __name__)
checker = CurrencyChecker()
logger = logging.getLogger(__name__)

@profit_bp.route('/')
@login_required
def get_profit_stats():
    """获取盈利统计数据"""
    try:
        # 原有的统计查询代码
        user_id = session.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')

        # 构建查询条件
        params = [user_id]
        conditions = ["t.user_id = %s"]
        
        if start_date:
            conditions.append("t.transaction_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("t.transaction_date <= %s")
            params.append(end_date)
        if market:
            conditions.append("t.market = %s")
            params.append(market)

        where_clause = " AND ".join(conditions)

        # 获取市场统计数据
        market_sql = f"""
            SELECT 
                t.market,
                COUNT(DISTINCT t.id) as transaction_count,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN 
                    t.total_amount * COALESCE(
                        (SELECT rate FROM exchange_rates 
                         WHERE currency = t.market 
                         AND rate_date <= t.transaction_date 
                         ORDER BY rate_date DESC LIMIT 1), 
                        1
                    ) 
                ELSE 0 END) as total_buy_hkd,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN 
                    t.total_amount * COALESCE(
                        (SELECT rate FROM exchange_rates 
                         WHERE currency = t.market 
                         AND rate_date <= t.transaction_date 
                         ORDER BY rate_date DESC LIMIT 1), 
                        1
                    ) 
                ELSE 0 END) as total_sell_hkd,
                SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                SUM((t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) * 
                    COALESCE(
                        (SELECT rate FROM exchange_rates 
                         WHERE currency = t.market 
                         AND rate_date <= t.transaction_date 
                         ORDER BY rate_date DESC LIMIT 1), 
                        1
                    )
                ) as total_fees_hkd
            FROM stock_transactions t
            WHERE {where_clause}
            GROUP BY t.market
        """
        
        # 获取股票统计数据
        stock_sql = f"""
            WITH transaction_summary AS (
                SELECT 
                    t.market,
                    t.stock_code,
                    s.name as stock_name,
                    0 as current_price,
                    COUNT(DISTINCT t.id) as transaction_count,
                    SUM(CASE 
                        WHEN t.transaction_type = 'buy' THEN t.total_quantity 
                        WHEN t.transaction_type = 'sell' THEN -t.total_quantity 
                        ELSE 0 
                    END) as quantity,
                    SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                    SUM(CASE WHEN t.transaction_type = 'buy' THEN 
                        t.total_amount * COALESCE(
                            (SELECT rate FROM exchange_rates 
                             WHERE currency = t.market 
                             AND rate_date <= t.transaction_date 
                             ORDER BY rate_date DESC LIMIT 1), 
                            1
                        ) 
                    ELSE 0 END) as total_buy_hkd,
                    SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                    SUM(CASE WHEN t.transaction_type = 'sell' THEN 
                        t.total_amount * COALESCE(
                            (SELECT rate FROM exchange_rates 
                             WHERE currency = t.market 
                             AND rate_date <= t.transaction_date 
                             ORDER BY rate_date DESC LIMIT 1), 
                            1
                        ) 
                    ELSE 0 END) as total_sell_hkd,
                    SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                    SUM((t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) * 
                        COALESCE(
                            (SELECT rate FROM exchange_rates 
                             WHERE currency = t.market 
                             AND rate_date <= t.transaction_date 
                             ORDER BY rate_date DESC LIMIT 1), 
                            1
                        )
                    ) as total_fees_hkd,
                    COALESCE(
                        (SELECT rate FROM exchange_rates 
                         WHERE currency = t.market 
                         AND rate_date <= CURRENT_DATE 
                         ORDER BY rate_date DESC LIMIT 1), 
                        1
                    ) as current_rate
                FROM stock_transactions t
                LEFT JOIN stocks s ON t.stock_code = s.code AND t.market = s.market
                WHERE {where_clause}
                GROUP BY t.market, t.stock_code, s.name
            )
            SELECT 
                market,
                stock_code,
                stock_name,
                quantity,
                transaction_count,
                total_buy,
                total_buy_hkd,
                CASE WHEN quantity > 0 THEN total_buy / quantity ELSE NULL END as average_cost,
                total_sell,
                total_sell_hkd,
                total_fees,
                total_fees_hkd,
                total_sell_hkd - total_buy_hkd - total_fees_hkd as realized_profit_hkd,
                current_price,
                CASE WHEN quantity > 0 THEN quantity * current_price * current_rate ELSE 0 END as market_value,
                CASE 
                    WHEN quantity > 0 THEN 
                        quantity * current_price * current_rate - total_buy_hkd + total_sell_hkd - total_fees_hkd
                    ELSE 
                        total_sell_hkd - total_buy_hkd - total_fees_hkd
                END as total_profit,
                CASE 
                    WHEN total_buy_hkd > 0 THEN 
                        (CASE 
                            WHEN quantity > 0 THEN 
                                (quantity * current_price * current_rate - total_buy_hkd + total_sell_hkd - total_fees_hkd) / total_buy_hkd * 100
                            ELSE 
                                (total_sell_hkd - total_buy_hkd - total_fees_hkd) / total_buy_hkd * 100
                        END)
                    ELSE NULL
                END as profit_rate,
                current_rate
            FROM transaction_summary
        """

        # 获取交易明细数据
        details_sql = f"""
            SELECT 
                t.id,
                t.market,
                t.stock_code,
                s.name as stock_name,
                t.transaction_type,
                t.transaction_date,
                t.transaction_code,
                t.total_amount,
                t.total_quantity,
                t.exchange_rate,
                t.broker_fee,
                t.stamp_duty,
                t.transaction_levy,
                t.trading_fee,
                t.deposit_fee,
                t.total_amount * COALESCE(
                    (SELECT rate FROM exchange_rates 
                     WHERE currency = t.market 
                     AND rate_date <= t.transaction_date 
                     ORDER BY rate_date DESC LIMIT 1), 
                    1
                ) as total_amount_hkd,
                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) * 
                COALESCE(
                    (SELECT rate FROM exchange_rates 
                     WHERE currency = t.market 
                     AND rate_date <= t.transaction_date 
                     ORDER BY rate_date DESC LIMIT 1), 
                    1
                ) as total_fees_hkd,
                td.quantity as detail_quantity,
                td.price as detail_price,
                td.quantity * td.price as detail_amount
            FROM stock_transactions t
            LEFT JOIN stocks s ON t.stock_code = s.code AND t.market = s.market
            LEFT JOIN stock_transaction_details td ON t.id = td.transaction_id
            WHERE {where_clause}
            ORDER BY t.transaction_date DESC, t.id DESC, td.id ASC
        """

        # 执行查询
        market_stats = db.fetch_all(market_sql, params)
        stock_stats = db.fetch_all(stock_sql, params)
        transaction_details = db.fetch_all(details_sql, params)

        # 处理市场统计数据
        market_stats_dict = {}
        for market in market_stats:
            market_code = market['market']
            market_stats_dict[market_code] = {
                'market': market_code,
                'transaction_count': market['transaction_count'],
                'total_buy': float(market['total_buy'] or 0),
                'total_buy_hkd': float(market['total_buy_hkd'] or 0),
                'total_sell': float(market['total_sell'] or 0),
                'total_sell_hkd': float(market['total_sell_hkd'] or 0),
                'total_fees': float(market['total_fees'] or 0),
                'total_fees_hkd': float(market['total_fees_hkd'] or 0),
                'realized_profit': float(market['total_sell_hkd'] - market['total_buy_hkd'] - market['total_fees_hkd']),
                'market_value': 0,  # 将在下面计算
                'total_profit': 0,  # 将在下面计算
                'profit_rate': 0    # 将在下面计算
            }

        # 处理股票统计数据
        stock_stats_dict = {}
        for stock in stock_stats:
            market = stock['market']
            stock_code = stock['stock_code']
            market_value = float(stock['market_value'] or 0)
            total_profit = float(stock['total_profit'] or 0)
            
            # 更新市场统计
            if market in market_stats_dict:
                market_stats_dict[market]['market_value'] += market_value
                market_stats_dict[market]['total_profit'] += total_profit
                if market_stats_dict[market]['total_buy_hkd'] > 0:
                    market_stats_dict[market]['profit_rate'] = (
                        market_stats_dict[market]['total_profit'] / 
                        market_stats_dict[market]['total_buy_hkd'] * 100
                    )

            # 股票统计
            stock_stats_dict[f"{market}-{stock_code}"] = {
                'market': market,
                'code': stock_code,
                'name': stock['stock_name'],
                'quantity': float(stock['quantity'] or 0),
                'transaction_count': stock['transaction_count'],
                'total_buy': float(stock['total_buy'] or 0),
                'total_buy_hkd': float(stock['total_buy_hkd'] or 0),
                'average_cost': float(stock['average_cost'] or 0),
                'total_sell': float(stock['total_sell'] or 0),
                'total_sell_hkd': float(stock['total_sell_hkd'] or 0),
                'total_fees': float(stock['total_fees'] or 0),
                'total_fees_hkd': float(stock['total_fees_hkd'] or 0),
                'realized_profit': float(stock['realized_profit_hkd'] or 0),
                'current_price': float(stock['current_price'] or 0),
                'market_value': market_value,
                'total_profit': total_profit,
                'profit_rate': float(stock['profit_rate'] or 0),
                'exchange_rate': float(stock['current_rate'] or 1)
            }

        # 处理交易明细数据
        transaction_details_dict = {}
        for detail in transaction_details:
            market = detail['market']
            stock_code = detail['stock_code']
            key = f"{market}-{stock_code}"
            
            if key not in transaction_details_dict:
                transaction_details_dict[key] = []
            
            # 添加交易明细
            transaction_details_dict[key].append({
                'id': detail['id'],
                'transaction_code': detail['transaction_code'],
                'transaction_type': detail['transaction_type'],
                'transaction_date': detail['transaction_date'].isoformat() if detail['transaction_date'] else None,
                'total_amount': float(detail['total_amount'] or 0),
                'total_amount_hkd': float(detail['total_amount_hkd'] or 0),
                'total_quantity': float(detail['total_quantity'] or 0),
                'exchange_rate': float(detail['exchange_rate'] or 1),
                'broker_fee': float(detail['broker_fee'] or 0),
                'stamp_duty': float(detail['stamp_duty'] or 0),
                'transaction_levy': float(detail['transaction_levy'] or 0),
                'trading_fee': float(detail['trading_fee'] or 0),
                'deposit_fee': float(detail['deposit_fee'] or 0),
                'total_fees_hkd': float(detail['total_fees_hkd'] or 0),
                'details': [{
                    'quantity': float(detail['detail_quantity'] or 0),
                    'price': float(detail['detail_price'] or 0),
                    'amount': float(detail['detail_amount'] or 0)
                }] if detail['detail_quantity'] is not None else []
            })

        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats_dict,
                'stock_stats': stock_stats_dict,
                'transaction_details': transaction_details_dict
            }
        })

    except Exception as e:
        logger.error(f"获取盈利统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取盈利统计失败: {str(e)}"
        }), 500 