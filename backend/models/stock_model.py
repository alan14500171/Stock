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
        self.code_name = data.get('code_name') if data else None
        self.google_name = data.get('google_name') if data else None
        self.created_at = data.get('created_at') if data else datetime.utcnow()
        self.updated_at = data.get('updated_at') if data else datetime.utcnow()
    
    def save(self):
        """保存或更新股票信息"""
        try:
            # 验证必填字段
            if not self.code or not self.market or not self.code_name:
                logger.error("保存股票失败: 缺少必填字段")
                return False

            if self.id:
                # 更新
                sql = """
                    UPDATE stock.stocks 
                    SET code = %s, market = %s, code_name = %s, 
                        google_name = %s, updated_at = NOW()
                    WHERE id = %s
                """
                params = [
                    self.code, self.market, self.code_name,
                    self.google_name, self.id
                ]
            else:
                # 检查是否已存在相同代码的股票
                check_sql = "SELECT id FROM stock.stocks WHERE code = %s AND market = %s"
                existing = db.fetch_one(check_sql, [self.code, self.market])
                if existing:
                    logger.error(f"保存股票失败: 股票代码 {self.code} 在市场 {self.market} 已存在")
                    return False

                # 新增
                sql = """
                    INSERT INTO stock.stocks (
                        code, market, code_name, google_name, 
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, NOW(), NOW()
                    )
                """
                params = [
                    self.code, self.market, self.code_name,
                    self.google_name
                ]
            
            result = db.execute(sql, params)
            if not result:
                logger.error("保存股票失败: 数据库操作失败")
                return False
            return True
            
        except Exception as e:
            logger.error(f"保存股票失败: {str(e)}")
            raise e  # 向上抛出异常，让调用者处理
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'market': self.market,
            'code_name': self.code_name,
            'google_name': self.google_name,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        
    @classmethod
    def find_by_code_and_market(cls, code, market):
        """根据股票代码和市场查找股票"""
        sql = "SELECT * FROM stock.stocks WHERE code = %s AND market = %s"
        data = db.fetch_one(sql, (code, market))
        return cls(data) if data else None
        
    @classmethod
    def get_all_by_market(cls, market=None):
        """获取指定市场的所有股票"""
        sql = "SELECT * FROM stock.stocks"
        params = []
        if market:
            sql += " WHERE market = %s"
            params.append(market)
        sql += " ORDER BY market, code"
        data = db.fetch_all(sql, params)
        return [cls(item) for item in data] 