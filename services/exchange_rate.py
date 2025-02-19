from datetime import datetime
from config.database import db
from .currency_checker import CurrencyChecker
import logging

logger = logging.getLogger(__name__)

class ExchangeRateService:
    """汇率服务类"""
    
    def __init__(self, app=None):
        self.app = app
        self.currency_checker = CurrencyChecker()
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        
    def init_app(self, app):
        self.app = app
        
    def update_missing_rates(self):
        """更新缺失的汇率记录"""
        try:
            # 获取所有没有汇率的交易记录
            sql = """
                SELECT * FROM stock_transactions 
                WHERE market != 'HK' AND exchange_rate IS NULL
            """
            transactions = db.fetch_all(sql)
            
            updated_count = 0
            failed_count = 0
            
            for trans in transactions:
                rate = self.currency_checker.get_exchange_rate(f'{trans["market"]}/HKD')
                if rate:
                    update_sql = """
                        UPDATE stock_transactions 
                        SET exchange_rate = %s 
                        WHERE id = %s
                    """
                    if db.execute(update_sql, (rate, trans['id'])):
                        updated_count += 1
                else:
                    failed_count += 1
                    
            return {
                'updated': updated_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f'更新汇率时出错: {str(e)}')
            return {
                'updated': 0,
                'failed': 0,
                'error': str(e)
            }
            
    def get_exchange_rate(self, currency, date=None):
        """获取指定货币对港币的汇率"""
        if currency == 'HKD':
            return 1.0
            
        # 如果提供了日期，先查找数据库
        if date:
            sql = """
                SELECT rate FROM exchange_rates 
                WHERE currency = %s AND rate_date = %s
            """
            result = db.fetch_one(sql, (currency, date))
            if result:
                return result['rate']
        
        try:
            # 从API获取最新汇率
            rate = self.currency_checker.get_exchange_rate(f'{currency}/HKD')
            if rate:
                # 保存到数据库
                if date:
                    sql = """
                        INSERT INTO exchange_rates 
                        (currency, rate, rate_date, source) 
                        VALUES (%s, %s, %s, 'API')
                    """
                    db.execute(sql, (currency, rate, date))
                return rate
                
        except Exception as e:
            logger.error(f"获取汇率失败: {str(e)}")
            
        # 如果获取失败，返回默认值1.0
        return 1.0 