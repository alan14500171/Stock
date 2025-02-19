from flask import Blueprint, request, session, jsonify
from routes.auth import login_required
from config.database import db
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
    
    # 构建SQL查询
    sql = """
        SELECT * FROM stock_transactions 
        WHERE user_id = %s
    """
    params = [session['user_id']]
    
    if start_date:
        sql += " AND transaction_date >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND transaction_date <= %s"
        params.append(end_date)
    if market:
        sql += " AND market = %s"
        params.append(market)
    if stock_codes:
        placeholders = ','.join(['%s'] * len(stock_codes))
        sql += f" AND stock_code IN ({placeholders})"
        params.extend(stock_codes)
        
    # 添加排序和分页
    sql += " ORDER BY transaction_date DESC LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])
    
    # 获取总记录数
    count_sql = """
        SELECT COUNT(*) as total FROM stock_transactions 
        WHERE user_id = %s
    """
    count_params = [session['user_id']]
    
    if start_date:
        count_sql += " AND transaction_date >= %s"
        count_params.append(start_date)
    if end_date:
        count_sql += " AND transaction_date <= %s"
        count_params.append(end_date)
    if market:
        count_sql += " AND market = %s"
        count_params.append(market)
    if stock_codes:
        placeholders = ','.join(['%s'] * len(stock_codes))
        count_sql += f" AND stock_code IN ({placeholders})"
        count_params.extend(stock_codes)
    
    # 执行查询
    transactions = db.fetch_all(sql, params)
    total_result = db.fetch_one(count_sql, count_params)
    total = total_result['total'] if total_result else 0
    
    return jsonify({
        'success': True,
        'data': {
            'items': transactions,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page
        }
    })

