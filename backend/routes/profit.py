from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from utils.auth import permission_required
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

def process_transactions(transactions):
    """处理交易数据，生成统计信息"""
    market_stats = {}
    stock_stats = {}
    transaction_details = {}
    sorted_stock_stats = {}  # 添加这一行，确保变量在使用前初始化
    
    # 按日期排序交易记录 - 修复：使用sorted函数而不是直接调用sort方法
    transactions = sorted(transactions, key=lambda x: (x['transaction_date'], x['id']))
    
    # 按股票分组处理交易记录
    stock_groups = {}
    for transaction in transactions:
        market = transaction['market']
        stock_code = transaction['stock_code']
        stock_key = f"{market}-{stock_code}"
        
        # 确保交易类型为大写
        transaction['transaction_type'] = transaction['transaction_type'].upper()
        
        if stock_key not in stock_groups:
            stock_groups[stock_key] = []
        stock_groups[stock_key].append(transaction)
        
        # 初始化市场统计
        if market not in market_stats:
            market_stats[market] = {
                'transaction_count': 0,
                'total_buy': 0,
                'total_sell': 0,
                'total_fees': 0,
                'realized_profit': 0,
                'market_value': 0,
                'holding_profit': 0,
                'total_profit': 0,
                'profit_rate': 0,
                'holding_stats': {
                    'count': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'market_value': 0,
                    'holding_profit': 0,
                    'total_profit': 0,
                    'profit_rate': 0
                },
                'closed_stats': {
                    'count': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'profit_rate': 0
                }
            }
    
    # 处理每个股票的统计数据
    for stock_key, stock_transactions in stock_groups.items():
        market = stock_transactions[0]['market']
        stock_code = stock_transactions[0]['stock_code']
        stock_name = stock_transactions[0]['stock_name']
        current_price = float(stock_transactions[0]['current_avg_cost'] if stock_transactions[0].get('current_avg_cost') else 0)
        
        # 初始化股票统计
        stock_stats[stock_key] = {
            'market': market,
            'stock_code': stock_code,
            'stock_name': stock_name,
            'current_quantity': 0,
            'transaction_count': len(stock_transactions),
            'total_buy': 0,
            'total_sell': 0,
            'total_fees': 0,
            'realized_profit': 0,
            'current_price': current_price,
            'market_value': 0,
            'holding_profit': 0,
            'total_profit': 0,
            'profit_rate': 0,
            'average_cost': 0,
            'last_transaction_date': stock_transactions[0]['transaction_date']
        }
        
        # 初始化交易明细
        transaction_details[stock_key] = []
        
        # 计算股票统计数据
        last_buy_transaction = None
        for trans in stock_transactions:
            total_amount = float(trans['total_amount'] or 0)
            total_quantity = float(trans['total_quantity'] or 0)
            total_fees = float(trans['total_fees'] or 0)
            prev_avg_cost = float(trans['prev_avg_cost'] or 0)
            
            # 更新统计数据
            if trans['transaction_type'].upper() == 'BUY':
                stock_stats[stock_key]['current_quantity'] += total_quantity
                stock_stats[stock_key]['total_buy'] += total_amount
                stock_stats[stock_key]['total_fees'] += total_fees
                market_stats[market]['transaction_count'] += trans['transaction_count']
                market_stats[market]['total_buy'] += trans['total_amount']
                market_stats[market]['total_fees'] += trans['total_fees']
                last_buy_transaction = trans
            else:  # SELL
                stock_stats[stock_key]['current_quantity'] -= total_quantity
                stock_stats[stock_key]['total_sell'] += total_amount
                stock_stats[stock_key]['total_fees'] += total_fees
                market_stats[market]['transaction_count'] += trans['transaction_count']
                market_stats[market]['total_sell'] += trans['total_amount']
                market_stats[market]['total_fees'] += trans['total_fees']
                
                # 计算卖出时的已实现盈亏
                # 卖出收入 - 买入成本 - 相关费用
                realized_profit = total_amount - (total_quantity * prev_avg_cost) - total_fees
                stock_stats[stock_key]['realized_profit'] += realized_profit
                market_stats[market]['realized_profit'] += realized_profit
            
            transaction_details[stock_key].append(trans)
        
        # 计算持仓市值和持仓盈亏
        current_quantity = stock_stats[stock_key]['current_quantity']
        if current_quantity > 0:
            # 使用最后一次买入的移动加权平均价格作为平均成本
            stock_stats[stock_key]['average_cost'] = float(last_buy_transaction['current_avg_cost']) if last_buy_transaction else 0
            
            # 计算市值
            market_value = current_quantity * current_price
            stock_stats[stock_key]['market_value'] = market_value
            
            # 计算持仓盈亏
            holding_cost = current_quantity * stock_stats[stock_key]['average_cost']
            stock_stats[stock_key]['holding_profit'] = market_value - holding_cost
        
        # 计算总盈亏和盈亏率
        stock_stats[stock_key]['total_profit'] = (
            stock_stats[stock_key]['realized_profit'] + 
            stock_stats[stock_key]['holding_profit']
        )
        
        if stock_stats[stock_key]['total_buy'] > 0:
            stock_stats[stock_key]['profit_rate'] = (
                stock_stats[stock_key]['total_profit'] / 
                stock_stats[stock_key]['total_buy'] * 100
            )
        
        # 更新市场统计
        market_stats[market]['realized_profit'] += stock_stats[stock_key]['realized_profit']
        
        if current_quantity > 0:
            # 持仓统计
            market_stats[market]['holding_stats']['count'] += 1
            market_stats[market]['holding_stats']['total_buy'] += stock_stats[stock_key]['total_buy']
            market_stats[market]['holding_stats']['total_sell'] += stock_stats[stock_key]['total_sell']
            market_stats[market]['holding_stats']['total_fees'] += stock_stats[stock_key]['total_fees']
            market_stats[market]['holding_stats']['realized_profit'] += stock_stats[stock_key]['realized_profit']
            market_stats[market]['holding_stats']['market_value'] += stock_stats[stock_key]['market_value']
            market_stats[market]['holding_stats']['holding_profit'] += stock_stats[stock_key]['holding_profit']
            
            # 更新市场总计
            market_stats[market]['market_value'] += stock_stats[stock_key]['market_value']
            market_stats[market]['holding_profit'] += stock_stats[stock_key]['holding_profit']
        else:
            # 已清仓统计
            market_stats[market]['closed_stats']['count'] += 1
            market_stats[market]['closed_stats']['total_buy'] += stock_stats[stock_key]['total_buy']
            market_stats[market]['closed_stats']['total_sell'] += stock_stats[stock_key]['total_sell']
            market_stats[market]['closed_stats']['total_fees'] += stock_stats[stock_key]['total_fees']
            market_stats[market]['closed_stats']['realized_profit'] += stock_stats[stock_key]['realized_profit']
        
        # 获取每只股票的最后交易日期
        stock_last_dates = {}
        for stock_key, transactions in transaction_details.items():
            if transactions:
                # 按交易日期降序排序
                sorted_trans = sorted(transactions, key=lambda x: (x['transaction_date'], x['id']), reverse=True)
                stock_last_dates[stock_key] = sorted_trans[0]['transaction_date']
                # 将最后交易日期添加到 stock_stats 中
                stock_stats[stock_key]['last_transaction_date'] = sorted_trans[0]['transaction_date']
        
        # 对stock_stats进行排序
        sorted_stock_stats = {}
        for market in market_stats:
            market_stocks = {k: v for k, v in stock_stats.items() if v['market'] == market}
            # 按最后交易日期降序排序
            sorted_stocks = sorted(market_stocks.items(), 
                                 key=lambda x: stock_last_dates.get(x[0], ''), 
                                 reverse=True)
            for stock_key, stock_stat in sorted_stocks:
                sorted_stock_stats[stock_key] = stock_stat

    # 计算市场级别的汇总数据
    for market in market_stats:
        # 计算持仓统计的总盈亏和盈亏率
        holding_stats = market_stats[market]['holding_stats']
        holding_stats['total_profit'] = holding_stats['realized_profit'] + holding_stats['holding_profit']
        if holding_stats['total_buy'] > 0:
            holding_stats['profit_rate'] = (holding_stats['total_profit'] / holding_stats['total_buy']) * 100
        
        # 计算已清仓统计的盈亏率
        closed_stats = market_stats[market]['closed_stats']
        if closed_stats['total_buy'] > 0:
            closed_stats['profit_rate'] = (closed_stats['realized_profit'] / closed_stats['total_buy']) * 100
        
        # 计算市场总计的总盈亏和盈亏率
        market_stats[market]['total_profit'] = (
            market_stats[market]['realized_profit'] + 
            market_stats[market]['holding_profit']
        )
        if market_stats[market]['total_buy'] > 0:
            market_stats[market]['profit_rate'] = (
                market_stats[market]['total_profit'] / 
                market_stats[market]['total_buy']
            ) * 100

    return market_stats, sorted_stock_stats, transaction_details

