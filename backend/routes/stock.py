from flask import Blueprint, request, session, jsonify, make_response
from routes.auth import login_required
from config.database import db
from datetime import datetime
from services.currency_checker import CurrencyChecker
from models import Stock, StockTransaction
from models.exchange import ExchangeRate
import logging
import json
from sqlalchemy import text
from services.transaction_calculator import TransactionCalculator
from services.transaction_service import TransactionService
from services.transaction_query import TransactionQuery

stock_bp = Blueprint('stock', __name__)
checker = CurrencyChecker()
logger = logging.getLogger(__name__)

@stock_bp.route('/transactions/')
@login_required
def get_transactions():
    """获取交易记录列表"""
    try:
        # 获取查询参数
        user_id = session.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        market = request.args.get('market')
        stock_codes = request.args.getlist('stock_codes[]')
        transaction_code = request.args.get('transaction_code')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # 构建过滤条件
        filters = {
            'start_date': start_date,
            'end_date': end_date,
            'market': market,
            'stock_codes': stock_codes,
            'transaction_code': transaction_code
        }
        
        # 使用TransactionQuery服务获取交易记录
        result = TransactionQuery.get_transactions(user_id, filters, page, per_page)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f'获取交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取交易记录失败: {str(e)}'
        }), 500

@stock_bp.route('/transactions', methods=['POST'])
@login_required
def add_transaction():
    """添加交易记录"""
    try:
        data = request.get_json()
        logger.info(f"接收到的交易数据: {data}")
        
        # 使用交易服务处理添加操作
        success, result, status_code = TransactionService.process_transaction(
            db, session['user_id'], data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'id': result.get('id'),
                    'changes': result.get('changes')
                }
            })
        else:
            return jsonify({'success': False, **result}), status_code
            
    except Exception as e:
        logger.error(f'添加交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['PUT'])
@login_required
def update_transaction(id):
    """更新交易记录"""
    try:
        data = request.get_json()
        logger.info(f"更新交易记录: ID={id}, 数据={data}")
        
        # 使用交易服务处理编辑操作
        success, result, status_code = TransactionService.process_transaction(
            db, session['user_id'], data, id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'changes': result.get('changes')
                }
            })
        else:
            return jsonify({'success': False, **result}), status_code
            
    except Exception as e:
        logger.error(f'更新交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    """删除交易记录"""
    try:
        # 获取原始交易记录
        transaction = TransactionQuery.get_transaction_by_id(id, session['user_id'])
        if not transaction:
            return jsonify({
                'success': False,
                'message': '交易记录不存在或无权限删除'
            }), 404
        
        # 使用交易服务处理删除操作
        success, result, status_code = TransactionService.process_transaction(
            db, session['user_id'], transaction, id, is_delete=True
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': result.get('message', '删除交易记录成功')
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', '删除交易记录失败')
            }), status_code
            
    except Exception as e:
        logger.error(f'删除交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除交易记录失败: {str(e)}'
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
        
        # 构建SQL查询 - 优化后直接使用数据库中存储的字段
        sql = """
            SELECT 
                t.id,
                t.market,
                t.stock_code,
                s.code_name as stock_name,
                LOWER(t.transaction_type) as transaction_type,
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
                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees_hkd,
                GROUP_CONCAT(
                    CONCAT(
                        COALESCE(td.quantity, ''),
                        '@',
                        COALESCE(td.price, ''),
                        '@',
                        COALESCE(td.quantity * td.price, '')
                    ) ORDER BY td.id ASC
                ) as detail_info,
                t.current_quantity,
                t.current_avg_cost,
                t.prev_avg_cost,
                t.realized_profit,
                t.profit_rate,
                t.running_quantity,
                t.running_cost
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            LEFT JOIN stock.stock_transaction_details td ON t.id = td.transaction_id
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
            
        # 添加分组
        sql += " GROUP BY t.id, t.market, t.stock_code, s.code_name, t.transaction_type, t.transaction_date, t.transaction_code"
        
        # 获取总记录数
        count_sql = f"SELECT COUNT(*) as count FROM stock.stock_transactions t WHERE t.user_id = %s"
        count_params = [session['user_id']]
        
        if start_date:
            count_sql += " AND t.transaction_date >= %s"
            count_params.append(start_date)
        if end_date:
            count_sql += " AND t.transaction_date <= %s"
            count_params.append(end_date)
        if market:
            count_sql += " AND t.market = %s"
            count_params.append(market)
        if stock_code:
            count_sql += " AND t.stock_code = %s"
            count_params.append(stock_code)
        if transaction_type:
            count_sql += " AND t.transaction_type = %s"
            count_params.append(transaction_type)
            
        total_result = db.fetch_one(count_sql, count_params)
        total = total_result['count'] if total_result else 0
        
        # 添加排序和分页
        sql += " ORDER BY t.transaction_date DESC, t.id DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        # 执行查询
        logs = db.fetch_all(sql, params)
        
        # 处理结果
        for log in logs:
            # 处理交易明细
            if log['detail_info']:
                details = []
                for detail_str in log['detail_info'].split(','):
                    parts = detail_str.split('@')
                    if len(parts) >= 3 and parts[0] and parts[1]:
                        details.append({
                            'quantity': float(parts[0]),
                            'price': float(parts[1]),
                            'amount': float(parts[2]) if parts[2] else float(parts[0]) * float(parts[1])
                        })
                log['details'] = details
            else:
                log['details'] = []
                
            # 删除不需要的字段
            del log['detail_info']
            
            # 确保数值字段为浮点数
            numeric_fields = [
                'total_amount', 'total_quantity', 'broker_fee', 'stamp_duty',
                'transaction_levy', 'trading_fee', 'deposit_fee', 'total_fees_hkd',
                'current_quantity', 'current_avg_cost', 'prev_avg_cost',
                'realized_profit', 'profit_rate', 'running_quantity', 'running_cost'
            ]
            
            for field in numeric_fields:
                if field in log and log[field] is not None:
                    log[field] = float(log[field])
                    
            # 计算卖出时的平均成本
            if log['transaction_type'] == 'sell' and log['prev_avg_cost']:
                log['sold_average_cost'] = log['prev_avg_cost']
            else:
                log['sold_average_cost'] = None
        
        return jsonify({
            'success': True,
            'data': {
                'items': logs,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"获取交易日志失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取交易日志失败: {str(e)}'
        }), 500

@stock_bp.route('/stocks')
@login_required
def get_stocks():
    """获取股票列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        market = request.args.get('market')
        search = request.args.get('search')
        
        # 构建SQL查询
        sql = """
            SELECT s.*, 
                   CASE 
                       WHEN s.code = %s THEN 1
                       WHEN s.code LIKE %s THEN 2
                       WHEN s.code_name LIKE %s THEN 3
                       ELSE 4
                   END as match_priority
            FROM stocks s
            WHERE 1=1
        """
        params = [search or '', f"{search}%" if search else "%", f"%{search}%" if search else "%"]
        
        if market:
            sql += " AND market = %s"
            params.append(market)
            
        if search:
            sql += " AND (code LIKE %s OR code_name LIKE %s)"
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern])
            
        # 计算总记录数
        count_sql = "SELECT COUNT(*) as count FROM stocks WHERE 1=1"
        count_params = []
        
        if market:
            count_sql += " AND market = %s"
            count_params.append(market)
            
        if search:
            count_sql += " AND (code LIKE %s OR code_name LIKE %s)"
            count_params.extend([search_pattern, search_pattern])
        
        total_result = db.fetch_one(count_sql, count_params)
        total = total_result['count'] if total_result else 0
        
        # 添加排序和分页
        sql += " ORDER BY match_priority, market, code LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        # 执行查询
        stocks = db.fetch_all(sql, params)
            
        return jsonify({
            'success': True,
            'data': {
                'items': [Stock(item).to_dict() for item in stocks],
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page
            }
        })
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取股票列表失败: {str(e)}'
        }), 500

