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
    """计算交易统计数据"""
    market_stats = defaultdict(lambda: {
        'transaction_count': 0,  # 笔数
        'total_buy': 0,         # 买入总额（不含费用）
        'total_sell': 0,        # 卖出总额
        'total_fees': 0,        # 费用
        'realized_profit': 0,   # 已实现盈亏
        'market_value': 0,      # 持仓价值
        'total_profit': 0,      # 总盈亏（已实现盈亏+持仓价值）
        'profit_rate': 0        # 总盈亏比例
    })
    
    stock_stats = defaultdict(lambda: {
        'market': '',                # 市场
        'stock_name': '',           # 股票名称
        'current_quantity': 0,      # 数量
        'transaction_count': 0,     # 笔数
        'total_buy': 0,            # 买入总额（不含费用）
        'total_buy_with_fees': 0,  # 买入总额（含费用）
        'total_buy_quantity': 0,    # 买入总数量
        'avg_cost': 0,             # 加权平均价格（含费用）
        'total_sell': 0,           # 卖出总额
        'total_fees': 0,           # 费用
        'realized_profit': 0,       # 已实现盈亏
        'current_price': 0,         # 现价
        'market_value': 0,          # 持仓价值
        'total_profit': 0,          # 总盈亏
        'profit_rate': 0,          # 总盈亏比例
        'transactions': [],         # 交易记录
        'fifo_queue': []           # FIFO队列，用于计算每笔交易的FIFO均价
    })
    
    # 获取所有相关股票的名称
    stock_codes = set(t.stock_code for t in transactions)
    stocks = Stock.query.filter(Stock.code.in_(stock_codes)).all()
    stock_names = {s.code: s.name for s in stocks}
    
    # 按日期排序交易记录
    sorted_transactions = sorted(transactions, key=lambda x: x.transaction_date)
    
    # 计算每支股票的统计数据
    for trans in sorted_transactions:
        market = trans.market
        code = trans.stock_code
        
        # 更新市场统计
        market_stats[market]['transaction_count'] += 1
        market_stats[market]['total_fees'] += trans.total_fees
        
        # 更新股票统计
        stock = stock_stats[code]
        stock['market'] = market
        stock['stock_name'] = stock_names.get(code, '')
        stock['transaction_count'] += 1
        stock['total_fees'] += trans.total_fees
        
        # 计算FIFO均价
        fifo_price = 0
        if trans.transaction_type == 'BUY':
            # 买入时，计算当前这笔交易的均价（含费用）
            fifo_price = (trans.total_amount + trans.total_fees) / trans.total_quantity
            # 添加到FIFO队列
            stock['fifo_queue'].append({
                'quantity': trans.total_quantity,
                'price': fifo_price
            })
        else:  # SELL
            # 卖出时，从FIFO队列中计算卖出部分的均价
            remaining_sell_quantity = trans.total_quantity
            total_cost = 0
            sell_records = []
            
            for buy_record in stock['fifo_queue'][:]:
                if remaining_sell_quantity <= 0:
                    break
                    
                if buy_record['quantity'] <= remaining_sell_quantity:
                    # 完全卖出这笔买入
                    sell_quantity = buy_record['quantity']
                    total_cost += sell_quantity * buy_record['price']
                    remaining_sell_quantity -= sell_quantity
                    stock['fifo_queue'].remove(buy_record)
                    sell_records.append({
                        'quantity': sell_quantity,
                        'price': buy_record['price']
                    })
                else:
                    # 部分卖出
                    sell_quantity = remaining_sell_quantity
                    total_cost += sell_quantity * buy_record['price']
                    buy_record['quantity'] -= sell_quantity
                    remaining_sell_quantity = 0
                    sell_records.append({
                        'quantity': sell_quantity,
                        'price': buy_record['price']
                    })
            
            if sell_records:
                # 计算FIFO均价
                fifo_price = total_cost / trans.total_quantity
        
        # 计算交易明细
        trans_detail = {
            'transaction_date': trans.transaction_date,
            'transaction_type': trans.transaction_type,
            'transaction_code': trans.transaction_code,
            'total_quantity': trans.total_quantity,
            'total_amount': trans.total_amount,
            'total_fees': trans.total_fees,
            'exchange_rate': trans.exchange_rate,
            'average_price': trans.average_price,
            'fifo_price': fifo_price,
            'net_amount': trans.net_amount,
            'net_amount_hkd': trans.net_amount_hkd,
            'details': [],
            'profit': trans.net_amount_hkd if trans.transaction_type == 'SELL' else None,
            'profit_rate': ((trans.average_price / fifo_price - 1) * 100) if trans.transaction_type == 'SELL' and fifo_price > 0 else None
        }
        
        # 更新股票统计数据
        if trans.transaction_type == 'BUY':
            stock['total_buy'] += trans.total_amount
            stock['total_buy_with_fees'] += (trans.total_amount + trans.total_fees)
            stock['total_buy_quantity'] += trans.total_quantity
            stock['current_quantity'] += trans.total_quantity
            market_stats[market]['total_buy'] += trans.total_amount
        else:  # SELL
            stock['total_sell'] += trans.total_amount
            stock['current_quantity'] -= trans.total_quantity
            market_stats[market]['total_sell'] += trans.total_amount
            
            # 计算已实现盈亏
            realized_profit = trans.net_amount_hkd
            stock['realized_profit'] += realized_profit
            market_stats[market]['realized_profit'] += realized_profit
        
        # 计算加权平均价格（含费用）- 用于汇总显示
        if stock['total_buy_quantity'] > 0:
            stock['avg_cost'] = stock['total_buy_with_fees'] / stock['total_buy_quantity']
        
        stock['transactions'].append(trans_detail)
    
    # 获取当前价格并计算持仓市值
    stock_list = [(s['market'], code) for code, s in stock_stats.items() if s['current_quantity'] > 0]
    current_prices = get_multiple_quotes(stock_list)
    
    # 获取当前汇率
    today = datetime.now().strftime('%Y-%m-%d')
    usd_rate = get_exchange_rate('USD', today)
    if not usd_rate:
        print(f"警告：无法获取 {today} 的美元汇率，将跳过美股市值计算")
    
    for code, stock in stock_stats.items():
        if stock['current_quantity'] > 0 and code in current_prices:
            quote = current_prices[code]
            if not quote:
                print(f"警告：无法获取 {code} 的当前价格")
                continue
                
            stock['current_price'] = quote['price']
            
            # 计算持仓市值（转换为港币）
            if quote['market'] == 'HK':
                market_value = quote['price'] * stock['current_quantity']
            else:  # USA
                if not usd_rate:
                    print(f"警告：由于缺少汇率，跳过 {code} 的市值计算")
                    continue
                market_value = quote['price'] * stock['current_quantity'] * usd_rate
            
            stock['market_value'] = market_value
            market_stats[stock['market']]['market_value'] += market_value
            
            # 计算未实现盈亏
            unrealized_profit = market_value - (stock['avg_cost'] * stock['current_quantity'])
            stock['total_profit'] = stock['realized_profit'] + unrealized_profit
            
            # 计算总盈亏率
            total_investment = stock['total_buy_with_fees']
            if total_investment > 0:
                stock['profit_rate'] = stock['total_profit'] / total_investment * 100
    
    # 计算市场维度的总盈亏和盈亏率
    for market in market_stats:
        stats = market_stats[market]
        stats['total_profit'] = stats['realized_profit'] + stats['market_value'] - stats['total_buy']
        if stats['total_buy'] > 0:
            stats['profit_rate'] = stats['total_profit'] / stats['total_buy'] * 100
    
    return dict(market_stats), dict(stock_stats)

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
            else:
                # 尝试不同的交易所
                exchanges = ['NASDAQ', 'NYSE']
                for exchange in exchanges:
                    try:
                        test_url = f'https://www.google.com/finance/quote/{code}:{exchange}'
                        print(f"尝试访问URL: {test_url}")
                        response = requests.get(test_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            price_div = soup.find('div', {'data-last-price': True})
                            if price_div and price_div.get('data-last-price'):
                                url = test_url
                                break
                    except:
                        continue
                
                if not url:
                    # 如果都失败了，默认使用NASDAQ
                    url = f'https://www.google.com/finance/quote/{code}:NASDAQ'
        
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
    
    transactions = query.order_by(StockTransaction.transaction_date.desc()).all()
    
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
    if request.method == 'GET':
        return render_template('stock/add.html')
    
    try:
        # 获取表单数据
        market = request.form['market']
        transaction_date = request.form['transaction_date']
        transaction_code = request.form['transaction_code']
        stock_code = request.form['stock_code']
        
        # 检查交易编号是否已存在
        existing_transaction = StockTransaction.query.filter_by(
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
            exchange_rate = ensure_exchange_rate_exists(currency, transaction_date)
            if exchange_rate is None:
                return jsonify({
                    'success': False,
                    'error': f'无法获取 {transaction_date} 的{currency}汇率，请稍后重试'
                })
        
        # 开始事务
        try:
            # 创建交易主记录
            transaction = StockTransaction(
                user_id=session['user_id'],
                transaction_code=transaction_code,
                stock_code=stock_code,
                market=market,
                transaction_type=request.form['transaction_type'],
                transaction_date=datetime.strptime(transaction_date, '%Y-%m-%d'),
                exchange_rate=exchange_rate,
                broker_fee=float(request.form.get('broker_fee', 0)),
                stamp_duty=float(request.form.get('stamp_duty', 0)),
                transaction_levy=float(request.form.get('transaction_levy', 0)),
                trading_fee=float(request.form.get('trading_fee', 0)),
                clearing_fee=float(request.form.get('clearing_fee', 0)),
                deposit_fee=float(request.form.get('deposit_fee', 0))
            )
            db.session.add(transaction)
            db.session.flush()  # 获取transaction.id
            
            # 处理成交明细
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            if not quantities or not prices:
                raise ValueError('请至少添加一条成交明细')
            
            for quantity, price in zip(quantities, prices):
                if quantity and price:  # 确保数量和价格都有值
                    detail = StockTransactionDetail(
                        transaction_id=transaction.id,
                        quantity=int(quantity),
                        price=float(price)
                    )
                    db.session.add(detail)
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '交易记录添加成功',
                'redirect': url_for('stock.list') if request.form.get('action') == 'save' else url_for('stock.add')
            })
            
        except ValueError as ve:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(ve)
            })
            
        except Exception as e:
            db.session.rollback()
            raise  # 重新抛出异常，让外层捕获
            
    except Exception as e:
        # 记录详细错误信息
        print(f'添加交易记录时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'添加交易记录失败: {str(e)}'
        })

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
    
    transactions = query.order_by(StockTransaction.transaction_date.desc()).all()
    
    # 获取所有股票代码供查询使用
    all_stock_codes = db.session.query(StockTransaction.stock_code)\
        .filter_by(user_id=session['user_id'])\
        .distinct()\
        .order_by(StockTransaction.stock_code)\
        .all()
    all_stock_codes = [code[0] for code in all_stock_codes]
    
    # 计算统计数据
    market_stats, stock_stats = calculate_stats(transactions)
    
    return render_template('stock/stats.html',
                         market_stats=market_stats,
                         stock_stats=stock_stats,
                         all_stock_codes=all_stock_codes,
                         selected_stock_codes=stock_codes)

