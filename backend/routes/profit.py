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

def process_transactions(transactions):
    """处理交易数据，生成统计信息"""
    market_stats = {}
    stock_stats = {}
    transaction_details = {}
    
    # 按日期排序交易记录
    transactions.sort(key=lambda x: (x['transaction_date'], x['id']))
    
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
def get_profit_stats():
    """获取盈利统计数据"""
    try:
        # 1. 获取查询参数
        user_id = session.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')

        # 2. 构建查询条件
        conditions = ['t.user_id = %s']
        params = [user_id]

        if start_date:
            conditions.append('t.transaction_date >= %s')
            params.append(start_date)
        if end_date:
            conditions.append('t.transaction_date <= %s')
            params.append(end_date)
        if market:
            conditions.append('t.market = %s')
            params.append(market)

        where_clause = ' AND '.join(conditions)

        # 3. 获取交易明细数据
        sql = f"""
            WITH last_transaction_dates AS (
                SELECT 
                    market,
                    stock_code,
                    MAX(transaction_date) as last_transaction_date
                FROM stock.stock_transactions
                WHERE user_id = %s
                GROUP BY market, stock_code
            )
            SELECT 
                t.id,
                t.market,
                t.stock_code,
                s.code_name as stock_name,
                UPPER(t.transaction_type) as transaction_type,
                t.transaction_date,
                t.transaction_code,
                t.total_quantity,
                t.total_amount,
                t.broker_fee,
                t.transaction_levy,
                t.stamp_duty,
                t.trading_fee,
                t.deposit_fee,
                t.prev_avg_cost,
                t.current_avg_cost,
                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                t.created_at,
                ltd.last_transaction_date,
                1 as transaction_count
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            LEFT JOIN last_transaction_dates ltd ON t.market = ltd.market AND t.stock_code = ltd.stock_code
            WHERE {where_clause}
            ORDER BY ltd.last_transaction_date DESC, t.transaction_date DESC, t.id DESC
        """

        # 在参数列表开头添加user_id参数
        all_params = [user_id] + params
        transactions = db.fetch_all(sql, all_params)

        # 4. 处理数据
        market_stats, stock_stats, transaction_details = process_transactions(transactions)

        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats,
                'stock_stats': stock_stats,
                'transaction_details': transaction_details
            }
        })

    except Exception as e:
        print(f"Error in get_profit_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取盈利统计数据失败: {str(e)}'
        })

def get_holding_stocks():
    try:
        with get_db().cursor() as cursor:
            # 获取每个股票的最后交易日期
            cursor.execute("""
            WITH last_transaction_dates AS (
                SELECT 
                    market,
                    stock_code,
                    MAX(transaction_date) as last_transaction_date
                FROM stock.stock_transactions
                GROUP BY market, stock_code
            )
            SELECT 
                t.market,
                t.stock_code,
                s.name as stock_name,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'BUY' THEN t.total_quantity ELSE -t.total_quantity END) as holding_quantity,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'BUY' THEN t.total_quantity ELSE 0 END) as total_buy_quantity,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'SELL' THEN t.total_quantity ELSE 0 END) as total_sell_quantity,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'BUY' THEN t.total_amount ELSE 0 END) as total_buy_amount,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'SELL' THEN t.total_amount ELSE 0 END) as total_sell_amount,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'BUY' THEN t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee ELSE 0 END) as total_buy_fees,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'SELL' THEN t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee ELSE 0 END) as total_sell_fees,
                MAX(CASE WHEN UPPER(t.transaction_type) = 'BUY' THEN t.current_avg_cost ELSE NULL END) as avg_cost,
                MAX(ltd.last_transaction_date) as last_transaction_date
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            LEFT JOIN last_transaction_dates ltd ON t.market = ltd.market AND t.stock_code = ltd.stock_code
            GROUP BY t.market, t.stock_code, s.name
            HAVING SUM(CASE WHEN UPPER(t.transaction_type) = 'BUY' THEN t.total_quantity ELSE -t.total_quantity END) > 0
            ORDER BY last_transaction_date DESC, t.market, t.stock_code
            """)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_holding_stocks: {str(e)}")
        return []
    finally:
        cursor.close()

