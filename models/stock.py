from datetime import datetime
from config.database import db
import logging

logger = logging.getLogger(__name__)

class Stock:
    """股票信息表"""
    def __init__(self, data=None):
        self.id = data.get('id') if data else None
        self.code = data.get('code') if data else None
        self.market = data.get('market') if data else None
        self.name = data.get('name') if data else None
        self.full_name = data.get('full_name') if data else None
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        self.updated_at = data.get('updated_at') if data else datetime.utcnow()
    
    def save(self):
        """保存或更新股票信息"""
        try:
            if self.id:
                # 更新
                sql = """
                    UPDATE stocks 
                    SET code = %s, market = %s, name = %s, 
                        full_name = %s, updated_at = NOW()
                    WHERE id = %s
                """
                params = [
                    self.code, self.market, self.name,
                    self.full_name, self.id
                ]
            else:
                # 新增
                sql = """
                    INSERT INTO stocks (
                        code, market, name, full_name, 
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, NOW(), NOW()
                    )
                """
                params = [
                    self.code, self.market, self.name,
                    self.full_name
                ]
            
            return db.execute(sql, params)
        except Exception as e:
            logger.error(f"保存股票失败: {str(e)}")
            return False
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'market': self.market,
            'name': self.name,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        
    @classmethod
    def find_by_code_and_market(cls, code, market):
        """根据股票代码和市场查找股票"""
        sql = "SELECT * FROM stocks WHERE code = %s AND market = %s"
        data = db.fetch_one(sql, (code, market))
        return cls(data) if data else None
        
    @classmethod
    def get_all_by_market(cls, market=None):
        """获取指定市场的所有股票"""
        sql = "SELECT * FROM stocks"
        params = []
        if market:
            sql += " WHERE market = %s"
            params.append(market)
        sql += " ORDER BY market, code"
        data = db.fetch_all(sql, params)
        return [cls(item) for item in data] 