@profit_bp.route('/')
@login_required
@permission_required('profit:stats:view')
def get_profit_stats():
    """获取盈利统计数据"""
    try:
        # 1. 获取查询参数
        user_id = session.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')
        holder_id = request.args.get('holder_id')

        # 获取用户关联的持有人ID
        holder_sql = "SELECT id FROM stock.holders WHERE user_id = %s"
        user_holders = db.fetch_all(holder_sql, [user_id])
        user_holder_ids = [h['id'] for h in user_holders]
        
        logger.info(f"用户 {user_id} 关联的持有人IDs: {user_holder_ids}")

        # 2. 构建查询条件
        conditions = []
        params = []

        # 修改用户ID条件，允许查看与用户关联的分单
        if user_holder_ids:
            holder_placeholders = ', '.join(['%s'] * len(user_holder_ids))
            conditions.append(f'(t.user_id = %s OR ts.holder_id IN ({holder_placeholders}))')
            params.append(user_id)
            params.extend(user_holder_ids)
        else:
            conditions.append('t.user_id = %s')
            params.append(user_id)

        if start_date:
            conditions.append('ts.transaction_date >= %s')
            params.append(start_date)
        if end_date:
            conditions.append('ts.transaction_date <= %s')
            params.append(end_date)
        if market:
            conditions.append('ts.market = %s')
            params.append(market)
        if holder_id:
            conditions.append('ts.holder_id = %s')
            params.append(holder_id)

        where_clause = ' AND '.join(conditions)

        # 3. 获取交易明细数据
        cte_sql = """
            WITH last_transaction_dates AS (
                SELECT 
                    ts.market COLLATE utf8mb4_unicode_ci as market,
                    ts.stock_code COLLATE utf8mb4_unicode_ci as stock_code,
                    MAX(ts.transaction_date) as last_transaction_date
                FROM stock.transaction_splits ts
                JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
                WHERE """
        
        if user_holder_ids:
            holder_placeholders = ', '.join(['%s'] * len(user_holder_ids))
            cte_sql += f"(t.user_id = %s OR ts.holder_id IN ({holder_placeholders}))"
            all_params_for_cte = [user_id] + user_holder_ids
        else:
            cte_sql += "t.user_id = %s"
            all_params_for_cte = [user_id]
            
        cte_sql += """
                GROUP BY ts.market, ts.stock_code
            )
        """
        
        main_sql = """
            SELECT 
                ts.id,
                ts.original_transaction_id,
                ts.market,
                ts.stock_code,
                ts.stock_name,
                UPPER(ts.transaction_type) as transaction_type,
                ts.transaction_date,
                ts.transaction_code,
                ts.holder_id,
                ts.holder_name,
                ts.split_ratio,
                ts.total_quantity,
                ts.total_amount,
                ts.broker_fee,
                ts.transaction_levy,
                ts.stamp_duty,
                ts.trading_fee,
                ts.deposit_fee,
                ts.prev_avg_cost,
                ts.current_avg_cost,
                (ts.broker_fee + ts.transaction_levy + ts.stamp_duty + ts.trading_fee + ts.deposit_fee) as total_fees,
                ts.created_at,
                ltd.last_transaction_date,
                1 as transaction_count
            FROM stock.transaction_splits ts
            JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
            LEFT JOIN stock.stocks s ON ts.stock_code COLLATE utf8mb4_unicode_ci = s.code AND ts.market COLLATE utf8mb4_unicode_ci = s.market
            LEFT JOIN last_transaction_dates ltd ON ts.market COLLATE utf8mb4_unicode_ci = ltd.market AND ts.stock_code COLLATE utf8mb4_unicode_ci = ltd.stock_code
            WHERE """ + where_clause + """
            ORDER BY ltd.last_transaction_date DESC, ts.transaction_date DESC, ts.id DESC
        """
        
        sql = cte_sql + main_sql

        # 在参数列表开头添加CTE的参数
        all_params = all_params_for_cte + params
        logger.info(f"执行SQL: {sql}")
        logger.info(f"参数: {all_params}")
        transactions = db.fetch_all(sql, all_params)
        logger.info(f"查询到 {len(transactions)} 条交易记录")

        # 4. 处理交易数据
        market_stats, stock_stats, transaction_details = process_transactions(transactions)

        # 5. 返回结果
        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats,
                'stock_stats': stock_stats,
                'transaction_details': transaction_details
            }
        })
    except Exception as e:
        logger.error(f"获取盈利统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取盈利统计失败: {str(e)}'
        }), 500