@profit_bp.route('/refresh_prices', methods=['POST'])
@login_required
def refresh_stock_prices():
    """刷新股票现价"""
    try:
        logger.info("开始刷新股票现价...")
        # 获取持仓股票列表
        sql = """
            SELECT 
                s.market,
                s.code,
                s.code_name as stock_name,
                s.google_name,
                SUM(CASE 
                    WHEN UPPER(t.transaction_type) = 'BUY' THEN t.total_quantity 
                    WHEN UPPER(t.transaction_type) = 'SELL' THEN -t.total_quantity 
                    ELSE 0 
                END) as quantity,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'BUY' THEN t.total_amount ELSE 0 END) as total_buy,
                SUM(CASE WHEN UPPER(t.transaction_type) = 'SELL' THEN t.total_amount ELSE 0 END) as total_sell,
                SUM(t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees
            FROM stock.stock_transactions t
            JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE t.user_id = %s
            GROUP BY s.market, s.code, s.code_name, s.google_name
            HAVING SUM(CASE 
                WHEN UPPER(t.transaction_type) = 'BUY' THEN t.total_quantity 
                WHEN UPPER(t.transaction_type) = 'SELL' THEN -t.total_quantity 
                ELSE 0 
            END) > 0
        """
        
        user_id = session.get('user_id')
        logger.info(f"查询用户 {user_id} 的持仓股票")
        stocks = db.fetch_all(sql, [user_id])
        logger.info(f"找到 {len(stocks)} 支持仓股票")
        
        results = []
        success_count = 0
        failed_count = 0
        
        for stock in stocks:
            quantity = float(stock['quantity'])
            total_buy = float(stock['total_buy'])
            total_sell = float(stock['total_sell'])
            total_fees = float(stock['total_fees'])
            
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
                    
                    # 获取最后一次买入时的移动加权平均价
                    avg_cost_sql = """
                        SELECT current_avg_cost
                        FROM stock_transactions
                        WHERE user_id = %s 
                          AND stock_code = %s 
                          AND market = %s
                          AND UPPER(transaction_type) = 'BUY'
                        ORDER BY transaction_date DESC, id DESC
                        LIMIT 1
                    """
                    latest_record = db.fetch_one(avg_cost_sql, [user_id, stock['code'], stock['market']])
                    avg_cost = float(latest_record['current_avg_cost']) if latest_record else 0
                    logger.info(f"最新买入均价: {avg_cost}")
                    
                    # 计算持仓成本
                    holding_cost = quantity * avg_cost
                    logger.info(f"持仓成本: {holding_cost}")
                    
                    # 计算持仓盈亏 = 市值 - 持仓成本
                    holding_profit = market_value - holding_cost
                    logger.info(f"持仓盈亏: {holding_profit}")
                    
                    # 获取已实现盈亏
                    realized_profit_sql = """
                        SELECT 
                            SUM(
                                CASE 
                                    WHEN UPPER(t.transaction_type) = 'SELL' THEN 
                                        t.total_amount - (t.total_quantity * t.prev_avg_cost) - 
                                        (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                                    ELSE 0 
                                END
                            ) as total_realized_profit
                        FROM stock_transactions t
                        WHERE t.user_id = %s 
                          AND t.stock_code = %s 
                          AND t.market = %s
                    """
                    realized_profit_record = db.fetch_one(realized_profit_sql, [user_id, stock['code'], stock['market']])
                    realized_profit = float(realized_profit_record['total_realized_profit'] or 0) if realized_profit_record else 0
                    logger.info(f"已实现盈亏: {realized_profit}")
                    
                    # 总盈亏 = 已实现盈亏 + 持仓盈亏
                    total_profit = realized_profit + holding_profit
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