from datetime import datetime
from .base import BaseModel, db

class StockTransaction(BaseModel):
    """股票交易记录模型"""
    __tablename__ = 'stock_transactions'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    stock_code = db.Column(db.String(20), nullable=False, index=True)
    market = db.Column(db.String(10), nullable=False, index=True)
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    transaction_type = db.Column(db.String(10), nullable=False)  # BUY or SELL
    transaction_code = db.Column(db.String(50), unique=True, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)
    broker_fee = db.Column(db.Float, default=0)
    transaction_levy = db.Column(db.Float, default=0)
    stamp_duty = db.Column(db.Float, default=0)
    trading_fee = db.Column(db.Float, default=0)
    deposit_fee = db.Column(db.Float, default=0)
    exchange_rate = db.Column(db.Float, default=1.0)
    
    # 关联
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    details = db.relationship('TransactionDetail', backref='transaction', lazy=True, 
                            cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StockTransaction {self.transaction_code}>'
        
    @property
    def total_fees(self):
        """计算总费用"""
        return self.broker_fee + self.transaction_levy + self.stamp_duty + \
               self.trading_fee + self.deposit_fee
               
    @property
    def net_amount(self):
        """计算净金额"""
        if self.transaction_type == 'BUY':
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
            'transaction_date': self.transaction_date.isoformat(),
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
            'details': [detail.to_dict() for detail in self.details],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    @classmethod
    def find_by_code(cls, transaction_code):
        """根据交易编号查找交易记录"""
        return cls.query.filter_by(transaction_code=transaction_code).first()
        
    @classmethod
    def get_user_transactions(cls, user_id, market=None, stock_code=None, 
                            start_date=None, end_date=None):
        """获取用户的交易记录"""
        query = cls.query.filter_by(user_id=user_id)
        
        if market:
            query = query.filter_by(market=market)
        if stock_code:
            query = query.filter_by(stock_code=stock_code)
        if start_date:
            query = query.filter(cls.transaction_date >= start_date)
        if end_date:
            query = query.filter(cls.transaction_date <= end_date)
            
        return query.order_by(cls.transaction_date.desc()).all()

class TransactionDetail(db.Model):
    """交易明细模型"""
    __tablename__ = 'stock_transaction_details'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('stock_transactions.id'), 
                             nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TransactionDetail {self.quantity}@{self.price}>'
        
    @property
    def amount(self):
        """计算总金额"""
        return self.quantity * self.price
        
    def to_dict(self):
        return {
            'id': self.id,
            'quantity': self.quantity,
            'price': self.price,
            'amount': self.amount,
            'created_at': self.created_at.isoformat()
        } 