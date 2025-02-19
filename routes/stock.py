from flask import Blueprint, request, session, jsonify
from flask_login import login_required
from models import db, Stock, StockTransaction, TransactionDetail, ExchangeRate
from datetime import datetime
from services.exchange_rate import ExchangeRateService
import logging

stock_bp = Blueprint('stock', __name__)
logger = logging.getLogger(__name__)

# 交易记录相关API
@stock_bp.route('/transactions')
@login_required
def get_transactions():
    """获取交易记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    market = request.args.get('market')
    stock_codes = request.args.getlist('stock_codes')
    
    query = StockTransaction.query.filter_by(user_id=session['user_id'])
    
    if start_date:
        query = query.filter(StockTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(StockTransaction.transaction_date <= end_date)
    if market:
        query = query.filter_by(market=market)
    if stock_codes:
        query = query.filter(StockTransaction.stock_code.in_(stock_codes))
        
    pagination = query.order_by(StockTransaction.transaction_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }
    })

@stock_bp.route('/transactions/add', methods=['POST'])
@login_required
def add_transaction():
    """添加交易记录"""
    try:
        data = request.get_json()
        
        # 创建交易记录
        transaction = StockTransaction(
            user_id=session['user_id'],
            stock_code=data['stock_code'],
            market=data['market'],
            transaction_date=datetime.strptime(data['transaction_date'], '%Y-%m-%d'),
            transaction_type=data['transaction_type'],
            transaction_code=data['transaction_code'],
            broker_fee=data.get('broker_fee', 0),
            transaction_levy=data.get('transaction_levy', 0),
            stamp_duty=data.get('stamp_duty', 0),
            trading_fee=data.get('trading_fee', 0),
            deposit_fee=data.get('deposit_fee', 0)
        )
        
        # 添加交易明细
        for detail in data['details']:
            transaction_detail = TransactionDetail(
                quantity=detail['quantity'],
                price=detail['price']
            )
            transaction.details.append(transaction_detail)
        
        # 如果是非港股，获取汇率
        if transaction.market != 'HK':
            exchange_rate = ExchangeRateService().get_exchange_rate(
                'USD' if transaction.market == 'USA' else transaction.market,
                transaction.transaction_date.strftime('%Y-%m-%d')
            )
            transaction.exchange_rate = exchange_rate
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '交易记录添加成功',
            'data': transaction.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'添加交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'添加失败：{str(e)}'
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['PUT'])
@login_required
def edit_transaction(id):
    """编辑交易记录"""
    transaction = StockTransaction.query.get_or_404(id)
    
    # 检查权限
    if transaction.user_id != session['user_id']:
        return jsonify({
            'success': False,
            'message': '无权限编辑此记录'
        }), 403
    
    try:
        data = request.get_json()
        
        # 更新交易记录
        transaction.stock_code = data['stock_code']
        transaction.market = data['market']
        transaction.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d')
        transaction.transaction_type = data['transaction_type']
        transaction.transaction_code = data['transaction_code']
        transaction.broker_fee = data.get('broker_fee', 0)
        transaction.transaction_levy = data.get('transaction_levy', 0)
        transaction.stamp_duty = data.get('stamp_duty', 0)
        transaction.trading_fee = data.get('trading_fee', 0)
        transaction.deposit_fee = data.get('deposit_fee', 0)
        
        # 更新交易明细
        transaction.details.clear()
        for detail in data['details']:
            transaction_detail = TransactionDetail(
                quantity=detail['quantity'],
                price=detail['price']
            )
            transaction.details.append(transaction_detail)
        
        # 如果是非港股，更新汇率
        if transaction.market != 'HK':
            exchange_rate = ExchangeRateService().get_exchange_rate(
                'USD' if transaction.market == 'USA' else transaction.market,
                transaction.transaction_date.strftime('%Y-%m-%d')
            )
            transaction.exchange_rate = exchange_rate
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '交易记录更新成功',
            'data': transaction.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败：{str(e)}'
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    """删除交易记录"""
    transaction = StockTransaction.query.get_or_404(id)
    
    # 检查权限
    if transaction.user_id != session['user_id']:
        return jsonify({
            'success': False,
            'message': '无权限删除此记录'
        }), 403
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '交易记录删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(e)}'
        }), 500

# 汇率相关API
@stock_bp.route('/exchange_rates')
@login_required
def get_exchange_rates():
    """获取汇率列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    currency = request.args.get('currency')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = ExchangeRate.query
    
    if currency:
        query = query.filter_by(currency=currency)
    if start_date:
        query = query.filter(ExchangeRate.rate_date >= start_date)
    if end_date:
        query = query.filter(ExchangeRate.rate_date <= end_date)
        
    pagination = query.order_by(ExchangeRate.rate_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }
    })

@stock_bp.route('/exchange_rates/add', methods=['POST'])
@login_required
def add_exchange_rate():
    """添加汇率记录"""
    try:
        data = request.get_json()
        
        exchange_rate = ExchangeRate(
            currency=data['currency'],
            rate_date=datetime.strptime(data['rate_date'], '%Y-%m-%d').date(),
            rate=data['rate'],
            source='MANUAL'
        )
        
        db.session.add(exchange_rate)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '汇率添加成功',
            'data': exchange_rate.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'添加汇率失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'添加失败：{str(e)}'
        }), 500

@stock_bp.route('/exchange_rates/fetch_missing', methods=['POST'])
@login_required
def fetch_missing_rates():
    """获取缺失的汇率"""
    try:
        service = ExchangeRateService()
        stats = service.update_missing_rates()
        
        return jsonify({
            'success': True,
            'message': f"成功更新 {stats['updated']} 条汇率记录",
            'data': stats
        })
        
    except Exception as e:
        logger.error(f'获取缺失汇率失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败：{str(e)}'
        }), 500

# 股票相关API
@stock_bp.route('/stocks')
@login_required
def get_stocks():
    """获取股票列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    market = request.args.get('market')
    search = request.args.get('search')
    
    query = Stock.query
    
    if market:
        query = query.filter_by(market=market)
    if search:
        query = query.filter(
            (Stock.code.like(f'%{search}%')) |
            (Stock.name.like(f'%{search}%'))
        )
        
    pagination = query.order_by(Stock.market, Stock.code).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }
    })

@stock_bp.route('/stocks', methods=['POST'])
@login_required
def add_stock():
    """添加股票"""
    try:
        data = request.get_json()
        
        stock = Stock(
            code=data['code'],
            market=data['market'],
            name=data['name'],
            full_name=data.get('full_name'),
            industry=data.get('industry'),
            currency=data.get('currency')
        )
        
        db.session.add(stock)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '股票添加成功',
            'data': stock.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'添加股票失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'添加失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/<int:id>', methods=['PUT'])
@login_required
def edit_stock(id):
    """编辑股票"""
    stock = Stock.query.get_or_404(id)
    
    try:
        data = request.get_json()
        
        stock.code = data['code']
        stock.market = data['market']
        stock.name = data['name']
        stock.full_name = data.get('full_name')
        stock.industry = data.get('industry')
        stock.currency = data.get('currency')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '股票更新成功',
            'data': stock.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新股票失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/<int:id>', methods=['DELETE'])
@login_required
def delete_stock(id):
    """删除股票"""
    stock = Stock.query.get_or_404(id)
    
    try:
        db.session.delete(stock)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '股票删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除股票失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(e)}'
        }), 500 