@stock_bp.route('/stocks', methods=['POST'])
@login_required
def add_stock():
    """添加股票"""
    try:
        data = request.get_json()
        logger.info(f"接收到添加股票请求，数据：{data}")
        
        # 验证必填字段
        required_fields = ['code', 'market', 'code_name']
        for field in required_fields:
            if not data.get(field):
                logger.error(f"添加股票失败：缺少必填字段 {field}")
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400
        
        # 检查是否已存在相同代码的股票
        check_sql = "SELECT id FROM stock.stocks WHERE code = %s AND market = %s"
        existing = db.fetch_one(check_sql, [data['code'], data['market']])
        if existing:
            logger.error(f"添加股票失败：股票代码 {data['code']} 在市场 {data['market']} 已存在")
            return jsonify({
                'success': False,
                'message': f"股票代码 {data['code']} 在市场 {data['market']} 已存在"
            }), 400
        
        # 创建股票对象
        stock = Stock({
            'code': data['code'].strip(),
            'market': data['market'].strip(),
            'code_name': data['code_name'].strip(),
            'google_name': data.get('google_name', '').strip()
        })
        
        # 保存到数据库
        logger.info(f"开始保存股票：{stock.to_dict()}")
        if stock.save():
            logger.info("股票添加成功")
            return jsonify({
                'success': True,
                'message': '股票添加成功',
                'data': stock.to_dict()
            })
        else:
            logger.error("股票添加失败：数据库保存失败")
            return jsonify({
                'success': False,
                'message': '添加失败：数据库保存失败'
            }), 500
            
    except Exception as e:
        logger.error(f"添加股票失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/<int:id>', methods=['PUT'])
@login_required
def edit_stock(id):
    """编辑股票"""
    try:
        data = request.get_json()
        
        # 查找股票记录
        sql = "SELECT * FROM stocks WHERE id = %s"
        stock_data = db.fetch_one(sql, (id,))
        if not stock_data:
            return jsonify({
                'success': False,
                'message': '股票不存在'
            }), 404
            
        stock = Stock(stock_data)
        stock.code = data['code']
        stock.market = data['market']
        stock.code_name = data['code_name']
        stock.google_name = data.get('google_name')
        stock.industry = data.get('industry')
        stock.currency = data.get('currency')
        
        if stock.save():
            return jsonify({
                'success': True,
                'message': '股票更新成功',
                'data': stock.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新失败'
            }), 500
            
    except Exception as e:
        logger.error(f'更新股票失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/<int:id>', methods=['DELETE'])
@login_required
def delete_stock(id):
    """删除股票"""
    try:
        # 先检查股票是否存在
        sql = "SELECT * FROM stocks WHERE id = %s"
        stock = db.fetch_one(sql, (id,))
        if not stock:
            return jsonify({
                'success': False,
                'message': '股票不存在'
            }), 404
            
        # 删除股票
        sql = "DELETE FROM stocks WHERE id = %s"
        if db.execute(sql, (id,)):
            return jsonify({
                'success': True,
                'message': '股票删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除失败'
            }), 500
            
    except Exception as e:
        logger.error(f'删除股票失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(e)}'
        }), 500

