from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models import db, StockTransaction, StockTransactionDetail, ExchangeRate, Stock
from routes.auth import login_required
from datetime import datetime, timedelta
from sqlalchemy import distinct
from utils.exchange_rate import ensure_exchange_rate_exists, get_exchange_rate
from collections import defaultdict
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from sqlalchemy import or_

stock_bp = Blueprint('stock', __name__)

def calculate_stats(transactions):
    """计算交易统计数据
    使用FIFO方法计算卖出交易的盈亏
    对USA市场同时计算美元和港币金额
    """
    market_stats = {}
    stock_stats = {}
    
    # 初始化市场统计
    def init_market_stats():
        return {
            'transaction_count': 0,  # 交易笔数
            'total_buy': 0,         # 买入总额(HKD)
            'total_buy_usd': 0,     # 买入总额(USD，仅USA市场)
            'total_sell': 0,        # 卖出总额(HKD)
            'total_sell_usd': 0,    # 卖出总额(USD，仅USA市场)
            'total_fees': 0,        # 总费用(HKD)
            'total_fees_usd': 0,    # 总费用(USD，仅USA市场)
            'realized_profit': 0,   # 已实现盈亏(HKD)
            'realized_profit_usd': 0, # 已实现盈亏(USD，仅USA市场)
            'market_value': 0,      # 当前市值(HKD)
            'market_value_usd': 0,  # 当前市值(USD，仅USA市场)
            'total_profit': 0,      # 总盈亏(HKD)
            'total_profit_usd': 0,  # 总盈亏(USD，仅USA市场)
            'profit_rate': 0,       # 总盈亏比例
            'exchange_rate': 1.0    # 当前汇率，默认为1.0
        }
    
    # 初始化股票统计
    def init_stock_stats():
        return {
            'market': '',              # 市场
            'name': '',               # 添加公司名称字段
            'current_quantity': 0,     # 当前持仓数量
            'total_buy_quantity': 0,   # 总买入数量
            'transaction_count': 0,    # 交易笔数
            'total_buy': 0,           # 买入总额(HKD)
            'total_buy_usd': 0,       # 买入总额(USD，仅USA市场)
            'total_sell': 0,          # 卖出总额(HKD)
            'total_sell_usd': 0,      # 卖出总额(USD，仅USA市场)
            'total_fees': 0,          # 总费用(HKD)
            'total_fees_usd': 0,      # 总费用(USD，仅USA市场)
            'avg_cost': 0,            # 平均成本(HKD)
            'avg_cost_usd': 0,        # 平均成本(USD，仅USA市场)
            'realized_profit': 0,      # 已实现盈亏(HKD)
            'realized_profit_usd': 0,  # 已实现盈亏(USD，仅USA市场)
            'market_value': 0,         # 当前市值(HKD)
            'market_value_usd': 0,     # 当前市值(USD，仅USA市场)
            'total_profit': 0,         # 总盈亏(HKD)
            'total_profit_usd': 0,     # 总盈亏(USD，仅USA市场)
            'profit_rate': 0,          # 总盈亏比例
            'current_price': 0,        # 当前价格
            'transactions': [],        # 交易记录
            'fifo_queue': [],         # FIFO队列
            'exchange_rate': 1.0       # 当前汇率，默认为1.0
        }
    
    # 按时间顺序处理交易
    for trans in sorted(transactions, key=lambda x: (x.transaction_date, x.created_at), reverse=True):
        market = trans.market
        code = trans.stock_code
        
        # 初始化市场统计
        if market not in market_stats:
            market_stats[market] = init_market_stats()
        
        # 初始化股票统计
        if code not in stock_stats:
            stock_stats[code] = init_stock_stats()
            stock_stats[code]['market'] = market
            # 获取并设置公司名称
            stock = Stock.query.filter_by(code=code, market=market).first()
            if stock:
                stock_stats[code]['name'] = stock.name
        
        stock = stock_stats[code]
        
        # 更新基本统计数据
        stock['transaction_count'] += 1
        market_stats[market]['transaction_count'] += 1
        
        if market == 'USA':
            stock['total_fees_usd'] += trans.total_fees
            market_stats[market]['total_fees_usd'] += trans.total_fees
            stock['total_fees'] += trans.total_fees * trans.exchange_rate
            market_stats[market]['total_fees'] += trans.total_fees * trans.exchange_rate
        else:
            stock['total_fees'] += trans.total_fees
            market_stats[market]['total_fees'] += trans.total_fees
        
        if trans.transaction_type == 'BUY':
            # 买入交易处理
            stock['current_quantity'] += trans.total_quantity
            stock['total_buy_quantity'] += trans.total_quantity  # 更新总买入数量
            
            if market == 'USA':
                stock['total_buy_usd'] += trans.total_amount
                market_stats[market]['total_buy_usd'] += trans.total_amount
                stock['total_buy'] += trans.total_amount_hkd
                market_stats[market]['total_buy'] += trans.total_amount_hkd
                stock['avg_cost_usd'] = stock['total_buy_usd'] / stock['current_quantity'] if stock['current_quantity'] > 0 else 0
            else:
                stock['total_buy'] += trans.total_amount
                market_stats[market]['total_buy'] += trans.total_amount
            
            stock['avg_cost'] = stock['total_buy'] / stock['current_quantity'] if stock['current_quantity'] > 0 else 0
            
            # 添加到FIFO队列，包含买入费用
            stock['fifo_queue'].append({
                'quantity': trans.total_quantity,
                'price': trans.total_amount / trans.total_quantity,  # 原始币种单位成本
                'price_hkd': trans.total_amount_hkd / trans.total_quantity,  # 港币单位成本
                'date': trans.transaction_date,
                'exchange_rate': trans.exchange_rate,
                'fees': trans.total_fees,  # 记录买入费用
                'total_cost': trans.total_amount + trans.total_fees,  # 总成本（含费用）
                'total_cost_hkd': trans.total_amount_hkd + trans.total_fees  # 港币总成本（含费用）
            })
            
            # 记录买入交易详情
            trans_detail = {
                'transaction_date': trans.transaction_date,
                'transaction_type': trans.transaction_type,
                'transaction_code': trans.transaction_code,
                'total_quantity': trans.total_quantity,
                'total_amount': trans.total_amount,
                'total_amount_hkd': trans.total_amount_hkd,
                'average_price': trans.average_price,
                'total_fees': trans.total_fees,
                'exchange_rate': trans.exchange_rate
            }
            
            stock['transactions'].append(trans_detail)
            
        else:  # SELL
            # 卖出交易处理
            stock['current_quantity'] -= trans.total_quantity
            
            if market == 'USA':
                stock['total_sell_usd'] += trans.total_amount
                market_stats[market]['total_sell_usd'] += trans.total_amount
                stock['total_sell'] += trans.total_amount_hkd
                market_stats[market]['total_sell'] += trans.total_amount_hkd
            else:
                stock['total_sell'] += trans.total_amount
                market_stats[market]['total_sell'] += trans.total_amount
            
            # 计算FIFO成本和盈亏
            remaining_quantity = trans.total_quantity
            total_cost = 0  # 原始币种的总成本（含买入费用）
            total_cost_hkd = 0  # 港币总成本（含买入费用）
            fifo_cost_details = []  # FIFO成本明细
            
            while remaining_quantity > 0 and stock['fifo_queue']:
                buy_record = stock['fifo_queue'][0]
                used_quantity = min(remaining_quantity, buy_record['quantity'])
                
                # 计算这部分股票的成本（包含买入费用）
                cost_ratio = used_quantity / buy_record['quantity']
                unit_cost = buy_record['price']  # 原始币种单位成本
                unit_cost_hkd = buy_record['price_hkd']  # 港币单位成本
                buy_fees = buy_record['fees'] * cost_ratio  # 分摊的买入费用
                
                cost = unit_cost * used_quantity + buy_fees  # 原始币种成本（含买入费用）
                cost_hkd = unit_cost_hkd * used_quantity + buy_fees  # 港币成本（含买入费用）
                
                # 记录FIFO成本明细
                fifo_cost_details.append({
                    'date': buy_record['date'],
                    'quantity': used_quantity,
                    'price': unit_cost,
                    'price_hkd': unit_cost_hkd,
                    'cost': cost,
                    'cost_hkd': cost_hkd,
                    'exchange_rate': buy_record['exchange_rate'],
                    'fees': buy_fees  # 记录分摊的买入费用
                })
                
                total_cost += cost
                total_cost_hkd += cost_hkd
                
                # 更新或移除买入记录
                buy_record['quantity'] -= used_quantity
                if buy_record['quantity'] == 0:
                    stock['fifo_queue'].pop(0)
                remaining_quantity -= used_quantity
            
            # 计算利润（减去所有相关费用）
            if market == 'USA':
                # 美股：直接用美元计算
                net_income = trans.total_amount - trans.total_fees  # 卖出净收入
                profit_usd = net_income - total_cost  # 利润 = 净收入 - 总成本（已包含买入费用）
                profit_hkd = profit_usd * trans.exchange_rate
                profit_rate = profit_usd / total_cost if total_cost > 0 else 0
                
                stock['realized_profit_usd'] += profit_usd
                market_stats[market]['realized_profit_usd'] += profit_usd
                stock['realized_profit'] += profit_hkd
                market_stats[market]['realized_profit'] += profit_hkd
            else:
                # 港股：直接用港币计算
                net_income = trans.total_amount_hkd - trans.total_fees  # 卖出净收入
                profit = net_income - total_cost_hkd  # 利润 = 净收入 - 总成本（已包含买入费用）
                profit_rate = profit / total_cost_hkd if total_cost_hkd > 0 else 0
                
                stock['realized_profit'] += profit
                market_stats[market]['realized_profit'] += profit
            
            # 记录卖出交易详情
            trans_detail = {
                'transaction_date': trans.transaction_date,
                'transaction_type': trans.transaction_type,
                'transaction_code': trans.transaction_code,
                'total_quantity': trans.total_quantity,
                'total_amount': trans.total_amount,
                'total_amount_hkd': trans.total_amount_hkd,
                'average_price': trans.average_price,
                'total_fees': trans.total_fees,
                'exchange_rate': trans.exchange_rate,
                'fifo_price': total_cost / trans.total_quantity if trans.total_quantity > 0 else 0,
                'fifo_price_hkd': total_cost_hkd / trans.total_quantity if trans.total_quantity > 0 else 0,
                'profit': profit_usd if market == 'USA' else profit,
                'profit_rate': profit_rate,
                'fifo_cost_details': fifo_cost_details
            }
            
            stock['transactions'].append(trans_detail)
    
    # 计算当前市值和总盈亏
    for code, stock in stock_stats.items():
        if stock['current_quantity'] > 0:
            # 获取当前价格
            current_price = get_stock_price(code, stock['market'])
            if current_price:
                stock['current_price'] = current_price['price']
                
                # 计算市值
                if stock['market'] == 'USA':
                    # 获取当前汇率
                    exchange_rate = get_exchange_rate('USD', datetime.now().strftime('%Y-%m-%d'))
                    if exchange_rate:
                        stock['exchange_rate'] = exchange_rate
                        market_stats[stock['market']]['exchange_rate'] = exchange_rate
                        
                        # 计算美元市值
                        market_value_usd = stock['current_price'] * stock['current_quantity']
                        stock['market_value_usd'] = market_value_usd
                        market_stats[stock['market']]['market_value_usd'] += market_value_usd
                        
                        # 计算港币市值
                        market_value_hkd = market_value_usd * exchange_rate
                        stock['market_value'] = market_value_hkd
                        market_stats[stock['market']]['market_value'] += market_value_hkd
                        
                        # 计算未实现盈亏（美元）
                        # 当前持仓成本 = 平均成本 * 数量 + 剩余持仓对应的买入费用
                        remaining_buy_fees_usd = stock['total_fees_usd'] * (stock['current_quantity'] / stock['total_buy_quantity'])
                        current_position_cost_usd = (stock['avg_cost_usd'] * stock['current_quantity']) + remaining_buy_fees_usd
                        unrealized_profit_usd = market_value_usd - current_position_cost_usd
                        
                        # 总盈亏 = 已实现盈亏 + 未实现盈亏
                        stock['total_profit_usd'] = stock['realized_profit_usd'] + unrealized_profit_usd
                        
                        # 计算未实现盈亏（港币）
                        remaining_buy_fees_hkd = stock['total_fees'] * (stock['current_quantity'] / stock['total_buy_quantity'])
                        current_position_cost_hkd = (stock['avg_cost'] * stock['current_quantity']) + remaining_buy_fees_hkd
                        unrealized_profit_hkd = market_value_hkd - current_position_cost_hkd
                        
                        # 总盈亏（港币） = 已实现盈亏 + 未实现盈亏
                        stock['total_profit'] = stock['realized_profit'] + unrealized_profit_hkd
                        
                        # 计算盈亏率（使用美元）
                        total_cost_with_fees_usd = current_position_cost_usd + stock['total_fees_usd'] * (stock['total_buy_quantity'] - stock['current_quantity']) / stock['total_buy_quantity']
                        if total_cost_with_fees_usd > 0:
                            stock['profit_rate'] = stock['total_profit_usd'] / total_cost_with_fees_usd * 100
                else:
                    # 港股：直接用港币计算
                    market_value = stock['current_price'] * stock['current_quantity']
                    stock['market_value'] = market_value
                    market_stats[stock['market']]['market_value'] += market_value
                    
                    # 计算未实现盈亏，包含费用成本
                    remaining_buy_fees = stock['total_fees'] * (stock['current_quantity'] / stock['total_buy_quantity'])
                    current_position_cost = (stock['avg_cost'] * stock['current_quantity']) + remaining_buy_fees
                    unrealized_profit = market_value - current_position_cost
                    
                    # 总盈亏 = 已实现盈亏 + 未实现盈亏
                    stock['total_profit'] = stock['realized_profit'] + unrealized_profit
                    
                    # 计算盈亏率
                    total_cost_with_fees = current_position_cost + stock['total_fees'] * (stock['total_buy_quantity'] - stock['current_quantity']) / stock['total_buy_quantity']
                    if total_cost_with_fees > 0:
                        stock['profit_rate'] = stock['total_profit'] / total_cost_with_fees * 100
    
    # 计算市场级别的总盈亏和盈亏率
    for market, stats in market_stats.items():
        if market == 'USA':
            # 美股市场：美元计算
            # 总盈亏 = 已实现盈亏 + 未实现盈亏
            # 未实现盈亏 = 当前市值 - 当前持仓成本
            # 当前持仓成本 = 总买入 - 已卖出部分的成本（等于已实现盈亏 + 卖出金额 - 卖出费用）
            current_position_cost_usd = stats['total_buy_usd'] - (stats['realized_profit_usd'] + stats['total_sell_usd'] - stats['total_fees_usd'])
            unrealized_profit_usd = stats['market_value_usd'] - current_position_cost_usd
            stats['total_profit_usd'] = stats['realized_profit_usd'] + unrealized_profit_usd
            
            # 港币计算
            current_position_cost_hkd = stats['total_buy'] - (stats['realized_profit'] + stats['total_sell'] - stats['total_fees'])
            unrealized_profit_hkd = stats['market_value'] - current_position_cost_hkd
            stats['total_profit'] = stats['realized_profit'] + unrealized_profit_hkd
            
            # 计算盈亏率（使用美元）
            if stats['total_buy_usd'] > 0:
                stats['profit_rate'] = stats['total_profit_usd'] / stats['total_buy_usd'] * 100
        else:
            # 港股市场：港币计算
            current_position_cost = stats['total_buy'] - (stats['realized_profit'] + stats['total_sell'] - stats['total_fees'])
            unrealized_profit = stats['market_value'] - current_position_cost
            stats['total_profit'] = stats['realized_profit'] + unrealized_profit
            
            # 计算盈亏率
            if stats['total_buy'] > 0:
                stats['profit_rate'] = stats['total_profit'] / stats['total_buy'] * 100
    
    # 将股票分为持仓和已清仓两组
    holding_stocks = {}
    closed_stocks = {}
    
    for code, stock in stock_stats.items():
        if stock['current_quantity'] > 0:
            holding_stocks[code] = stock
        else:
            closed_stocks[code] = stock
    
    # 分别对持仓和已清仓股票按最新交易日期和系统时间排序
    def get_latest_transaction_info(transactions):
        if not transactions:
            return (datetime.min, datetime.min)
        latest = max(transactions, key=lambda x: (x['transaction_date'], x.get('created_at', datetime.min)))
        return (latest['transaction_date'], latest.get('created_at', datetime.min))
    
    sorted_holding_stocks = dict(sorted(
        holding_stocks.items(),
        key=lambda x: get_latest_transaction_info(x[1]['transactions']),
        reverse=True
    ))
    
    sorted_closed_stocks = dict(sorted(
        closed_stocks.items(),
        key=lambda x: get_latest_transaction_info(x[1]['transactions']),
        reverse=True
    ))
    
    # 合并排序后的结果
    sorted_stock_stats = {**sorted_holding_stocks, **sorted_closed_stocks}
    
    # 对每个股票的交易记录按日期和创建时间排序
    for code in sorted_stock_stats:
        sorted_stock_stats[code]['transactions'].sort(
            key=lambda x: (x['transaction_date'], x.get('created_at', datetime.min)),
            reverse=True
        )
    
    return market_stats, sorted_stock_stats

