from datetime import datetime
from .base import db

class ExchangeRate(db.Model):
    """汇率模型"""
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), nullable=False, index=True)
    rate = db.Column(db.Float, nullable=False)
    rate_date = db.Column(db.Date, nullable=False, index=True)
    source = db.Column(db.String(50))  # 数据来源
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 添加唯一约束
    __table_args__ = (
        db.UniqueConstraint('currency', 'rate_date', name='uix_currency_date'),
    )
    
    def __repr__(self):
        return f'<ExchangeRate {self.currency}@{self.rate_date}>'
        
    @classmethod
    def find_by_date(cls, currency, date_str):
        """根据货币和日期查找汇率记录"""
        try:
            rate_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            return cls.query.filter_by(
                currency=currency,
                rate_date=rate_date
            ).first()
        except:
            return None
            
    def to_dict(self):
        return {
            'id': self.id,
            'currency': self.currency,
            'rate': self.rate,
            'rate_date': self.rate_date.isoformat(),
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 