@stock_bp.route('/stocks/update-prices', methods=['POST'])
@login_required
def update_stock_prices():
    """更新股票价格"""
    try:
        # 获取所有股票
        sql = "SELECT code, market FROM stocks"
        stocks = db.fetch_all(sql)
        
        updated_count = 0
        failed_count = 0
        
        for stock in stocks:
            try:
                market_code = 'HKG' if stock['market'] == 'HK' else stock['market']
                query = f"{stock['code']}:{market_code}"
                price_result = checker.get_exchange_rate(query)
                stock['current_price'] = float(price_result) if price_result is not None else 0
            except Exception as e:
                logger.error(f"获取股票 {query} 价格失败: {str(e)}")
                stock['current_price'] = 0
                
            try:
                # 更新股票价格
                update_sql = """
                    UPDATE stocks 
                    SET current_price = %s, 
                        price_updated_at = NOW() 
                    WHERE code = %s AND market = %s
                """
                if db.execute(update_sql, (stock['current_price'], stock['code'], stock['market'])):
                    updated_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"更新股票 {stock['code']} 价格失败: {str(e)}")
        
        return jsonify({
            'success': True,
            'data': {
                'updated': updated_count,
                'failed': failed_count
            }
        })
        
    except Exception as e:
        logger.error(f"更新股票价格失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新股票价格失败: {str(e)}'
        }), 500

