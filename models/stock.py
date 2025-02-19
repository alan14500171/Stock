from datetime import datetime
from .base import db

class Stock(db.Model):
    """股票信息表"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)  # 股票代码
    market = db.Column(db.String(10), nullable=False)  # 市场：HK或USA
    name = db.Column(db.String(100), nullable=False)  # 股票名称（中文）
    full_name = db.Column(db.String(200))  # 公司全称
    industry = db.Column(db.String(50))  # 行业
    currency = db.Column(db.String(3))  # 交易货币
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('code', 'market', name='uix_code_market'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'market': self.market,
            'name': self.name,
            'full_name': self.full_name,
            'industry': self.industry,
            'currency': self.currency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    @classmethod
    def find_by_code_and_market(cls, code, market):
        """根据股票代码和市场查找股票"""
        return cls.query.filter_by(code=code, market=market).first()
        
    @classmethod
    def get_all_by_market(cls, market=None):
        """获取指定市场的所有股票"""
        query = cls.query
        if market:
            query = query.filter_by(market=market)
        return query.order_by(cls.market, cls.code).all() 