def get_holding_stocks(user_id):
    """获取用户的持仓股票"""
    # 使用calculate_stats函数获取持仓信息
    transactions = StockTransaction.query.filter_by(user_id=user_id).all()
    stats_data = calculate_stats(transactions)
    
    # 提取持仓股票
    holding_stocks = []
    for code, stock in stats_data['stock_stats'].items():
        if stock['current_quantity'] > 0:
            holding_stocks.append({
                'code': code,
                'market': stock['market'],
                'quantity': stock['current_quantity'],
                'avg_price': stock['avg_cost']
            })
    
    return holding_stocks

def get_stock_symbol(code, market):
    """转换股票代码为 Yahoo Finance 格式"""
    if market == 'HK':
        return f"{code}.HK"
    else:  # USA
        return code

def get_stock_price(code, market):
    """获取单个股票的实时价格"""
    try:
        # 从数据库获取股票信息
        stock = Stock.query.filter_by(code=code, market=market).first()
        if not stock:
            print(f"数据库中未找到股票: {market} {code}")
            return None
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        url = None
        if stock.full_name:  # 优先使用保存的谷歌查询代码
            url = f'https://www.google.com/finance/quote/{stock.full_name}'
        else:
            if market == 'HK':
                # 港股代码需要补足4位
                padded_code = code.zfill(4)
                url = f'https://www.google.com/finance/quote/{padded_code}:HKG'
            elif market == 'USA':
                # 设置请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                # 先尝试NASDAQ
                try:
                    test_url = f'https://www.google.com/finance/quote/{code}:NASDAQ'
                    print(f"尝试NASDAQ: {test_url}")
                    response = requests.get(test_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        price_div = soup.find('div', {'data-last-price': True})
                        if price_div and price_div.get('data-last-price'):
                            url = test_url
                            stock.full_name = f"{code}:NASDAQ"
                            db.session.commit()
                            print("在NASDAQ找到股票")
                except Exception as e:
                    print(f"NASDAQ查询失败: {str(e)}")
                    url = None

                # 如果NASDAQ查询失败，尝试NYSE
                if not url:
                    try:
                        test_url = f'https://www.google.com/finance/quote/{code}:NYSE'
                        print(f"尝试NYSE: {test_url}")
                        response = requests.get(test_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            price_div = soup.find('div', {'data-last-price': True})
                            if price_div and price_div.get('data-last-price'):
                                url = test_url
                                stock.full_name = f"{code}:NYSE"
                                db.session.commit()
                                print("在NYSE找到股票")
                    except Exception as e:
                        print(f"NYSE查询失败: {str(e)}")
                        url = None

                if not url:
                    # 如果两个交易所都查询失败
                    raise ValueError(f"股票 {code} 在NASDAQ和NYSE均未找到")
        
        print(f"最终访问URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        price_div = soup.find('div', {'data-last-price': True})
        
        if price_div and price_div.get('data-last-price'):
            price = float(price_div.get('data-last-price'))
            return {
                'code': code,
                'market': market,
                'currency': 'HKD' if market == 'HK' else 'USD',
                'price': price,
                'timestamp': datetime.now()
            }
            
        print("未能从页面解析到股价数据")
        return None
        
    except Exception as e:
        print(f"获取股价失败: {str(e)}")
        return None

def get_multiple_quotes(stock_list):
    """批量获取多个股票的实时价格"""
    result = {}
    for market, code in stock_list:
        quote = get_stock_price(code, market)
        if quote:
            result[code] = quote
    return result

@stock_bp.route('/api/portfolio/market-value')
@login_required
def get_portfolio_market_value():
    """获取持仓股票的当前市值"""
    try:
        # 获取持仓股票
        holdings = get_holding_stocks(session['user_id'])
        if not holdings:
            return jsonify({
                'success': True,
                'data': {
                    'holdings': [],
                    'total_value_hkd': 0
                }
            })
        
        # 获取当前汇率
        today = datetime.now().strftime('%Y-%m-%d')
        usd_rate = get_exchange_rate('USD', today)
        
        # 获取实时报价
        stocks = [(h['market'], h['code']) for h in holdings]
        quotes = get_multiple_quotes(stocks)
        
        # 计算市值
        total_value_hkd = 0
        holdings_data = []
        
        for holding in holdings:
            quote = quotes.get(holding['code'])
            if not quote:
                continue
            
            # 计算市值（转换为港币）
            if quote['market'] == 'HK':
                market_value_hkd = quote['price'] * holding['quantity']
            else:  # USA
                market_value_hkd = quote['price'] * holding['quantity'] * usd_rate
            
            # 更新持仓信息
            holding_data = {
                'code': holding['code'],
                'market': holding['market'],
                'quantity': holding['quantity'],
                'avg_price': holding['avg_price'],
                'current_price': quote['price'],
                'currency': quote['currency'],
                'market_value': quote['price'] * holding['quantity'],
                'market_value_hkd': market_value_hkd,
                'unrealized_profit': market_value_hkd - (holding['avg_price'] * holding['quantity'])
            }
            holdings_data.append(holding_data)
            total_value_hkd += market_value_hkd
        
        return jsonify({
            'success': True,
            'data': {
                'holdings': holdings_data,
                'total_value_hkd': total_value_hkd,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@stock_bp.route('/stock/codes')
@login_required
def get_stock_codes():
    # 获取当前用户的所有不重复的股票代码
    user_id = session.get('user_id')
    codes = db.session.query(StockTransaction.stock_code)\
        .filter_by(user_id=user_id)\
        .distinct()\
        .order_by(StockTransaction.stock_code)\
        .all()
    return jsonify([code[0] for code in codes])

@stock_bp.route('/stock/list')
@login_required
def list():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stock_codes = request.args.getlist('stock_codes')
    
    query = StockTransaction.query.filter_by(user_id=session['user_id'])
    
    if start_date:
        query = query.filter(StockTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(StockTransaction.transaction_date <= end_date)
    if stock_codes:
        query = query.filter(StockTransaction.stock_code.in_(stock_codes))
    
    transactions = query.order_by(StockTransaction.created_at.desc()).all()
    
    # 获取所有股票代码供查询使用
    all_stock_codes = db.session.query(StockTransaction.stock_code)\
        .filter_by(user_id=session['user_id'])\
        .distinct()\
        .order_by(StockTransaction.stock_code)\
        .all()
    all_stock_codes = [code[0] for code in all_stock_codes]
    
    # 获取股票名称
    stock_codes = set(t.stock_code for t in transactions)
    stocks = Stock.query.filter(Stock.code.in_(stock_codes)).all()
    stock_names = {s.code: s.name for s in stocks}
    
    return render_template('stock/list.html', 
                         transactions=transactions,
                         all_stock_codes=all_stock_codes,
                         selected_stock_codes=stock_codes,
                         stock_names=stock_names)

@stock_bp.route('/stock/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            # 获取基本信息
            transaction_date = datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d')
            stock_code = request.form.get('stock_code')
            market = request.form.get('market')
            transaction_code = request.form.get('transaction_code')
            transaction_type = request.form.get('transaction_type')
            
            # 检查交易编号是否已存在
            existing_transaction = StockTransaction.query.filter_by(
                user_id=session['user_id'],
                transaction_code=transaction_code
            ).first()
            if existing_transaction:
                return jsonify({
                    'success': False,
                    'error': '交易编号已存在，请使用其他编号'
                })
            
            # 如果是非港股市场，获取汇率
            exchange_rate = None
            if market != 'HK':
                currency = 'USD'  # 统一使用USD作为货币代码
                exchange_rate = ensure_exchange_rate_exists(currency, transaction_date.strftime('%Y-%m-%d'))
                if exchange_rate is None:
                    return jsonify({
                        'success': False,
                        'error': f'无法获取 {transaction_date.strftime("%Y-%m-%d")} 的{currency}汇率，请稍后重试'
                    })
            
            # 处理费用字段，确保空值转换为0
            def get_fee(field_name):
                value = request.form.get(field_name, '0')
                return float(value) if value.strip() else 0.0
            
            # 获取费用信息
            broker_fee = get_fee('broker_fee')
            transaction_levy = get_fee('transaction_levy')
            stamp_duty = get_fee('stamp_duty')
            trading_fee = get_fee('trading_fee')
            deposit_fee = get_fee('deposit_fee')
            
            # 获取成交明细
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            if not quantities or not prices:
                return jsonify({
                    'success': False,
                    'error': '请至少添加一条成交记录'
                })
            
            # 创建交易记录
            transaction = StockTransaction(
                user_id=session['user_id'],
                transaction_date=transaction_date,
                stock_code=stock_code,
                market=market,
                transaction_code=transaction_code,
                transaction_type=transaction_type,
                exchange_rate=exchange_rate,
                broker_fee=broker_fee,
                transaction_levy=transaction_levy,
                stamp_duty=stamp_duty,
                trading_fee=trading_fee,
                deposit_fee=deposit_fee
            )
            
            # 添加成交明细
            for quantity, price in zip(quantities, prices):
                if not quantity or not price:
                    continue
                detail = StockTransactionDetail(
                    quantity=int(quantity),
                    price=float(price)
                )
                transaction.details.append(detail)
            
            if not transaction.details:
                return jsonify({
                    'success': False,
                    'error': '请至少添加一条有效的成交记录'
                })
            
            db.session.add(transaction)
            db.session.commit()
            
            action = request.form.get('action')
            if action == 'save_and_add':
                return jsonify({
                    'success': True,
                    'message': '保存成功',
                    'redirect': url_for('stock.add')
                })
            else:
                return jsonify({
                    'success': True,
                    'message': '保存成功',
                    'redirect': url_for('stock.list')
                })
                
        except ValueError as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'输入数据格式错误: {str(e)}'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'保存失败: {str(e)}'
            })
    
    return render_template('stock/add.html')

@stock_bp.route('/stock/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    transaction = StockTransaction.query.get_or_404(id)
    if transaction.user_id != session['user_id']:
        flash('无权限编辑此记录')
        return redirect(url_for('stock.list'))
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            market = request.form['market']
            transaction_date = request.form['transaction_date']
            
            # 如果是非港股市场，获取汇率
            exchange_rate = None
            if market != 'HK':
                currency = 'USD'  # 统一使用USD作为货币代码
                exchange_rate = ensure_exchange_rate_exists(currency, transaction_date)
                if exchange_rate is None:
                    flash(f'无法获取 {transaction_date} 的{currency}汇率，请稍后重试')
                    return redirect(url_for('stock.edit', id=id))
            
            # 更新主记录
            transaction.transaction_code = request.form['transaction_code']
            transaction.stock_code = request.form['stock_code']
            transaction.market = market
            transaction.transaction_type = request.form['transaction_type']
            transaction.transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d')
            transaction.exchange_rate = exchange_rate
            transaction.broker_fee = float(request.form.get('broker_fee', 0))
            transaction.stamp_duty = float(request.form.get('stamp_duty', 0))
            transaction.transaction_levy = float(request.form.get('transaction_levy', 0))
            transaction.trading_fee = float(request.form.get('trading_fee', 0))
            transaction.clearing_fee = float(request.form.get('clearing_fee', 0))
            transaction.deposit_fee = float(request.form.get('deposit_fee', 0))
            
            # 删除旧的明细记录
            StockTransactionDetail.query.filter_by(transaction_id=transaction.id).delete()
            
            # 添加新的明细记录
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            for quantity, price in zip(quantities, prices):
                if quantity and price:  # 确保数量和价格都有值
                    detail = StockTransactionDetail(
                        transaction_id=transaction.id,
                        quantity=int(quantity),
                        price=float(price)
                    )
                    db.session.add(detail)
            
            db.session.commit()
            flash('交易记录更新成功')
            return redirect(url_for('stock.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}')
            return redirect(url_for('stock.edit', id=id))
    
    return render_template('stock/edit.html', transaction=transaction)

@stock_bp.route('/stock/delete/<int:id>')
@login_required
def delete(id):
    transaction = StockTransaction.query.get_or_404(id)
    if transaction.user_id != session['user_id']:
        flash('无权限删除此记录')
        return redirect(url_for('stock.list'))
    
    try:
        # 删除明细记录
        StockTransactionDetail.query.filter_by(transaction_id=transaction.id).delete()
        # 删除主记录
        db.session.delete(transaction)
        db.session.commit()
        flash('交易记录删除成功')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}')
    
    return redirect(url_for('stock.list'))

@stock_bp.route('/exchange_rates')
@login_required
def exchange_rate_list():
    """汇率列表页面"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 构建查询
    query = ExchangeRate.query
    
    # 添加日期范围过滤
    if start_date:
        query = query.filter(ExchangeRate.rate_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(ExchangeRate.rate_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    # 按日期降序排序并分页
    rates = query.order_by(ExchangeRate.rate_date.desc()).paginate(
        page=page, 
        per_page=per_page,
        error_out=False
    )
    
    return render_template('stock/exchange_rates.html', rates=rates, per_page=per_page)

@stock_bp.route('/exchange_rates/edit/<int:id>', methods=['POST'])
@login_required
def edit_exchange_rate(id):
    """修改汇率"""
    try:
        rate_id = request.form.get('rate_id')
        new_rate = float(request.form.get('rate'))
        
        # 获取汇率记录
        rate_record = ExchangeRate.query.get_or_404(id)
        old_rate = rate_record.rate
        
        # 更新汇率
        rate_record.rate = new_rate
        rate_record.source = 'MANUAL'  # 标记为手动修改
        
        # 更新使用此汇率的所有交易记录
        transactions = StockTransaction.query.filter(
            StockTransaction.transaction_date >= rate_record.rate_date,
            StockTransaction.transaction_date < rate_record.rate_date + timedelta(days=1),
            StockTransaction.market != 'HK'
        ).all()
        
        for transaction in transactions:
            if transaction.exchange_rate == old_rate:
                transaction.exchange_rate = new_rate
        
        db.session.commit()
        flash('汇率更新成功')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@stock_bp.route('/exchange_rates/add', methods=['POST'])
@login_required
def add_exchange_rate():
    """手动添加汇率"""
    try:
        date_str = request.form.get('date')
        currency = request.form.get('currency')
        rate = float(request.form.get('rate'))
        
        # 检查是否已存在
        rate_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing = ExchangeRate.query.filter_by(
            currency=currency,
            rate_date=rate_date
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': f'{date_str} 的 {currency} 汇率记录已存在'
            })
        
        # 创建新记录
        new_rate = ExchangeRate(
            currency=currency,
            rate_date=rate_date,
            rate=rate,
            source='MANUAL'  # 设置来源为手动添加
        )
        db.session.add(new_rate)
        db.session.commit()
        
        flash('汇率添加成功')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@stock_bp.route('/exchange_rates/fetch_missing', methods=['POST'])
@login_required
def fetch_missing_rates():
    """自动抓取缺失汇率"""
    try:
        # 更新所有临时汇率记录
        stats = update_temporary_rates()
        
        if stats['updated'] > 0:
            flash(f"成功更新 {stats['updated']} 条汇率记录")
        elif stats['failed'] > 0:
            flash(f"更新失败：{stats['failed']} 条记录更新失败", 'error')
        else:
            flash("没有需要更新的临时汇率记录")
            
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@stock_bp.route('/stock/stats')
@login_required
def stats():
    # 获取查询参数，但不设置默认值，允许为空
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stock_codes = request.args.getlist('stock_codes')
    
    # 只过滤用户ID
    query = StockTransaction.query.filter_by(user_id=session['user_id'])
    
    # 仅当有查询参数时才应用过滤条件
    if start_date:
        query = query.filter(StockTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(StockTransaction.transaction_date <= end_date)
    if stock_codes:
        query = query.filter(StockTransaction.stock_code.in_(stock_codes))
    
    # 按创建时间降序获取交易记录
    transactions = query.order_by(StockTransaction.created_at.desc()).all()
    
    # 获取所有股票代码供查询使用
    all_stock_codes = db.session.query(StockTransaction.stock_code)\
        .filter_by(user_id=session['user_id'])\
        .distinct()\
        .order_by(StockTransaction.stock_code)\
        .all()
    all_stock_codes = [code[0] for code in all_stock_codes]
    
    # 计算统计数据
    market_stats, stock_stats = calculate_stats(transactions)
    
    # 将股票分为持仓和已清仓两组
    holding_stocks = {}
    closed_stocks = {}
    
    for code, stock in stock_stats.items():
        if stock['current_quantity'] > 0:
            holding_stocks[code] = stock
        else:
            closed_stocks[code] = stock
    
    # 分别对持仓和已清仓股票按最新交易日期和系统时间排序
    def get_latest_transaction_info(transactions):
        if not transactions:
            return (datetime.min, datetime.min)
        latest = max(transactions, key=lambda x: (x['transaction_date'], x.get('created_at', datetime.min)))
        return (latest['transaction_date'], latest.get('created_at', datetime.min))
    
    sorted_holding_stocks = dict(sorted(
        holding_stocks.items(),
        key=lambda x: get_latest_transaction_info(x[1]['transactions']),
        reverse=True
    ))
    
    sorted_closed_stocks = dict(sorted(
        closed_stocks.items(),
        key=lambda x: get_latest_transaction_info(x[1]['transactions']),
        reverse=True
    ))
    
    # 合并排序后的结果
    sorted_stock_stats = {**sorted_holding_stocks, **sorted_closed_stocks}
    
    # 对每个股票的交易记录按日期和创建时间排序
    for code in sorted_stock_stats:
        sorted_stock_stats[code]['transactions'].sort(
            key=lambda x: (x['transaction_date'], x.get('created_at', datetime.min)),
            reverse=True
        )
    
    return render_template('stock/stats.html',
                         market_stats=market_stats,
                         stock_stats=sorted_stock_stats,
                         all_stock_codes=all_stock_codes,
                         selected_stock_codes=stock_codes)

@stock_bp.route('/stocks')
@login_required
def stocks():
    # 获取查询参数
    market = request.args.get('market', '')
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15  # 每页显示15条记录

    # 构建查询
    query = Stock.query
    if market:
        query = query.filter(Stock.market == market)
    if keyword:
        query = query.filter(or_(
            Stock.code.ilike(f'%{keyword}%'),
            Stock.name.ilike(f'%{keyword}%')
        ))

    # 应用分页
    pagination = query.order_by(Stock.market.asc(), Stock.code.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('stock/stocks.html', 
                         pagination=pagination,
                         market=market,
                         keyword=keyword)

@stock_bp.route('/stocks/add', methods=['POST'])
@login_required
def add_stock():
    """添加股票"""
    try:
        code = request.form.get('code')
        market = request.form.get('market')
        name = request.form.get('name')
        full_name = request.form.get('full_name')
        
        # 检查是否已存在
        existing = Stock.query.filter_by(code=code, market=market).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'{market} 市场的股票代码 {code} 已存在'
            })
        
        # 创建新记录
        stock = Stock(
            code=code,
            market=market,
            name=name,
            full_name=full_name
        )
        db.session.add(stock)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@stock_bp.route('/stocks/edit/<int:id>', methods=['POST'])
@login_required
def edit_stock(id):
    """编辑股票"""
    try:
        stock = Stock.query.get_or_404(id)
        
        # 更新信息
        stock.name = request.form.get('name')
        stock.full_name = request.form.get('full_name')
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@stock_bp.route('/stocks/delete/<int:id>', methods=['POST'])
@login_required
def delete_stock(id):
    """删除股票"""
    try:
        stock = Stock.query.get_or_404(id)
        
        # 检查是否有关联的交易记录
        has_transactions = StockTransaction.query.filter_by(
            stock_code=stock.code,
            market=stock.market
        ).first() is not None
        
        if has_transactions:
            return jsonify({
                'success': False,
                'error': '该股票存在交易记录，无法删除'
            })
        
        db.session.delete(stock)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@stock_bp.route('/api/stock/info')
@login_required
def get_stock_info():
    """获取股票信息"""
    market = request.args.get('market')
    code = request.args.get('code')
    
    if not market or not code:
        return jsonify({'success': False, 'error': '缺少必要参数'})
    
    try:
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

        # 处理股票代码格式
        if market == 'HK':
            # 如果是港股，统一处理前导零
            code = code.lstrip('0')  # 先去除所有前导零
            code = code.zfill(4)  # 然后补充到4位
            url = f'https://www.google.com/finance/quote/{code}:HKG'
            google_code = f"{code}:HKG"
        else:  # USA
            google_code = None
            # 先尝试NASDAQ
            url = f'https://www.google.com/finance/quote/{code}:NASDAQ'
            try:
                print(f"尝试NASDAQ: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                price_div = soup.find('div', {'data-last-price': True})
                
                if price_div and price_div.get('data-last-price'):
                    google_code = f"{code}:NASDAQ"
                else:
                    # 如果在NASDAQ找不到，尝试NYSE
                    url = f'https://www.google.com/finance/quote/{code}:NYSE'
                    print(f"尝试NYSE: {url}")
                    response = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    price_div = soup.find('div', {'data-last-price': True})
                    if price_div and price_div.get('data-last-price'):
                        google_code = f"{code}:NYSE"
                    else:
                        raise ValueError(f"股票 {code} 在NASDAQ和NYSE均未找到价格信息")
            except Exception as e:
                print(f"NASDAQ查询失败，尝试NYSE: {url}")
                url = f'https://www.google.com/finance/quote/{code}:NYSE'
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                price_div = soup.find('div', {'data-last-price': True})
                if price_div and price_div.get('data-last-price'):
                    google_code = f"{code}:NYSE"
                else:
                    raise ValueError(f"股票 {code} 在NYSE未找到价格信息")
        
        print(f"最终访问URL: {url}")
        
        # 获取股票名称 - 查找包含中文名称的元素
        name_div = soup.find('div', {'class': 'zzDege'})
        name = name_div.text.strip() if name_div else None
        
        if not name:
            # 如果无法从Google获取名称，尝试从yfinance获取
            yf_code = f"{code}.HK" if market == 'HK' else code
            stock = yf.Ticker(yf_code)
            info = stock.info
            name = info.get('longName', None)
        
        # 获取股票价格
        price = float(price_div.get('data-last-price')) if price_div and price_div.get('data-last-price') else None

        print(f"获取到股票信息: name={name}, price={price}, google_code={google_code}")

        # 保存或更新股票信息到数据库
        stock = Stock.query.filter_by(code=code, market=market).first()
        if stock:
            if name:
                stock.name = name
            if google_code:
                stock.full_name = google_code
            stock.updated_at = datetime.now()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'code': code,
                'market': market,
                'name': name,
                'google_code': google_code,
                'current_price': price
            }
        })
        
    except Exception as e:
        print(f"获取股票信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取股票信息失败，请检查输入的代码是否正确'
        })

@stock_bp.route('/api/stock/prices')
@login_required
def get_stock_prices():
    """获取所有股票的实时价格"""
    try:
        stocks = Stock.query.all()
        result = []
        
        for stock in stocks:
            try:
                # 使用 get_stock_price 函数获取价格（该函数已经实现了谷歌金融的抓取逻辑）
                quote = get_stock_price(stock.code, stock.market)
                
                if quote and quote.get('price') is not None:
                    result.append({
                        'code': stock.code,
                        'market': stock.market,
                        'current_price': quote['price']
                    })
                else:
                    print(f"无法获取 {stock.code} 的价格信息")
                    result.append({
                        'code': stock.code,
                        'market': stock.market,
                        'current_price': None
                    })
            except Exception as e:
                print(f"获取 {stock.code} 价格失败: {str(e)}")
                result.append({
                    'code': stock.code,
                    'market': stock.market,
                    'current_price': None
                })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        print(f"获取股票价格失败: {str(e)}")
        return jsonify({'success': False, 'error': '获取股票价格失败'})

@stock_bp.route('/api/stock/list')
@login_required
def get_stock_list():
    """获取股票列表，支持按市场和关键词搜索"""
    try:
        market = request.args.get('market', '')
        keyword = request.args.get('term', '')
        
        query = Stock.query
        
        if market:
            query = query.filter(Stock.market == market)
            
        if keyword:
            keyword = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Stock.code.like(keyword),
                    Stock.name.like(keyword)
                )
            )
            
        stocks = query.order_by(Stock.market.asc(), Stock.code.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'code': stock.code,
                'market': stock.market,
                'name': stock.name
            } for stock in stocks]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@stock_bp.route('/api/stock/search')
@login_required
def search_stocks():
    """搜索股票"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({
                'success': True,
                'data': []
            })
        
        # 添加通配符
        keyword = f"%{keyword}%"
        
        # 查询股票
        stocks = Stock.query.filter(
            or_(
                Stock.code.like(keyword),
                Stock.name.like(keyword)
            )
        ).all()
        
        # 格式化结果
        results = [{
            'code': stock.code,
            'market': stock.market,
            'name': stock.name
        } for stock in stocks]
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@stock_bp.route('/stock/check_transaction_code')
@login_required
def check_transaction_code():
    """检查交易编号是否已存在"""
    code = request.args.get('code')
    if not code:
        return jsonify({'exists': False})
    
    # 检查当前用户是否已有该交易编号的记录
    exists = StockTransaction.query.filter_by(
        user_id=session['user_id'],
        transaction_code=code
    ).first() is not None
    
    return jsonify({'exists': exists})

def process_transaction(stock, market_stats, trans, market):
    """处理单个交易记录
    
    Args:
        stock: 股票统计数据字典
        market_stats: 市场统计数据字典
        trans: 交易记录对象
        market: 市场代码（HK/USA）
    """
    try:
        # 更新基本统计数据
        stock['transaction_count'] += 1
        market_stats[market]['transaction_count'] += 1
        
        if market == 'USA':
            stock['total_fees_usd'] += trans.total_fees
            market_stats[market]['total_fees_usd'] += trans.total_fees
            stock['total_fees'] += trans.total_fees * trans.exchange_rate
            market_stats[market]['total_fees'] += trans.total_fees * trans.exchange_rate
        else:
            stock['total_fees'] += trans.total_fees
            market_stats[market]['total_fees'] += trans.total_fees
        
        if trans.transaction_type == 'BUY':
            # 买入交易处理
            stock['current_quantity'] += trans.total_quantity
            stock['total_buy_quantity'] += trans.total_quantity  # 更新总买入数量
            
            if market == 'USA':
                stock['total_buy_usd'] += trans.total_amount
                market_stats[market]['total_buy_usd'] += trans.total_amount
                stock['total_buy'] += trans.total_amount_hkd
                market_stats[market]['total_buy'] += trans.total_amount_hkd
                stock['avg_cost_usd'] = stock['total_buy_usd'] / stock['current_quantity'] if stock['current_quantity'] > 0 else 0
            else:
                stock['total_buy'] += trans.total_amount
                market_stats[market]['total_buy'] += trans.total_amount
            
            stock['avg_cost'] = stock['total_buy'] / stock['current_quantity'] if stock['current_quantity'] > 0 else 0
            
            # 添加到FIFO队列，包含买入费用
            stock['fifo_queue'].append({
                'quantity': trans.total_quantity,
                'price': trans.total_amount / trans.total_quantity,  # 原始币种单位成本
                'price_hkd': trans.total_amount_hkd / trans.total_quantity,  # 港币单位成本
                'date': trans.transaction_date,
                'exchange_rate': trans.exchange_rate,
                'fees': trans.total_fees,  # 记录买入费用
                'total_cost': trans.total_amount + trans.total_fees,  # 总成本（含费用）
                'total_cost_hkd': trans.total_amount_hkd + trans.total_fees  # 港币总成本（含费用）
            })
            
            # 记录买入交易详情
            trans_detail = {
                'transaction_date': trans.transaction_date,
                'transaction_type': trans.transaction_type,
                'transaction_code': trans.transaction_code,
                'total_quantity': trans.total_quantity,
                'total_amount': trans.total_amount,
                'total_amount_hkd': trans.total_amount_hkd,
                'average_price': trans.average_price,
                'total_fees': trans.total_fees,
                'exchange_rate': trans.exchange_rate
            }
            
            stock['transactions'].append(trans_detail)
            
        else:  # SELL
            # 卖出交易处理
            stock['current_quantity'] -= trans.total_quantity
            
            if market == 'USA':
                stock['total_sell_usd'] += trans.total_amount
                market_stats[market]['total_sell_usd'] += trans.total_amount
                stock['total_sell'] += trans.total_amount_hkd
                market_stats[market]['total_sell'] += trans.total_amount_hkd
            else:
                stock['total_sell'] += trans.total_amount
                market_stats[market]['total_sell'] += trans.total_amount
            
            # 计算FIFO成本和盈亏
            remaining_quantity = trans.total_quantity
            total_cost = 0  # 原始币种的总成本（含买入费用）
            total_cost_hkd = 0  # 港币总成本（含买入费用）
            fifo_cost_details = []  # FIFO成本明细
            
            while remaining_quantity > 0 and stock['fifo_queue']:
                buy_record = stock['fifo_queue'][0]
                used_quantity = min(remaining_quantity, buy_record['quantity'])
                
                # 计算这部分股票的成本（包含买入费用）
                cost_ratio = used_quantity / buy_record['quantity']
                unit_cost = buy_record['price']  # 原始币种单位成本
                unit_cost_hkd = buy_record['price_hkd']  # 港币单位成本
                buy_fees = buy_record['fees'] * cost_ratio  # 分摊的买入费用
                
                cost = unit_cost * used_quantity + buy_fees  # 原始币种成本（含买入费用）
                cost_hkd = unit_cost_hkd * used_quantity + buy_fees  # 港币成本（含买入费用）
                
                # 记录FIFO成本明细
                fifo_cost_details.append({
                    'date': buy_record['date'],
                    'quantity': used_quantity,
                    'price': unit_cost,
                    'price_hkd': unit_cost_hkd,
                    'cost': cost,
                    'cost_hkd': cost_hkd,
                    'exchange_rate': buy_record['exchange_rate'],
                    'fees': buy_fees  # 记录分摊的买入费用
                })
                
                total_cost += cost
                total_cost_hkd += cost_hkd
                
                # 更新或移除买入记录
                buy_record['quantity'] -= used_quantity
                if buy_record['quantity'] == 0:
                    stock['fifo_queue'].pop(0)
                remaining_quantity -= used_quantity
            
            # 计算利润（减去所有相关费用）
            if market == 'USA':
                # 美股：直接用美元计算
                net_income = trans.total_amount - trans.total_fees  # 卖出净收入
                profit_usd = net_income - total_cost  # 利润 = 净收入 - 总成本（已包含买入费用）
                profit_hkd = profit_usd * trans.exchange_rate
                profit_rate = profit_usd / total_cost if total_cost > 0 else 0
                
                stock['realized_profit_usd'] += profit_usd
                market_stats[market]['realized_profit_usd'] += profit_usd
                stock['realized_profit'] += profit_hkd
                market_stats[market]['realized_profit'] += profit_hkd
            else:
                # 港股：直接用港币计算
                net_income = trans.total_amount_hkd - trans.total_fees  # 卖出净收入
                profit = net_income - total_cost_hkd  # 利润 = 净收入 - 总成本（已包含买入费用）
                profit_rate = profit / total_cost_hkd if total_cost_hkd > 0 else 0
                
                stock['realized_profit'] += profit
                market_stats[market]['realized_profit'] += profit
            
            # 记录卖出交易详情
            trans_detail = {
                'transaction_date': trans.transaction_date,
                'transaction_type': trans.transaction_type,
                'transaction_code': trans.transaction_code,
                'total_quantity': trans.total_quantity,
                'total_amount': trans.total_amount,
                'total_amount_hkd': trans.total_amount_hkd,
                'average_price': trans.average_price,
                'total_fees': trans.total_fees,
                'exchange_rate': trans.exchange_rate,
                'fifo_price': total_cost / trans.total_quantity if trans.total_quantity > 0 else 0,
                'fifo_price_hkd': total_cost_hkd / trans.total_quantity if trans.total_quantity > 0 else 0,
                'profit': profit_usd if market == 'USA' else profit,
                'profit_rate': profit_rate,
                'fifo_cost_details': fifo_cost_details
            }
            
            stock['transactions'].append(trans_detail)
            
    except Exception as e:
        print(f"Error processing transaction: {str(e)}")
        raise 