@stock_bp.route('/check_price')
@login_required
def check_stock_price():
    """检查股票价格"""
    try:
        code = request.args.get('code')
        
        if not code:
            return jsonify({
                'success': False,
                'message': '请提供股票代码'
            }), 400

        # 如果是纯数字,先尝试港股市场
        if code.isdigit():
            # 如果是5位数,去除首位
            if len(code) == 5:
                code = code[1:]
            # 补齐到4位
            padded_code = code.zfill(4)
            query = f"{padded_code}:HKG"
            result = checker.get_exchange_rate(query)
            if result and result.get('price') is not None:
                return jsonify({
                    'success': True,
                    'data': {
                        'price': result['price'],
                        'name': result['name'],
                        'market': 'HK',
                        'google_code': query
                    }
                })

        # 尝试美股市场
        us_markets = ['NASDAQ', 'NYSE', 'NYSEAMERICAN']
        for market in us_markets:
            query = f"{code}:{market}"
            result = checker.get_exchange_rate(query)
            if result and result.get('price') is not None:
                return jsonify({
                    'success': True,
                    'data': {
                        'price': result['price'],
                        'name': result['name'],
                        'market': 'USA',
                        'google_code': query
                    }
                })

        return jsonify({
            'success': False,
            'message': '未找到股票信息'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '检查股票价格失败'
        }), 500

@stock_bp.route('/exchange_rates')
@login_required
def get_exchange_rates():
    """获取汇率列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 15))
        currency = request.args.get('currency')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建SQL查询
        sql = """
            SELECT * FROM exchange_rates 
            WHERE 1=1
        """
        params = []
        
        if currency:
            sql += " AND currency = %s"
            params.append(currency)
        if start_date:
            sql += " AND rate_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND rate_date <= %s"
            params.append(end_date)
            
        # 计算总记录数
        count_sql = sql.replace("*", "COUNT(*) as count")
        total = db.fetch_one(count_sql, params)
        total_count = total['count'] if total else 0
        
        # 添加排序和分页
        sql += " ORDER BY rate_date DESC, currency"
        sql += " LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        # 获取数据
        rates = db.fetch_all(sql, params)
        
        return jsonify({
            'success': True,
            'data': {
                'items': [ExchangeRate(rate).to_dict() for rate in rates],
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"获取汇率列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取汇率列表失败: {str(e)}'
        }), 500

@stock_bp.route('/exchange_rates/fetch_missing', methods=['POST'])
@login_required
def fetch_missing_rates():
    """获取缺失的汇率数据并更新临时汇率"""
    try:
        # 更新所有临时汇率记录
        updated_count = checker.update_temporary_rates()
        
        return jsonify({
            'success': True,
            'message': f'成功更新 {updated_count} 条临时汇率记录',
            'data': {
                'updated_count': updated_count
            }
        })
        
    except Exception as e:
        logger.error(f"获取缺失汇率失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取缺失汇率失败: {str(e)}'
        }), 500

@stock_bp.route('/exchange_rates', methods=['POST'])
@login_required
def add_exchange_rate():
    """添加汇率记录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['currency', 'rate', 'rate_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 检查是否已存在相同日期的汇率记录
        existing = ExchangeRate.find_by_date(data['currency'], data['rate_date'])
        if existing:
            return jsonify({
                'success': False,
                'message': '该日期的汇率记录已存在'
            }), 400
        
        # 创建新记录
        rate = ExchangeRate(data)
        if rate.save():
            # 添加成功后，检查并更新临时汇率记录
            checker.update_temporary_rates()
            
            return jsonify({
                'success': True,
                'message': '添加汇率记录成功',
                'data': rate.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '添加汇率记录失败'
            }), 500
        
    except Exception as e:
        logger.error(f"添加汇率记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加汇率记录失败: {str(e)}'
        }), 500

