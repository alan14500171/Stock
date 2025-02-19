from datetime import datetime
from .base import BaseModel, db

class Stock(BaseModel):
    """股票基本信息模型"""
    __tablename__ = 'stocks'
    
    code = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(100))
    market = db.Column(db.String(10), nullable=False, index=True)
    full_name = db.Column(db.String(200))
    
    # 添加唯一约束
    __table_args__ = (
        db.UniqueConstraint('code', 'market', name='uix_stock_code_market'),
    )
    
    def __repr__(self):
        return f'<Stock {self.market}:{self.code}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'market': self.market,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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