@profit_bp.route('/holding_stocks')
@login_required
@permission_required('profit:stats:view')
def get_holding_stocks_api():
    """获取持仓股票列表API"""
    try:
        # 获取查询参数
        user_id = session.get('user_id')
        holder_id = request.args.get('holder_id')
        
        # 获取用户关联的持有人ID
        holder_sql = "SELECT id FROM stock.holders WHERE user_id = %s"
        user_holders = db.fetch_all(holder_sql, [user_id])
        user_holder_ids = [h['id'] for h in user_holders]
        
        logger.info(f"用户 {user_id} 关联的持有人IDs: {user_holder_ids}")
        
        # 构建SQL查询
        cte_sql = """
        WITH last_transaction_dates AS (
            SELECT 
                ts.market COLLATE utf8mb4_unicode_ci as market,
                ts.stock_code COLLATE utf8mb4_unicode_ci as stock_code,
                MAX(ts.transaction_date) as last_transaction_date
            FROM stock.transaction_splits ts
            JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
            WHERE """
            
        if user_holder_ids:
            holder_placeholders = ', '.join(['%s'] * len(user_holder_ids))
            cte_sql += f"(t.user_id = %s OR ts.holder_id IN ({holder_placeholders}))"
            cte_params = [user_id] + user_holder_ids
        else:
            cte_sql += "t.user_id = %s"
            cte_params = [user_id]
            
        cte_sql += """
            GROUP BY ts.market, ts.stock_code
        )
        """
        
        avg_cost_sql = """
        (
            SELECT ts_last.current_avg_cost
            FROM stock.transaction_splits ts_last
            JOIN stock.stock_transactions t_last ON ts_last.original_transaction_id = t_last.id
            WHERE """
                
        if user_holder_ids:
            holder_placeholders = ', '.join(['%s'] * len(user_holder_ids))
            avg_cost_sql += f"(t_last.user_id = %s OR ts_last.holder_id IN ({holder_placeholders}))"
            avg_cost_params = [user_id] + user_holder_ids
        else:
            avg_cost_sql += "t_last.user_id = %s"
            avg_cost_params = [user_id]
            
        avg_cost_sql += """
              AND ts_last.market = ts.market
              AND ts_last.stock_code = ts.stock_code
              AND UPPER(ts_last.transaction_type) = 'BUY'
            ORDER BY ts_last.transaction_date DESC, ts_last.id DESC
            LIMIT 1
        ) as avg_cost
        """
        
        main_sql = """
        SELECT 
            ts.market,
            ts.stock_code,
            ts.stock_name,
            SUM(CASE WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.total_quantity ELSE -ts.total_quantity END) as holding_quantity,
            SUM(CASE WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.total_quantity ELSE 0 END) as total_buy_quantity,
            SUM(CASE WHEN UPPER(ts.transaction_type) = 'SELL' THEN ts.total_quantity ELSE 0 END) as total_sell_quantity,
            SUM(CASE WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.total_amount ELSE 0 END) as total_buy_amount,
            SUM(CASE WHEN UPPER(ts.transaction_type) = 'SELL' THEN ts.total_amount ELSE 0 END) as total_sell_amount,
            SUM(CASE WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.broker_fee + ts.transaction_levy + ts.stamp_duty + ts.trading_fee + ts.deposit_fee ELSE 0 END) as total_buy_fees,
            SUM(CASE WHEN UPPER(ts.transaction_type) = 'SELL' THEN ts.broker_fee + ts.transaction_levy + ts.stamp_duty + ts.trading_fee + ts.deposit_fee ELSE 0 END) as total_sell_fees,
        """ + avg_cost_sql + """,
            MAX(ltd.last_transaction_date) as last_transaction_date
        FROM stock.transaction_splits ts
        JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
        LEFT JOIN last_transaction_dates ltd ON ts.market COLLATE utf8mb4_unicode_ci = ltd.market AND ts.stock_code COLLATE utf8mb4_unicode_ci = ltd.stock_code
        WHERE """
        
        if user_holder_ids:
            holder_placeholders = ', '.join(['%s'] * len(user_holder_ids))
            main_sql += f"(t.user_id = %s OR ts.holder_id IN ({holder_placeholders}))"
            where_params = [user_id] + user_holder_ids
        else:
            main_sql += "t.user_id = %s"
            where_params = [user_id]
        
        # 合并所有参数
        params = cte_params + avg_cost_params + where_params
        
        if holder_id:
            main_sql += " AND ts.holder_id = %s"
            params.append(holder_id)
            
        main_sql += """
        GROUP BY ts.market, ts.stock_code, ts.stock_name
        HAVING SUM(CASE WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.total_quantity ELSE -ts.total_quantity END) > 0
        ORDER BY last_transaction_date DESC, ts.market, ts.stock_code
        """
        
        sql = cte_sql + main_sql
        
        logger.info(f"执行SQL: {sql}")
        logger.info(f"参数: {params}")
        stocks = db.fetch_all(sql, params)
        logger.info(f"查询到 {len(stocks)} 条持仓记录")
        
        # 处理结果
        result = []
        for stock in stocks:
            result.append({
                'market': stock['market'],
                'stock_code': stock['stock_code'],
                'stock_name': stock['stock_name'],
                'holding_quantity': float(stock['holding_quantity']),
                'total_buy_quantity': float(stock['total_buy_quantity']),
                'total_sell_quantity': float(stock['total_sell_quantity']),
                'total_buy_amount': float(stock['total_buy_amount']),
                'total_sell_amount': float(stock['total_sell_amount']),
                'total_buy_fees': float(stock['total_buy_fees']),
                'total_sell_fees': float(stock['total_sell_fees']),
                'avg_cost': float(stock['avg_cost']) if stock['avg_cost'] else 0,
                'last_transaction_date': stock['last_transaction_date'].strftime('%Y-%m-%d') if stock['last_transaction_date'] else None
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"获取持仓股票列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取持仓股票列表失败: {str(e)}'
        }), 500