@stock_bp.route('/exchange_rates/<int:id>', methods=['PUT'])
@login_required
def update_exchange_rate(id):
    """更新汇率记录"""
    try:
        data = request.get_json()
        
        # 查找记录
        sql = "SELECT * FROM exchange_rates WHERE id = %s"
        rate_data = db.fetch_one(sql, (id,))
        if not rate_data:
            return jsonify({
                'success': False,
                'message': '汇率记录不存在'
            }), 404
        
        rate = ExchangeRate(rate_data)
        
        # 更新字段
        if 'rate' in data:
            rate.rate = data['rate']
        if 'source' in data:
            rate.source = data['source']
        
        if rate.save():
            return jsonify({
                'success': True,
                'message': '更新汇率记录成功',
                'data': rate.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新汇率记录失败'
            }), 500
        
    except Exception as e:
        logger.error(f"更新汇率记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新汇率记录失败: {str(e)}'
        }), 500

@stock_bp.route('/exchange_rates/<int:id>', methods=['DELETE'])
@login_required
def delete_exchange_rate(id):
    """删除汇率记录"""
    try:
        # 查找记录
        sql = "SELECT * FROM exchange_rates WHERE id = %s"
        rate = db.fetch_one(sql, (id,))
        if not rate:
            return jsonify({
                'success': False,
                'message': '汇率记录不存在'
            }), 404
        
        # 删除记录
        delete_sql = "DELETE FROM exchange_rates WHERE id = %s"
        if db.execute(delete_sql, (id,)):
            return jsonify({
                'success': True,
                'message': '删除汇率记录成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除汇率记录失败'
            }), 500
            
    except Exception as e:
        logger.error(f"删除汇率记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除汇率记录失败: {str(e)}'
        }), 500

@stock_bp.route('/transactions/<int:id>', methods=['GET'])
@login_required
def get_transaction(id):
    """获取单个交易记录"""
    try:
        # 使用TransactionQuery服务获取交易记录
        transaction = TransactionQuery.get_transaction_by_id(id, session['user_id'])
        
        if not transaction:
            return jsonify({
                'success': False,
                'message': '交易记录不存在或无权限查看'
            }), 404
            
        return jsonify({
            'success': True,
            'data': transaction
        })
        
    except Exception as e:
        logger.error(f'获取交易记录失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取交易记录失败: {str(e)}'
        }), 500

