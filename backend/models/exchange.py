from datetime import datetime
from config.database import db

class ExchangeRate:
    """汇率模型"""
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.currency = data.get('currency') if data else None
        self.rate = data.get('rate') if data else None
        self.rate_date = data.get('rate_date') if data else None
        self.source = data.get('source') if data else None
        self.created_at = data.get('created_at') if data else datetime.utcnow()
    
    def __repr__(self):
        return f'<ExchangeRate {self.currency}@{self.rate_date}>'
        
    @classmethod
    def find_by_date(cls, currency, date_str):
        """根据货币和日期查找汇率记录"""
        try:
            rate_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            sql = "SELECT * FROM exchange_rates WHERE currency = %s AND rate_date = %s"
            data = db.fetch_one(sql, (currency, rate_date))
            return cls(data) if data else None
        except:
            return None
    
    @classmethod
    def find_temporary_rates(cls):
        """查找所有临时汇率记录"""
        try:
            sql = "SELECT * FROM exchange_rates WHERE source = 'TEMPORARY'"
            data = db.fetch_all(sql)
            return [cls(rate) for rate in data] if data else []
        except Exception as e:
            print(f"查找临时汇率记录失败: {str(e)}")
            return []
            
    def save(self):
        """保存或更新汇率记录"""
        if self.id:
            # 更新
            sql = """
                UPDATE exchange_rates 
                SET currency = %s, rate = %s, rate_date = %s,
                    source = %s
                WHERE id = %s
            """
            params = (self.currency, self.rate, self.rate_date,
                     self.source, self.id)
            return db.execute(sql, params)
        else:
            # 新增
            sql = """
                INSERT INTO exchange_rates 
                (currency, rate, rate_date, source, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (self.currency, self.rate, self.rate_date,
                     self.source, self.created_at)
            self.id = db.insert(sql, params)
            return bool(self.id)
            
    def to_dict(self):
        return {
            'id': self.id,
            'currency': self.currency,
            'rate': float(self.rate) if self.rate else None,
            'rate_date': self.rate_date.isoformat() if isinstance(self.rate_date, datetime) else self.rate_date,
            'source': self.source,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        } 