@profit_bp.route('/refresh_prices', methods=['POST'])
@login_required
@permission_required('profit:stats:view')
def refresh_stock_prices():
    """刷新股票现价"""
    try:
        logger.info("开始刷新股票现价...")
        
        user_id = session.get('user_id')
        holder_id = request.args.get('holder_id')
        
        # 获取用户关联的持有人ID
        holder_sql = "SELECT id FROM stock.holders WHERE user_id = %s"
        user_holders = db.fetch_all(holder_sql, [user_id])
        user_holder_ids = [h['id'] for h in user_holders]
        
        logger.info(f"用户 {user_id} 关联的持有人IDs: {user_holder_ids}")
        
        # 获取持仓股票列表
        avg_cost_sql = """
                (
                    SELECT ts_last.current_avg_cost
                    FROM stock.transaction_splits ts_last
                    JOIN stock.stock_transactions t_last ON ts_last.original_transaction_id = t_last.id
                    WHERE """
                    
        if user_holder_ids:
            holder_placeholders = ', '.join(['%s'] * len(user_holder_ids))
            avg_cost_sql += f"(t_last.user_id = %s OR ts_last.holder_id IN ({holder_placeholders}))"
            avg_cost_params = [user_id] + user_holder_ids
        else:
            avg_cost_sql += "t_last.user_id = %s"
            avg_cost_params = [user_id]
            
        avg_cost_sql += """
                      AND ts_last.market = s.market
                      AND ts_last.stock_code = s.code
                      AND UPPER(ts_last.transaction_type) = 'BUY'
                    ORDER BY ts_last.transaction_date DESC, ts_last.id DESC
                    LIMIT 1
                ) as last_buy_avg_cost
        """
        
        main_sql = """
            SELECT 
                s.market,
                s.code,
                s.code_name as stock_name,
                s.google_name,
                SUM(CASE 
                    WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.total_quantity 
                    WHEN UPPER(ts.transaction_type) = 'SELL' THEN -ts.total_quantity 
                    ELSE 0 
                END) as quantity,
                SUM(CASE WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN UPPER(ts.transaction_type) = 'SELL' THEN ts.total_amount ELSE 0 END) as total_sell,
                SUM(ts.broker_fee + ts.transaction_levy + ts.stamp_duty + ts.trading_fee + ts.deposit_fee) as total_fees,
        """ + avg_cost_sql + """
            FROM stock.transaction_splits ts
            JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
            JOIN stock.stocks s ON ts.stock_code COLLATE utf8mb4_unicode_ci = s.code AND ts.market COLLATE utf8mb4_unicode_ci = s.market
            WHERE """
            
        if user_holder_ids:
            holder_placeholders = ', '.join(['%s'] * len(user_holder_ids))
            main_sql += f"(t.user_id = %s OR ts.holder_id IN ({holder_placeholders}))"
            where_params = [user_id] + user_holder_ids
        else:
            main_sql += "t.user_id = %s"
            where_params = [user_id]
        
        # 合并所有参数
        params = avg_cost_params + where_params
        
        if holder_id:
            main_sql += " AND ts.holder_id = %s"
            params.append(holder_id)
        
        main_sql += """
            GROUP BY s.market, s.code, s.code_name, s.google_name
            HAVING SUM(CASE 
                WHEN UPPER(ts.transaction_type) = 'BUY' THEN ts.total_quantity 
                WHEN UPPER(ts.transaction_type) = 'SELL' THEN -ts.total_quantity 
                ELSE 0 
            END) > 0
        """
        
        sql = main_sql
        
        logger.info(f"查询用户 {user_id} 的持仓股票")
        logger.info(f"执行SQL: {sql}")
        logger.info(f"参数: {params}")
        stocks = db.fetch_all(sql, params)
        logger.info(f"查询到 {len(stocks)} 条持仓记录")
        
        results = []
        success_count = 0
        failed_count = 0
        
        for stock in stocks:
            quantity = float(stock['quantity'])
            total_buy = float(stock['total_buy'])
            total_sell = float(stock['total_sell'])
            total_fees = float(stock['total_fees'])
            last_buy_avg_cost = float(stock['last_buy_avg_cost'] or 0)
            
            logger.info(f"处理股票: {stock['market']}-{stock['code']} ({stock['stock_name']})")
            logger.info(f"持仓数量: {quantity}, 买入总额: {total_buy}, 卖出总额: {total_sell}, 总费用: {total_fees}")
            
            try:
                # 获取当前股价
                query = stock['google_name']
                logger.info(f"查询股价: {query}")
                price_result = checker.get_stock_price(query)
                logger.info(f"获取到的股价: {price_result}")
                
                if price_result is not None:
                    current_price = float(price_result)
                    # 计算市值
                    market_value = current_price * quantity
                    logger.info(f"当前价格: {current_price}, 市值: {market_value}")
                    
                    # 使用最后一次买入的移动加权平均价格作为平均成本
                    avg_cost = last_buy_avg_cost
                    logger.info(f"移动加权平均成本: {avg_cost}")
                    
                    # 计算持仓盈亏
                    holding_profit = (current_price - avg_cost) * quantity
                    logger.info(f"持仓盈亏: {holding_profit}")
                    
                    # 获取已实现盈亏
                    realized_profit_sql = """
                        SELECT 
                            SUM(
                                CASE 
                                    WHEN UPPER(ts.transaction_type) = 'SELL' THEN 
                                        ts.total_amount - (ts.total_quantity * ts.prev_avg_cost) - 
                                        (ts.broker_fee + ts.transaction_levy + ts.stamp_duty + ts.trading_fee + ts.deposit_fee)
                                    ELSE 0 
                                END
                            ) as total_realized_profit
                        FROM stock.transaction_splits ts
                        JOIN stock.stock_transactions t ON ts.original_transaction_id = t.id
                        WHERE t.user_id = %s 
                          AND ts.stock_code = %s 
                          AND ts.market = %s
                    """
                    
                    realized_params = [user_id, stock['code'], stock['market']]
                    if holder_id:
                        realized_profit_sql += " AND ts.holder_id = %s"
                        realized_params.append(holder_id)
                    
                    realized_profit_record = db.fetch_one(realized_profit_sql, realized_params)
                    realized_profit = float(realized_profit_record['total_realized_profit'] or 0) if realized_profit_record else 0
                    logger.info(f"已实现盈亏: {realized_profit}")
                    
                    # 计算总盈亏
                    total_profit = holding_profit + realized_profit
                    logger.info(f"总盈亏: {total_profit}")
                    
                    # 计算盈亏率
                    profit_rate = (total_profit / total_buy * 100) if total_buy > 0 else 0
                    logger.info(f"盈亏率: {profit_rate}%")
                    
                    results.append({
                        'market': stock['market'],
                        'code': stock['code'],
                        'name': stock['stock_name'],
                        'current_price': current_price,
                        'quantity': quantity,
                        'market_value': market_value,
                        'avg_cost': avg_cost,
                        'holding_profit': holding_profit,
                        'realized_profit': realized_profit,
                        'total_profit': total_profit,
                        'profit_rate': profit_rate
                    })
                    success_count += 1
                    logger.info(f"股票 {stock['market']}-{stock['code']} 处理成功")
                else:
                    failed_count += 1
                    logger.error(f"获取股价失败 {stock['market']}:{stock['code']}: 未获取到价格")
            except Exception as e:
                failed_count += 1
                logger.error(f"获取股价失败 {stock['market']}:{stock['code']}: {str(e)}")
        
        logger.info(f"股价刷新完成: {success_count} 个成功, {failed_count} 个失败")
        return jsonify({
            'success': True,
            'data': {
                'items': results,
                'success_count': success_count,
                'failed_count': failed_count
            }
        })
    except Exception as e:
        logger.error(f"刷新股价失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '刷新股价失败'
        }), 500 