@stock_bp.route('/profit/')
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
        conditions = ['(t.user_id = %s OR h.user_id = %s)']
        params = [user_id, user_id]

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

        # 3. 获取交易数据
        sql = f"""
            WITH user_transactions AS (
                -- 用户直接创建的交易
                SELECT st.*, NULL as holder_id, NULL as holder_name, 
                       NULL as split_ratio, st.total_quantity as split_quantity,
                       st.total_amount as split_amount, st.total_fees as split_fees,
                       st.current_quantity as split_current_quantity,
                       st.current_cost as split_current_cost,
                       st.current_avg_cost as split_current_avg_cost,
                       st.realized_profit as split_realized_profit,
                       st.profit_rate as split_profit_rate
                FROM stock_transactions st
                WHERE st.user_id = %s
                
                UNION ALL
                
                -- 用户通过持有人关联的分单交易
                SELECT st.*, ts.holder_id, h.name as holder_name,
                       ts.split_ratio, ts.total_quantity as split_quantity,
                       ts.total_amount as split_amount, ts.total_fees as split_fees,
                       ts.current_quantity as split_current_quantity,
                       ts.current_cost as split_current_cost,
                       ts.current_avg_cost as split_current_avg_cost,
                       ts.realized_profit as split_realized_profit,
                       ts.profit_rate as split_profit_rate
                FROM stock_transactions st
                JOIN transaction_splits ts ON st.id = ts.original_transaction_id
                JOIN holders h ON ts.holder_id = h.id
                WHERE h.user_id = %s
            )
            SELECT ut.*, s.code_name as stock_name
            FROM user_transactions ut
            LEFT JOIN stocks s ON ut.stock_code = s.code AND ut.market = s.market
            WHERE 1=1
        """

        transactions = db.fetch_all(sql, params)

        # 4. 处理数据
        market_stats = {}  # 市场级别统计
        stock_stats = {}   # 股票级别统计
        
        # 5. 计算统计数据
        for trans in transactions:
            market = trans['market']
            stock_code = trans['stock_code']
            key = f"{market}-{stock_code}"
            
            # 初始化股票统计
            if key not in stock_stats:
                stock_stats[key] = {
                    'market': market,
                    'code': stock_code,
                    'name': trans['stock_name'],
                    'buy_count': 0,
                    'sell_count': 0,
                    'buy_quantity': 0,
                    'sell_quantity': 0,
                    'buy_amount': 0,
                    'sell_amount': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'current_price': 0,
                    'market_value': 0,
                    'unrealized_profit': 0,
                    'total_profit': 0,
                    'profit_rate': 0
                }

            # 初始化市场统计
            if market not in market_stats:
                market_stats[market] = {
                    'buy_count': 0,
                    'sell_count': 0,
                    'buy_amount': 0,
                    'sell_amount': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'market_value': 0,
                    'unrealized_profit': 0,
                    'total_profit': 0,
                    'profit_rate': 0
                }

            # 更新统计数据
            if trans['transaction_type'].lower() == 'buy':
                stock_stats[key]['buy_count'] += trans['transaction_count']
                stock_stats[key]['buy_quantity'] += trans['total_quantity']
                stock_stats[key]['buy_amount'] += trans['total_amount']
                market_stats[market]['buy_count'] += trans['transaction_count']
                market_stats[market]['buy_amount'] += trans['total_amount']
            else:  # SELL
                stock_stats[key]['sell_count'] += trans['transaction_count']
                stock_stats[key]['sell_quantity'] += trans['total_quantity']
                stock_stats[key]['sell_amount'] += trans['total_amount']
                market_stats[market]['sell_count'] += trans['transaction_count']
                market_stats[market]['sell_amount'] += trans['total_amount']

            stock_stats[key]['total_fees'] += trans['total_fees']
            market_stats[market]['total_fees'] += trans['total_fees']

        # 6. 计算持仓数量和盈亏数据
        holding_stocks = {}
        closed_stocks = {}

        for key, stock in stock_stats.items():
            # 计算持仓数量
            quantity = stock['buy_quantity'] - stock['sell_quantity']
            stock['quantity'] = quantity

            # 计算平均成本
            if quantity > 0:
                stock['average_cost'] = stock['buy_amount'] / stock['buy_quantity']
            else:
                stock['average_cost'] = 0

            # 获取当前股价
            try:
                market_code = 'HKG' if stock['market'] == 'HK' else stock['market']
                query = f"{stock['code']}:{market_code}"
                price_result = checker.get_exchange_rate(query)
                stock['current_price'] = float(price_result) if price_result is not None else 0
            except Exception as e:
                logger.error(f"获取股票 {query} 价格失败: {str(e)}")
                stock['current_price'] = 0

            # 计算已实现盈亏
            if stock['sell_quantity'] > 0:
                avg_cost = stock['buy_amount'] / stock['buy_quantity'] if stock['buy_quantity'] > 0 else 0
                stock['realized_profit'] = stock['sell_amount'] - (stock['sell_quantity'] * avg_cost) - stock['total_fees']
            else:
                stock['realized_profit'] = -stock['total_fees']

            # 计算未实现盈亏
            stock['market_value'] = quantity * stock['current_price']
            stock['unrealized_profit'] = stock['market_value'] - (quantity * stock['average_cost']) if quantity > 0 else 0

            # 计算总盈亏和收益率
            stock['total_profit'] = stock['realized_profit'] + stock['unrealized_profit']
            stock['profit_rate'] = (stock['total_profit'] / stock['buy_amount'] * 100) if stock['buy_amount'] > 0 else 0

            # 更新市场统计数据
            market = stock['market']
            market_stats[market]['realized_profit'] += stock['realized_profit']
            market_stats[market]['market_value'] += stock['market_value']
            market_stats[market]['unrealized_profit'] += stock['unrealized_profit']
            market_stats[market]['total_profit'] += stock['total_profit']

            # 分类到持仓或已清仓
            if quantity > 0:
                holding_stocks[key] = stock
            else:
                closed_stocks[key] = stock

        # 7. 计算市场收益率
        for market, stats in market_stats.items():
            stats['profit_rate'] = (stats['total_profit'] / stats['buy_amount'] * 100) if stats['buy_amount'] > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'market_stats': market_stats,
                'holding_stocks': holding_stocks,
                'closed_stocks': closed_stocks
            }
        })

    except Exception as e:
        logger.error(f"获取盈利统计数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取盈利统计数据失败'
        })

