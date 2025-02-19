from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from config.database import db

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
        
        # 构建基础SQL
        market_sql = """
            SELECT 
                market,
                currency,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN transaction_type = 'buy' THEN 1 ELSE 0 END) as buy_count,
                SUM(CASE WHEN transaction_type = 'sell' THEN 1 ELSE 0 END) as sell_count,
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity * price ELSE 0 END) as total_buy,
                SUM(CASE WHEN transaction_type = 'sell' THEN quantity * price ELSE 0 END) as total_sell,
                SUM(broker_fee + transaction_levy + stamp_duty + trading_fee + deposit_fee) as total_fees,
                SUM(CASE 
                    WHEN transaction_type = 'sell' THEN quantity * price 
                    ELSE -quantity * price 
                END) as realized_profit
            FROM stock_transactions 
            WHERE user_id = %s
        """
        params = [session['user_id']]
        
        if start_date:
            market_sql += " AND transaction_date >= %s"
            params.append(start_date)
        if end_date:
            market_sql += " AND transaction_date <= %s"
            params.append(end_date)
        if market:
            market_sql += " AND market = %s"
            params.append(market)
            
        market_sql += " GROUP BY market, currency"
        
        # 获取市场统计数据
        market_stats = db.fetch_all(market_sql, params)
        
        # 获取股票明细统计
        stock_sql = """
            SELECT 
                stock_code,
                stock_name,
                market,
                currency,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE 0 END) as total_buy_quantity,
                SUM(CASE WHEN transaction_type = 'sell' THEN quantity ELSE 0 END) as total_sell_quantity,
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity * price ELSE 0 END) as total_buy,
                SUM(CASE WHEN transaction_type = 'sell' THEN quantity * price ELSE 0 END) as total_sell,
                SUM(broker_fee + transaction_levy + stamp_duty + trading_fee + deposit_fee) as total_fees,
                SUM(CASE 
                    WHEN transaction_type = 'sell' THEN quantity * price 
                    ELSE -quantity * price 
                END) as realized_profit
            FROM stock_transactions 
            WHERE user_id = %s
        """
        stock_params = [session['user_id']]
        
        if start_date:
            stock_sql += " AND transaction_date >= %s"
            stock_params.append(start_date)
        if end_date:
            stock_sql += " AND transaction_date <= %s"
            stock_params.append(end_date)
        if market:
            stock_sql += " AND market = %s"
            stock_params.append(market)
            
        stock_sql += " GROUP BY stock_code, stock_name, market, currency"
        
        # 获取股票统计数据
        stock_stats = db.fetch_all(stock_sql, stock_params)
        
        # 处理统计数据
        for market in market_stats:
            market['profit_rate'] = (market['realized_profit'] / market['total_buy'] * 100) if market['total_buy'] > 0 else 0
            market['market_value'] = 0  # TODO: 获取实时市值
            market['total_profit'] = market['realized_profit']  # TODO: 加上未实现盈亏
            
        for stock in stock_stats:
            stock['profit_rate'] = (stock['realized_profit'] / stock['total_buy'] * 100) if stock['total_buy'] > 0 else 0
            stock['current_price'] = 0  # TODO: 获取实时价格
            stock['market_value'] = 0  # TODO: 获取实时市值
            stock['total_profit'] = stock['realized_profit']  # TODO: 加上未实现盈亏
        
        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats,
                'stock_stats': stock_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取盈利统计失败: {str(e)}'
        }), 500 