@stock_bp.route('/transactions', methods=['POST'])
@login_required
def add_transaction():
    """添加交易记录"""
    try:
        data = request.get_json()
        required_fields = ['stock_code', 'stock_name', 'transaction_date', 'transaction_type', 
                         'quantity', 'price', 'market', 'currency']
        
        # 验证必填字段
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
        
        # 插入交易记录
        sql = """
            INSERT INTO stock_transactions 
            (user_id, stock_code, stock_name, transaction_date, transaction_type, 
             quantity, price, market, currency, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = [
            session['user_id'],
            data['stock_code'],
            data['stock_name'],
            data['transaction_date'],
            data['transaction_type'],
            data['quantity'],
            data['price'],
            data['market'],
            data['currency']
        ]
        
        transaction_id = db.insert(sql, params)
        
        if not transaction_id:
            return jsonify({'success': False, 'message': '添加交易记录失败'}), 500
            
        # 如果交易货币不是美元，获取汇率并更新
        if data['currency'] != 'USD':
            exchange_rate_service = ExchangeRateService()
            rate = exchange_rate_service.get_exchange_rate(data['currency'], data['transaction_date'])
            
            if rate:
                update_sql = """
                    UPDATE stock_transactions 
                    SET exchange_rate = %s, 
                        usd_price = price * %s,
                        updated_at = NOW()
                    WHERE id = %s
                """
                db.execute(update_sql, [rate, rate, transaction_id])
        
        return jsonify({
            'success': True,
            'message': '交易记录添加成功',
            'data': {'id': transaction_id}
        })
        
    except Exception as e:
        logger.error(f"添加交易记录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'添加交易记录失败: {str(e)}'}), 500

@stock_bp.route('/transactions/<int:id>', methods=['PUT'])
@login_required
def update_transaction(id):
    """更新交易记录"""
    try:
        data = request.get_json()
        
        # 检查记录是否存在且属于当前用户
        check_sql = "SELECT id FROM stock_transactions WHERE id = %s AND user_id = %s"
        transaction = db.fetch_one(check_sql, [id, session['user_id']])
        
        if not transaction:
            return jsonify({'success': False, 'message': '交易记录不存在或无权限修改'}), 404
        
        # 构建更新SQL
        update_fields = []
        params = []
        
        field_mapping = {
            'stock_code': 'stock_code',
            'stock_name': 'stock_name',
            'transaction_date': 'transaction_date',
            'transaction_type': 'transaction_type',
            'quantity': 'quantity',
            'price': 'price',
            'market': 'market',
            'currency': 'currency'
        }
        
        for key, field in field_mapping.items():
            if key in data:
                update_fields.append(f"{field} = %s")
                params.append(data[key])
        
        if not update_fields:
            return jsonify({'success': False, 'message': '没有需要更新的字段'}), 400
            
        update_fields.append("updated_at = NOW()")
        params.append(id)  # WHERE id = %s 的参数
        
        sql = f"""
            UPDATE stock_transactions 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        
        db.execute(sql, params)
        
        # 如果更新了货币或价格，重新计算美元价格
        if 'currency' in data or 'price' in data:
            # 获取最新的记录信息
            transaction_sql = """
                SELECT currency, price, transaction_date 
                FROM stock_transactions 
                WHERE id = %s
            """
            transaction = db.fetch_one(transaction_sql, [id])
            
            if transaction and transaction['currency'] != 'USD':
                exchange_rate_service = ExchangeRateService()
                rate = exchange_rate_service.get_exchange_rate(
                    transaction['currency'], 
                    transaction['transaction_date']
                )
                
                if rate:
                    update_sql = """
                        UPDATE stock_transactions 
                        SET exchange_rate = %s,
                            usd_price = price * %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    db.execute(update_sql, [rate, rate, id])
        
        return jsonify({
            'success': True,
            'message': '交易记录更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新交易记录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新交易记录失败: {str(e)}'}), 500

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

@stock_bp.route('/transactions/logs', methods=['GET'])
@login_required
def get_transaction_logs():
    """获取交易日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')
        stock_code = request.args.get('stock_code')
        transaction_type = request.args.get('transaction_type')
        
        # 构建SQL查询
        sql = """
            SELECT 
                t.*,
                DATE_FORMAT(t.transaction_date, '%Y-%m-%d') as formatted_date,
                CASE 
                    WHEN t.transaction_type = 'buy' THEN t.quantity * t.price
                    ELSE -t.quantity * t.price
                END as transaction_amount,
                CASE 
                    WHEN t.transaction_type = 'buy' THEN t.quantity * COALESCE(t.usd_price, t.price)
                    ELSE -t.quantity * COALESCE(t.usd_price, t.price)
                END as transaction_amount_usd
            FROM stock_transactions t
            WHERE t.user_id = %s
        """
        params = [session['user_id']]
        
        if start_date:
            sql += " AND t.transaction_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND t.transaction_date <= %s"
            params.append(end_date)
        if market:
            sql += " AND t.market = %s"
            params.append(market)
        if stock_code:
            sql += " AND t.stock_code = %s"
            params.append(stock_code)
        if transaction_type:
            sql += " AND t.transaction_type = %s"
            params.append(transaction_type)
            
        # 获取总记录数
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as temp"
        total_result = db.fetch_one(count_sql, params)
        total = total_result['total'] if total_result else 0
        
        # 添加排序和分页
        sql += " ORDER BY t.transaction_date DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        # 执行查询
        logs = db.fetch_all(sql, params)
        
        # 获取当前页面涉及的股票的累计持仓情况
        if logs:
            stock_codes = list(set(log['stock_code'] for log in logs))
            placeholders = ','.join(['%s'] * len(stock_codes))
            
            position_sql = f"""
                SELECT 
                    stock_code,
                    SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) as total_quantity,
                    SUM(CASE WHEN transaction_type = 'buy' THEN quantity * price ELSE -quantity * price END) as total_amount
                FROM stock_transactions
                WHERE user_id = %s AND stock_code IN ({placeholders})
                GROUP BY stock_code
            """
            position_params = [session['user_id']] + stock_codes
            positions = db.fetch_all(position_sql, position_params)
            position_map = {p['stock_code']: p for p in positions}
            
            # 添加累计持仓信息到日志中
            for log in logs:
                position = position_map.get(log['stock_code'], {})
                log['cumulative_quantity'] = position.get('total_quantity', 0)
                log['cumulative_amount'] = position.get('total_amount', 0)
        
        return jsonify({
            'success': True,
            'data': {
                'items': logs,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page
            }
        })
        
    except Exception as e:
        logger.error(f"获取交易日志失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取交易日志失败: {str(e)}'}), 500

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

@stock_bp.route('/market-summary', methods=['GET'])
@login_required
def get_market_summary():
    """获取市场汇总信息"""
    try:
        # 获取各市场的持仓总值（按原始货币）
        market_sql = """
            SELECT 
                market,
                currency,
                COUNT(DISTINCT stock_code) as stock_count,
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) as total_quantity,
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity * price ELSE -quantity * price END) as total_amount
            FROM stock_transactions 
            WHERE user_id = %s
            GROUP BY market, currency
            HAVING total_quantity > 0
        """
        market_summary = db.fetch_all(market_sql, [session['user_id']])
        
        # 获取美元总值
        usd_sql = """
            SELECT 
                market,
                SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) * 
                    COALESCE(usd_price, price) as usd_value
            FROM stock_transactions 
            WHERE user_id = %s
            GROUP BY market
            HAVING SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) > 0
        """
        usd_values = db.fetch_all(usd_sql, [session['user_id']])
        usd_map = {item['market']: item['usd_value'] for item in usd_values}
        
        # 计算总的美元市值
        total_usd_value = sum(usd_map.values())
        
        # 添加美元价值和占比信息
        for summary in market_summary:
            market = summary['market']
            summary['usd_value'] = usd_map.get(market, 0)
            summary['percentage'] = (summary['usd_value'] / total_usd_value * 100) if total_usd_value > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'market_summary': market_summary,
                'total_usd_value': total_usd_value
            }
        })
        
    except Exception as e:
        logger.error(f"获取市场汇总信息失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取市场汇总信息失败: {str(e)}'}), 500 