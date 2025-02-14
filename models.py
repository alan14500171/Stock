from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class StockTransaction(db.Model):
    """交易主表，包含费用信息"""
    __tablename__ = 'stock_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_code = db.Column(db.String(20), nullable=False)  # 交易编号，如 P-847256
    stock_code = db.Column(db.String(20), nullable=False)  # 股票代码
    market = db.Column(db.String(10), nullable=False)  # HK或US
    transaction_type = db.Column(db.String(10), nullable=False)  # BUY或SELL
    transaction_date = db.Column(db.DateTime, nullable=False)
    exchange_rate = db.Column(db.Float)  # 交易日期的汇率，非港股市场使用
    
    # 费用明细
    broker_fee = db.Column(db.Float, default=0.0)  # 经纪佣金
    stamp_duty = db.Column(db.Float, default=0.0)  # 印花税
    transaction_levy = db.Column(db.Float, default=0.0)  # 交易征费
    trading_fee = db.Column(db.Float, default=0.0)  # 交易费
    clearing_fee = db.Column(db.Float, default=0.0)  # 结算费
    deposit_fee = db.Column(db.Float, default=0.0)  # 存入证券费
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    details = db.relationship('StockTransactionDetail', backref='transaction', lazy=True)
    
    @property
    def total_quantity(self):
        """计算总成交数量"""
        return sum(detail.quantity for detail in self.details)
    
    @property
    def total_amount(self):
        """计算总成交金额"""
        return sum(detail.quantity * detail.price for detail in self.details)
    
    @property
    def total_amount_hkd(self):
        """计算港币总金额"""
        amount = self.total_amount
        if self.market != 'HK' and self.exchange_rate:
            amount = amount * self.exchange_rate
        return amount
    
    @property
    def average_price(self):
        """计算平均成交价格"""
        if self.total_quantity == 0:
            return 0
        return self.total_amount / self.total_quantity
    
    @property
    def total_fees(self):
        """计算总费用"""
        return (self.broker_fee + self.stamp_duty +
                self.transaction_levy + self.trading_fee + self.clearing_fee +
                self.deposit_fee)
    
    @property
    def net_amount(self):
        """计算净金额（买入为负，卖出为正）"""
        amount = self.total_amount
        if self.transaction_type == 'BUY':
            return -(amount + self.total_fees)
        else:
            return amount - self.total_fees
            
    @property
    def net_amount_hkd(self):
        """计算港币净金额"""
        amount = self.net_amount
        if self.market != 'HK' and self.exchange_rate:
            amount = amount * self.exchange_rate
        return amount

class StockTransactionDetail(db.Model):
    """交易明细表，包含具体的成交记录"""
    __tablename__ = 'stock_transaction_details'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('stock_transactions.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # 成交数量
    price = db.Column(db.Float, nullable=False)  # 成交价格
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def amount(self):
        """计算成交金额"""
        return self.quantity * self.price 

class ExchangeRate(db.Model):
    """汇率记录表"""
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), nullable=False)  # 货币代码，如 USD
    rate_date = db.Column(db.Date, nullable=False)  # 汇率日期
    rate = db.Column(db.Float, nullable=False)  # 对港币的汇率
    source = db.Column(db.String(20), nullable=False)  # 汇率来源：GOOGLE_REALTIME, GOOGLE_YTD, MANUAL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('currency', 'rate_date', name='uix_currency_date'),
    )

class Stock(db.Model):
    """股票信息表"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)  # 股票代码
    market = db.Column(db.String(10), nullable=False)  # 市场：HK或USA
    name = db.Column(db.String(100), nullable=False)  # 股票名称（中文）
    full_name = db.Column(db.String(200))  # 公司全称
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('code', 'market', name='uix_code_market'),
    ) 