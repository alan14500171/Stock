from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from config.database import db
from datetime import datetime
from models import Stock, StockTransaction
from utils.exchange_rate import get_exchange_rate

profit_bp = Blueprint('profit', __name__)

@profit_bp.route('/')
@login_required
def get_profit_stats():
    """获取盈利统计数据"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')
        
        # 构建市场统计SQL
        market_sql = """
            SELECT 
                t.market,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount * COALESCE(t.exchange_rate, 1) ELSE 0 END) as total_buy_hkd,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount * COALESCE(t.exchange_rate, 1) ELSE 0 END) as total_sell_hkd,
                SUM(COALESCE(t.broker_fee, 0) + COALESCE(t.transaction_levy, 0) + 
                    COALESCE(t.stamp_duty, 0) + COALESCE(t.trading_fee, 0) + 
                    COALESCE(t.clearing_fee, 0) + COALESCE(t.deposit_fee, 0)) as total_fees,
                SUM((COALESCE(t.broker_fee, 0) + COALESCE(t.transaction_levy, 0) + 
                     COALESCE(t.stamp_duty, 0) + COALESCE(t.trading_fee, 0) + 
                     COALESCE(t.clearing_fee, 0) + COALESCE(t.deposit_fee, 0)) * 
                    COALESCE(t.exchange_rate, 1)) as total_fees_hkd,
                SUM(CASE 
                    WHEN t.transaction_type = 'sell' THEN t.total_amount 
                    ELSE -t.total_amount 
                END) as realized_profit,
                SUM(CASE 
                    WHEN t.transaction_type = 'sell' THEN t.total_amount * COALESCE(t.exchange_rate, 1)
                    ELSE -t.total_amount * COALESCE(t.exchange_rate, 1)
                END) as realized_profit_hkd
            FROM stock_transactions t
            WHERE t.user_id = %s
        """
        params = [session['user_id']]
        
        if start_date:
            market_sql += " AND DATE(t.transaction_date) >= %s"
            params.append(start_date)
        if end_date:
            market_sql += " AND DATE(t.transaction_date) <= %s"
            params.append(end_date)
        if market:
            market_sql += " AND t.market = %s"
            params.append(market)
            
        market_sql += " GROUP BY t.market"
        
        # 获取市场统计数据
        market_stats = db.fetch_all(market_sql, params)
        
        # 构建股票统计SQL
        stock_sql = """
            SELECT 
                t.stock_code,
                s.name as stock_name,
                t.market,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_quantity ELSE -t.total_quantity END) as quantity,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_amount * COALESCE(t.exchange_rate, 1) ELSE 0 END) as total_buy_hkd,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(CASE WHEN t.transaction_type = 'sell' THEN t.total_amount * COALESCE(t.exchange_rate, 1) ELSE 0 END) as total_sell_hkd,
                SUM(COALESCE(t.broker_fee, 0) + COALESCE(t.transaction_levy, 0) + 
                    COALESCE(t.stamp_duty, 0) + COALESCE(t.trading_fee, 0) + 
                    COALESCE(t.clearing_fee, 0) + COALESCE(t.deposit_fee, 0)) as total_fees,
                SUM((COALESCE(t.broker_fee, 0) + COALESCE(t.transaction_levy, 0) + 
                     COALESCE(t.stamp_duty, 0) + COALESCE(t.trading_fee, 0) + 
                     COALESCE(t.clearing_fee, 0) + COALESCE(t.deposit_fee, 0)) * 
                    COALESCE(t.exchange_rate, 1)) as total_fees_hkd,
                SUM(CASE 
                    WHEN t.transaction_type = 'sell' THEN t.total_amount 
                    ELSE -t.total_amount 
                END) as realized_profit,
                SUM(CASE 
                    WHEN t.transaction_type = 'sell' THEN t.total_amount * COALESCE(t.exchange_rate, 1)
                    ELSE -t.total_amount * COALESCE(t.exchange_rate, 1)
                END) as realized_profit_hkd
            FROM stock_transactions t
            LEFT JOIN stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE t.user_id = %s
        """
        stock_params = [session['user_id']]
        
        if start_date:
            stock_sql += " AND DATE(t.transaction_date) >= %s"
            stock_params.append(start_date)
        if end_date:
            stock_sql += " AND DATE(t.transaction_date) <= %s"
            stock_params.append(end_date)
        if market:
            stock_sql += " AND t.market = %s"
            stock_params.append(market)
            
        stock_sql += " GROUP BY t.stock_code, s.name, t.market"
        
        # 获取股票统计数据
        stock_stats = db.fetch_all(stock_sql, stock_params)
        
        # 处理统计数据
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
                'realized_profit': float(market['realized_profit'] or 0),
                'realized_profit_hkd': float(market['realized_profit_hkd'] or 0),
                'market_value': 0,
                'market_value_hkd': 0,
                'total_profit': 0,
                'total_profit_hkd': 0,
                'profit_rate': 0
            }
            
        stock_stats_dict = {}
        for stock in stock_stats:
            stock_code = stock['stock_code']
            total_buy = float(stock['total_buy'] or 0)
            total_buy_hkd = float(stock['total_buy_hkd'] or 0)
            total_sell = float(stock['total_sell'] or 0)
            total_sell_hkd = float(stock['total_sell_hkd'] or 0)
            realized_profit = float(stock['realized_profit'] or 0)
            realized_profit_hkd = float(stock['realized_profit_hkd'] or 0)
            quantity = int(stock['quantity'] or 0)
            
            # 计算总盈亏
            total_profit = realized_profit
            total_profit_hkd = realized_profit_hkd
            
            # 计算收益率
            profit_rate = (total_profit / total_buy * 100) if total_buy > 0 else 0
            
            stock_stats_dict[stock_code] = {
                'code': stock_code,
                'name': stock['stock_name'],
                'market': stock['market'],
                'transaction_count': stock['transaction_count'],
                'quantity': quantity,
                'total_buy': total_buy,
                'total_buy_hkd': total_buy_hkd,
                'total_sell': total_sell,
                'total_sell_hkd': total_sell_hkd,
                'total_fees': float(stock['total_fees'] or 0),
                'total_fees_hkd': float(stock['total_fees_hkd'] or 0),
                'realized_profit': realized_profit,
                'realized_profit_hkd': realized_profit_hkd,
                'total_profit': total_profit,
                'total_profit_hkd': total_profit_hkd,
                'profit_rate': profit_rate,
                'average_cost': (total_buy / quantity) if quantity > 0 else 0
            }
            
            # 更新市场统计数据
            market_data = market_stats_dict.get(stock['market'])
            if market_data:
                market_data['total_profit'] = market_data['realized_profit']
                market_data['total_profit_hkd'] = market_data['realized_profit_hkd']
                if market_data['total_buy'] > 0:
                    market_data['profit_rate'] = (market_data['total_profit'] / market_data['total_buy']) * 100
        
        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats_dict,
                'stock_stats': stock_stats_dict
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取盈利统计失败: {str(e)}'
        }), 500 