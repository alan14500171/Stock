from datetime import datetime
from config.database import db

class StockTransaction:
    """股票交易记录模型"""
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.user_id = data.get('user_id')
        self.stock_code = data.get('stock_code')
        self.market = data.get('market')
        self.transaction_date = data.get('transaction_date')
        self.transaction_type = data.get('transaction_type', '').lower() if data else None
        self.transaction_code = data.get('transaction_code')
        self.total_amount = data.get('total_amount')
        self.total_quantity = data.get('total_quantity')
        self.broker_fee = data.get('broker_fee', 0)
        self.transaction_levy = data.get('transaction_levy', 0)
        self.stamp_duty = data.get('stamp_duty', 0)
        self.trading_fee = data.get('trading_fee', 0)
        self.deposit_fee = data.get('deposit_fee', 0)
        self.exchange_rate = data.get('exchange_rate', 1.0)
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        self.updated_at = data.get('updated_at') if data else datetime.utcnow()

    @property
    def total_fees(self):
        """计算总费用"""
        return (self.broker_fee or 0) + (self.transaction_levy or 0) + \
               (self.stamp_duty or 0) + (self.trading_fee or 0) + \
               (self.deposit_fee or 0)
               
    @property
    def net_amount(self):
        """计算净金额"""
        if self.transaction_type.lower() == 'buy':
            return self.total_amount + self.total_fees
        else:
            return self.total_amount - self.total_fees

    @property
    def total_amount_hkd(self):
        """计算港币金额"""
        if self.market == 'HK':
            return self.total_amount
        return self.total_amount * (self.exchange_rate or 1.0)

    @property
    def net_amount_hkd(self):
        """计算港币净金额"""
        if self.market == 'HK':
            return self.net_amount
        return self.net_amount * (self.exchange_rate or 1.0)

    @property
    def average_price(self):
        """计算平均价格"""
        if self.total_quantity and self.total_quantity > 0:
            return self.total_amount / self.total_quantity
        return 0
            
    def to_dict(self):
        return {
            'id': self.id,
            'stock_code': self.stock_code,
            'market': self.market,
            'transaction_date': self.transaction_date.isoformat() if isinstance(self.transaction_date, datetime) else self.transaction_date,
            'transaction_type': self.transaction_type,
            'transaction_code': self.transaction_code,
            'total_amount': self.total_amount,
            'total_quantity': self.total_quantity,
            'broker_fee': self.broker_fee,
            'transaction_levy': self.transaction_levy,
            'stamp_duty': self.stamp_duty,
            'trading_fee': self.trading_fee,
            'deposit_fee': self.deposit_fee,
            'exchange_rate': self.exchange_rate,
            'total_fees': self.total_fees,
            'net_amount': self.net_amount,
            'total_amount_hkd': self.total_amount_hkd,
            'net_amount_hkd': self.net_amount_hkd,
            'average_price': self.average_price,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        
    def save(self):
        """保存交易记录"""
        if self.id:
            # 更新
            sql = """
                UPDATE stock.stock_transactions 
                SET user_id=%s, stock_code=%s, market=%s, transaction_date=%s,
                    transaction_type=LOWER(%s), transaction_code=%s, total_amount=%s,
                    total_quantity=%s, broker_fee=%s, transaction_levy=%s,
                    stamp_duty=%s, trading_fee=%s, deposit_fee=%s,
                    exchange_rate=%s, updated_at=%s
                WHERE id=%s
            """
            params = (
                self.user_id, self.stock_code, self.market, self.transaction_date,
                self.transaction_type, self.transaction_code, self.total_amount,
                self.total_quantity, self.broker_fee, self.transaction_levy,
                self.stamp_duty, self.trading_fee, self.deposit_fee,
                self.exchange_rate, datetime.utcnow(), self.id
            )
            return db.execute(sql, params)
        else:
            # 新增
            sql = """
                INSERT INTO stock.stock_transactions 
                (user_id, stock_code, market, transaction_date, transaction_type,
                 transaction_code, total_amount, total_quantity, broker_fee,
                 transaction_levy, stamp_duty, trading_fee, deposit_fee,
                 exchange_rate, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                self.user_id, self.stock_code, self.market, self.transaction_date,
                self.transaction_type, self.transaction_code, self.total_amount,
                self.total_quantity, self.broker_fee, self.transaction_levy,
                self.stamp_duty, self.trading_fee, self.deposit_fee,
                self.exchange_rate, self.created_at, self.updated_at
            )
            self.id = db.insert(sql, params)
            return bool(self.id)
            
    @staticmethod
    def get_by_id(transaction_id):
        """根据ID获取交易记录"""
        sql = "SELECT * FROM stock.stock_transactions WHERE id=%s"
        data = db.fetch_one(sql, (transaction_id,))
        return StockTransaction(data) if data else None
        
    @staticmethod
    def get_by_code(transaction_code):
        """根据交易编号获取交易记录"""
        sql = "SELECT * FROM stock.stock_transactions WHERE transaction_code=%s"
        data = db.fetch_one(sql, (transaction_code,))
        return StockTransaction(data) if data else None
        
    @staticmethod
    def get_user_transactions(user_id, market=None, stock_code=None, 
                            start_date=None, end_date=None, page=1, per_page=15):
        """获取用户的交易记录"""
        sql = "SELECT * FROM stock.stock_transactions WHERE user_id=%s"
        params = [user_id]
        
        if market:
            sql += " AND market=%s"
            params.append(market)
        if stock_code:
            sql += " AND stock_code=%s"
            params.append(stock_code)
        if start_date:
            sql += " AND transaction_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND transaction_date <= %s"
            params.append(end_date)
            
        # 计算总记录数
        count_sql = sql.replace("*", "COUNT(*)")
        total = db.fetch_one(count_sql, params)
        total_count = total['COUNT(*)'] if total else 0
        
        # 添加排序和分页
        sql += " ORDER BY transaction_date DESC, id DESC"
        sql += " LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        # 获取数据
        data = db.fetch_all(sql, params)
        transactions = [StockTransaction(item) for item in data]
        
        return {
            'items': transactions,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'pages': (total_count + per_page - 1) // per_page
        }

class TransactionDetail:
    """交易明细模型"""
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.transaction_id = data.get('transaction_id')
        self.quantity = data.get('quantity')
        self.price = data.get('price')
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        
    @property
    def amount(self):
        """计算总金额"""
        return self.quantity * self.price if self.quantity and self.price else 0
        
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'quantity': self.quantity,
            'price': self.price,
            'amount': self.amount,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
        
    def save(self):
        """保存交易明细"""
        if self.id:
            # 更新
            sql = """
                UPDATE stock.stock_transaction_details 
                SET transaction_id=%s, quantity=%s, price=%s
                WHERE id=%s
            """
            params = (self.transaction_id, self.quantity, self.price, self.id)
            return db.execute(sql, params)
        else:
            # 新增
            sql = """
                INSERT INTO stock.stock_transaction_details 
                (transaction_id, quantity, price, created_at)
                VALUES (%s, %s, %s, %s)
            """
            params = (self.transaction_id, self.quantity, self.price, self.created_at)
            self.id = db.insert(sql, params)
            return bool(self.id)
            
    @staticmethod
    def get_by_transaction_id(transaction_id):
        """获取交易的所有明细"""
        sql = "SELECT * FROM stock.stock_transaction_details WHERE transaction_id=%s ORDER BY id"
        data = db.fetch_all(sql, (transaction_id,))
        return [TransactionDetail(item) for item in data] 