import os
import sys

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from flask import Flask
from models import db, StockTransaction
from config import Config
from utils.exchange_rate import get_exchange_rate
from datetime import datetime
from collections import defaultdict
import yfinance as yf

def get_stock_symbol(code, market):
    """转换股票代码为 Yahoo Finance 格式"""
    if market == 'HK':
        return f"{code}.HK"
    else:  # USA
        return code

def get_stock_price(code, market):
    """获取单个股票的实时价格"""
    try:
        symbol = get_stock_symbol(code, market)
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if 'regularMarketPrice' not in info or info['regularMarketPrice'] is None:
            return None
            
        return {
            'code': code,
            'market': market,
            'currency': 'HKD' if market == 'HK' else 'USD',
            'price': info['regularMarketPrice'],
            'timestamp': datetime.now()
        }
    except Exception as e:
        print(f"获取 {code} 价格失败: {str(e)}")
        return None

def get_multiple_quotes(stock_list):
    """批量获取多个股票的实时价格"""
    result = {}
    for market, code in stock_list:
        quote = get_stock_price(code, market)
        if quote:
            result[code] = quote
    return result

def calculate_stats(transactions):
    """计算交易统计数据"""
    stock_stats = defaultdict(lambda: {
        'market': '',
        'current_quantity': 0,
        'total_buy_cost': 0,
        'total_buy_quantity': 0,
        'avg_buy_price': 0
    })
    
    for trans in transactions:
        market = trans.market
        code = trans.stock_code
        
        stock_stats[code]['market'] = market
        
        if trans.transaction_type == 'BUY':
            stock_stats[code]['current_quantity'] += trans.total_quantity
            stock_stats[code]['total_buy_cost'] += trans.total_amount_hkd
            stock_stats[code]['total_buy_quantity'] += trans.total_quantity
        else:  # SELL
            stock_stats[code]['current_quantity'] -= trans.total_quantity
        
        # 计算平均买入价格
        if stock_stats[code]['total_buy_quantity'] > 0:
            stock_stats[code]['avg_buy_price'] = (
                stock_stats[code]['total_buy_cost'] / 
                stock_stats[code]['total_buy_quantity']
            )
    
    return dict(stock_stats)

def get_holding_stocks():
    """获取持仓股票"""
    transactions = StockTransaction.query.all()
    stats = calculate_stats(transactions)
    
    holdings = []
    for code, stock in stats.items():
        if stock['current_quantity'] > 0:
            holdings.append({
                'code': code,
                'market': stock['market'],
                'quantity': stock['current_quantity'],
                'avg_price': stock['avg_buy_price']
            })
    
    return holdings

def check_portfolio():
    """检查持仓市值"""
    try:
        # 创建Flask应用
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            # 获取持仓股票
            holdings = get_holding_stocks()
            if not holdings:
                print('当前没有持仓')
                return
            
            # 获取当前汇率
            today = datetime.now().strftime('%Y-%m-%d')
            usd_rate = get_exchange_rate('USD', today)
            
            # 获取实时报价
            stocks = [(h['market'], h['code']) for h in holdings]
            quotes = get_multiple_quotes(stocks)
            
            # 计算市值
            total_value_hkd = 0
            print('\n当前持仓市值:')
            print('=' * 80)
            print(f"{'代码':<10} {'市场':<6} {'持仓数量':<10} {'均价':<12} {'现价':<12} {'市值(HKD)':<15} {'盈亏':<12} {'盈亏率':<8}")
            print('-' * 80)
            
            for holding in holdings:
                quote = quotes.get(holding['code'])
                if not quote:
                    print(f"{holding['code']:<10} {holding['market']:<6} {holding['quantity']:<10} "
                          f"{holding['avg_price']:<12.3f} {'获取失败':<12} {'N/A':<15} {'N/A':<12} {'N/A':<8}")
                    continue
                
                # 计算市值（转换为港币）
                if quote['market'] == 'HK':
                    market_value_hkd = quote['price'] * holding['quantity']
                else:  # USA
                    market_value_hkd = quote['price'] * holding['quantity'] * usd_rate
                
                # 计算盈亏
                profit_loss = (quote['price'] - holding['avg_price']) * holding['quantity']
                if quote['market'] != 'HK':
                    profit_loss *= usd_rate
                    
                profit_loss_rate = ((quote['price'] / holding['avg_price']) - 1) * 100
                
                print(f"{holding['code']:<10} {holding['market']:<6} {holding['quantity']:<10} "
                      f"{holding['avg_price']:<12.3f} {quote['price']:<12.3f} "
                      f"{market_value_hkd:<15.2f} {profit_loss:<12.2f} {profit_loss_rate:<8.2f}%")
                
                total_value_hkd += market_value_hkd
            
            print('=' * 80)
            print(f"总市值: {total_value_hkd:,.2f} HKD")
            print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        print(f'查询失败: {str(e)}')

if __name__ == '__main__':
    print("正在查询持仓市值...")
    check_portfolio() 