@stock_bp.route('/stocks')
@login_required
def stock_list():
    """股票列表页面"""
    # 获取查询参数
    market = request.args.get('market', '')
    keyword = request.args.get('keyword', '')
    
    # 构建查询
    query = Stock.query
    
    # 添加市场过滤
    if market:
        query = query.filter(Stock.market == market)
    
    # 添加关键字搜索
    if keyword:
        query = query.filter(db.or_(
            Stock.code.ilike(f'%{keyword}%'),
            Stock.name.ilike(f'%{keyword}%'),
            Stock.full_name.ilike(f'%{keyword}%')
        ))
    
    # 按市场和代码排序
    stocks = query.order_by(Stock.market, Stock.code).all()
    
    return render_template('stock/stocks.html', stocks=stocks)

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
        # 处理股票代码格式
        if market == 'HK':
            # 如果是港股，统一处理前导零
            code = code.lstrip('0')  # 先去除所有前导零
            code = code.zfill(4)  # 然后补充到4位
        
        # 构建Google Finance URL
        if market == 'HK':
            url = f'https://www.google.com/finance/quote/{code}:HKG'
        else:  # USA
            url = f'https://www.google.com/finance/quote/{code}:NASDAQ'
        
        print(f"尝试访问URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
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
        price_div = soup.find('div', {'data-last-price': True})
        price = float(price_div['data-last-price']) if price_div and price_div.get('data-last-price') else None
        
        if not name or not price:
            print(f"未找到股票信息: name={name}, price={price}")
            return jsonify({
                'success': False,
                'error': '无法获取股票信息，请检查股票代码是否正确'
            })
        
        print(f"成功获取股票信息: {name}, 价格: {price}")
        return jsonify({
            'success': True,
            'data': {
                'name': name,
                'google_code': f"{code}:HKG" if market == 'HK' else f"{code}:NASDAQ",
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
            
        stocks = query.all()
        return jsonify({
            'success': True,
            'results': [{
                'id': stock.code,
                'text': stock.code,
                'name': stock.name,
                'market': stock.market
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
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({
            'success': True,
            'data': []
        })
    
    # 从数据库中搜索匹配的股票
    # 优先精确匹配股票代码
    exact_match = Stock.query.filter(Stock.code == keyword).first()
    if exact_match:
        return jsonify({
            'success': True,
            'data': [{
                'code': exact_match.code,
                'name': exact_match.name,
                'market': exact_match.market
            }]
        })
    
    # 如果没有精确匹配，则进行模糊搜索
    stocks = Stock.query.filter(
        or_(
            Stock.code.ilike(f'%{keyword}%'),
            Stock.name.ilike(f'%{keyword}%')
        )
    ).all()
    
    results = [{
        'code': stock.code,
        'name': stock.name,
        'market': stock.market
    } for stock in stocks]
    
    return jsonify({
        'success': True,
        'data': results
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