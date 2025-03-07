from datetime import datetime
import logging
from decimal import Decimal
from config.database import db

logger = logging.getLogger(__name__)

class TransactionQuery:
    """交易查询服务类，统一处理交易记录的查询操作"""
    
    @staticmethod
    def get_transaction_by_id(transaction_id, user_id=None):
        """
        根据ID获取单个交易记录
        
        Args:
            transaction_id: 交易ID
            user_id: 用户ID（可选，用于权限验证）
            
        Returns:
            dict: 交易记录
        """
        # 构建基础查询
        sql = """
            SELECT 
                t.*,
                s.code_name as stock_name,
                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                CASE 
                    WHEN LOWER(t.transaction_type) = 'buy' THEN 
                        t.total_amount + (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                    ELSE 
                        t.total_amount - (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                END as net_amount
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            WHERE t.id = %s
        """
        params = [transaction_id]
        
        # 如果提供了用户ID，则添加用户验证
        if user_id:
            sql += " AND t.user_id = %s"
            params.append(user_id)
            
        transaction = db.fetch_one(sql, params)
        
        if transaction:
            # 获取交易明细
            transaction['details'] = TransactionQuery.get_transaction_details(transaction_id)
            
            # 获取分单记录
            transaction['splits'] = TransactionQuery.get_transaction_splits(transaction_id)
            transaction['has_splits'] = len(transaction['splits']) > 0
            
            # 转换数值字段为浮点数
            TransactionQuery._convert_numeric_fields(transaction)
            
        return transaction
    
    @staticmethod
    def get_transactions(user_id, filters=None, page=1, per_page=15):
        """
        获取交易记录列表
        
        Args:
            user_id: 用户ID
            filters: 过滤条件字典
            page: 页码
            per_page: 每页记录数
            
        Returns:
            dict: 包含分页信息和交易记录的字典
        """
        # 构建基础查询
        sql = """
            SELECT DISTINCT
                t.*,
                s.code_name as stock_name,
                (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee) as total_fees,
                CASE 
                    WHEN LOWER(t.transaction_type) = 'buy' THEN 
                        t.total_amount + (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                    ELSE 
                        t.total_amount - (t.broker_fee + t.transaction_levy + t.stamp_duty + t.trading_fee + t.deposit_fee)
                END as net_amount
            FROM stock.stock_transactions t
            LEFT JOIN stock.stocks s ON t.stock_code = s.code AND t.market = s.market
            LEFT JOIN stock.transaction_splits ts ON t.id = ts.original_transaction_id
            LEFT JOIN stock.holders h ON ts.holder_id = h.id
            WHERE (t.user_id = %s OR h.user_id = %s)
        """
        params = [user_id, user_id]
        
        # 添加过滤条件
        if filters:
            if filters.get('start_date'):
                sql += " AND t.transaction_date >= %s"
                params.append(filters['start_date'])
                
            if filters.get('end_date'):
                sql += " AND t.transaction_date <= %s"
                params.append(filters['end_date'])
                
            if filters.get('market'):
                sql += " AND t.market = %s"
                params.append(filters['market'])
                
            if filters.get('stock_codes') and isinstance(filters['stock_codes'], list) and filters['stock_codes']:
                placeholders = ','.join(['%s'] * len(filters['stock_codes']))
                sql += f" AND t.stock_code IN ({placeholders})"
                params.extend(filters['stock_codes'])
                
            if filters.get('transaction_code'):
                sql += " AND t.transaction_code LIKE %s"
                params.append(f"%{filters['transaction_code']}%")
                
            if filters.get('transaction_type'):
                sql += " AND LOWER(t.transaction_type) = %s"
                params.append(filters['transaction_type'].lower())
        
        # 计算总记录数
        count_sql = "SELECT COUNT(*) as total FROM stock.stock_transactions t WHERE t.user_id = %s"
        
        # 添加与主查询相同的过滤条件
        if filters:
            if filters.get('start_date'):
                count_sql += " AND t.transaction_date >= %s"
            
            if filters.get('end_date'):
                count_sql += " AND t.transaction_date <= %s"
            
            if filters.get('market'):
                count_sql += " AND t.market = %s"
            
            if filters.get('stock_codes') and isinstance(filters['stock_codes'], list) and filters['stock_codes']:
                placeholders = ','.join(['%s'] * len(filters['stock_codes']))
                count_sql += f" AND t.stock_code IN ({placeholders})"
            
            if filters.get('transaction_code'):
                count_sql += " AND t.transaction_code LIKE %s"
            
            if filters.get('transaction_type'):
                count_sql += " AND LOWER(t.transaction_type) = %s"
        
        total_result = db.fetch_one(count_sql, params)
        total_count = total_result['total'] if total_result else 0
        
        # 添加排序和分页
        sql += " ORDER BY t.transaction_date DESC, t.id DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        # 获取交易记录
        transactions = db.fetch_all(sql, params)
        
        # 获取交易明细
        if transactions:
            transaction_ids = [t['id'] for t in transactions]
            details_map = TransactionQuery.get_transaction_details_batch(transaction_ids)
            
            # 获取分单记录
            splits_map = TransactionQuery.get_transaction_splits_batch(transaction_ids)
            
            # 将明细和分单记录添加到交易记录
            for transaction in transactions:
                transaction_id = transaction['id']
                transaction['details'] = details_map.get(transaction_id, [])
                transaction['splits'] = splits_map.get(transaction_id, [])
                transaction['has_splits'] = len(transaction['splits']) > 0
                
                # 转换数值字段为浮点数
                TransactionQuery._convert_numeric_fields(transaction)
        
        return {
            'items': transactions,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'pages': (total_count + per_page - 1) // per_page
        }
    
    @staticmethod
    def get_transaction_details(transaction_id):
        """
        获取单个交易的明细
        
        Args:
            transaction_id: 交易ID
            
        Returns:
            list: 交易明细列表
        """
        sql = """
            SELECT quantity, price
            FROM stock.stock_transaction_details
            WHERE transaction_id = %s
            ORDER BY id ASC
        """
        details = db.fetch_all(sql, [transaction_id])
        
        # 转换为前端需要的格式
        return [
            {
                'quantity': float(detail['quantity']),
                'price': float(detail['price']),
                'amount': float(detail['quantity']) * float(detail['price'])
            }
            for detail in details
        ]
    
    @staticmethod
    def get_transaction_details_batch(transaction_ids):
        """
        批量获取多个交易的明细
        
        Args:
            transaction_ids: 交易ID列表
            
        Returns:
            dict: 以交易ID为键的明细字典
        """
        if not transaction_ids:
            return {}
            
        placeholders = ','.join(['%s'] * len(transaction_ids))
        sql = f"""
            SELECT transaction_id, quantity, price
            FROM stock.stock_transaction_details
            WHERE transaction_id IN ({placeholders})
            ORDER BY id ASC
        """
        
        details = db.fetch_all(sql, transaction_ids)
        
        # 按交易ID分组
        result = {}
        for detail in details:
            transaction_id = detail['transaction_id']
            if transaction_id not in result:
                result[transaction_id] = []
            result[transaction_id].append({
                'quantity': float(detail['quantity']),
                'price': float(detail['price']),
                'amount': float(detail['quantity']) * float(detail['price'])
            })
        
        return result
    
    @staticmethod
    def get_transaction_splits_batch(transaction_ids):
        """
        批量获取交易的分单记录
        
        Args:
            transaction_ids: 交易ID列表
            
        Returns:
            dict: 以交易ID为键，分单记录列表为值的字典
        """
        if not transaction_ids:
            return {}
            
        placeholders = ','.join(['%s'] * len(transaction_ids))
        sql = f"""
            SELECT 
                ts.*,
                (ts.broker_fee + ts.transaction_levy + ts.stamp_duty + ts.trading_fee + ts.deposit_fee) as total_fees
            FROM stock.transaction_splits ts
            WHERE ts.original_transaction_id IN ({placeholders})
            ORDER BY ts.id ASC
        """
        
        splits = db.fetch_all(sql, transaction_ids)
        
        # 按交易ID分组
        result = {}
        for split in splits:
            transaction_id = split['original_transaction_id']
            if transaction_id not in result:
                result[transaction_id] = []
                
            # 转换数值字段为浮点数
            for key, value in split.items():
                if isinstance(value, Decimal):
                    split[key] = float(value)
                    
            result[transaction_id].append(split)
            
        return result
    
    @staticmethod
    def get_transaction_splits(transaction_id):
        """
        获取单个交易的分单记录
        
        Args:
            transaction_id: 交易ID
            
        Returns:
            list: 分单记录列表
        """
        sql = """
            SELECT 
                ts.*,
                (ts.broker_fee + ts.transaction_levy + ts.stamp_duty + ts.trading_fee + ts.deposit_fee) as total_fees
            FROM stock.transaction_splits ts
            WHERE ts.original_transaction_id = %s
            ORDER BY ts.id ASC
        """
        splits = db.fetch_all(sql, [transaction_id])
        
        # 转换数值字段为浮点数
        for split in splits:
            for key, value in split.items():
                if isinstance(value, Decimal):
                    split[key] = float(value)
        
        return splits
    
    @staticmethod
    def _convert_numeric_fields(transaction):
        """
        转换交易记录中的数值字段为浮点数
        
        Args:
            transaction: 交易记录字典
        """
        numeric_fields = [
            'total_quantity', 'total_amount', 'broker_fee', 'transaction_levy',
            'stamp_duty', 'trading_fee', 'deposit_fee', 'total_fees', 'net_amount',
            'prev_quantity', 'prev_cost', 'prev_avg_cost',
            'current_quantity', 'current_cost', 'current_avg_cost',
            'realized_profit', 'profit_rate', 'running_quantity', 'running_cost'
        ]
        
        for field in numeric_fields:
            if field in transaction and transaction[field] is not None:
                transaction[field] = float(transaction[field]) 