@stock_bp.route('/stocks/search')
@login_required
def search_stocks():
    """搜索股票"""
    try:
        query = request.args.get('query', '').strip()
        if not query:
            return jsonify({
                'success': True,
                'data': []
            })

        # 构建SQL查询
        sql = """
            SELECT code, code_name as name, market
            FROM stock.stocks
            WHERE code LIKE %s OR code_name LIKE %s
            ORDER BY 
                CASE 
                    WHEN code = %s THEN 1
                    WHEN code LIKE %s THEN 2
                    WHEN code_name LIKE %s THEN 3
                    ELSE 4
                END,
                market,
                code
            LIMIT 10
        """
        
        # 准备查询参数
        exact_match = query
        prefix_match = f"{query}%"
        contains_match = f"%{query}%"
        
        params = [
            contains_match,  # code LIKE
            contains_match,  # name LIKE
            exact_match,    # code =
            prefix_match,   # code LIKE (prefix)
            prefix_match    # name LIKE (prefix)
        ]
        
        # 执行查询
        results = db.fetch_all(sql, params)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"搜索股票失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索股票失败: {str(e)}'
        }), 500

@stock_bp.route('/transactions/check-code')
@login_required
def check_transaction_code():
    """检查交易编号是否已存在"""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({
                'success': False,
                'message': '请提供交易编号'
            }), 400
            
        # 使用TransactionQuery服务查询交易编号
        sql = "SELECT COUNT(*) as count FROM stock.stock_transactions WHERE transaction_code = %s AND user_id = %s"
        result = db.fetch_one(sql, [code, session['user_id']])
        
        exists = result and result['count'] > 0
        
        return jsonify({
            'success': True,
            'data': {
                'exists': exists
            }
        })
        
    except Exception as e:
        logger.error(f'检查交易编号失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'检查交易编号失败: {str(e)}'
        }), 500

@stock_bp.route('/search_stock')
@login_required
def search_stock():
    """搜索股票代码"""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({
                'success': False,
                'message': '请提供股票代码'
            }), 400

        # 添加时间戳和缓存控制
        response = make_response(jsonify({
            'success': True,
            'data': checker.search_stock(code)
        }))
        
        # 设置响应头以防止缓存
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response

    except Exception as e:
        logger.error(f"搜索股票失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索股票失败: {str(e)}'
        }), 500 