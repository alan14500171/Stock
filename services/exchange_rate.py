from datetime import datetime, timedelta
from models.stock import Stock
from models.transaction import StockTransaction
from config.database import db
from .currency_checker import CurrencyChecker
import logging
import requests
from models import ExchangeRate

logger = logging.getLogger(__name__)

class ExchangeRateService:
    """汇率服务类"""
    
    def __init__(self, app=None):
        self.app = app
        self.currency_checker = CurrencyChecker()
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.api_key = None  # 如果需要API key，在这里设置
        
    def init_app(self, app):
        self.app = app
        
    def update_missing_rates(self):
        """
        更新缺失的汇率记录
        """
        try:
            # 获取所有没有汇率的交易记录
            transactions = StockTransaction.query.filter(
                StockTransaction.market != 'HK',
                StockTransaction.exchange_rate.is_(None)
            ).all()
            
            updated_count = 0
            failed_count = 0
            
            for trans in transactions:
                rate = self.currency_checker.get_exchange_rate(f'{trans.market}/HKD')
                if rate:
                    trans.exchange_rate = rate
                    updated_count += 1
                else:
                    failed_count += 1
                    
            if updated_count > 0:
                db.session.commit()
                
            return {
                'updated': updated_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f'更新汇率时出错: {str(e)}')
            db.session.rollback()
            return {
                'updated': 0,
                'failed': 0,
                'error': str(e)
            }
            
    def get_exchange_rate(self, currency, date=None):
        """获取指定货币对港币的汇率
        
        Args:
            currency: 货币代码（例如：USD）
            date: 日期字符串（YYYY-MM-DD格式）
            
        Returns:
            float: 汇率值
        """
        if currency == 'HKD':
            return 1.0
            
        # 如果提供了日期，先查找数据库
        if date:
            rate_record = ExchangeRate.find_by_date(currency, date)
            if rate_record:
                return rate_record.rate
        
        try:
            # 从API获取最新汇率
            response = requests.get(f"{self.base_url}/HKD")
            if response.status_code == 200:
                data = response.json()
                rate = 1 / data['rates'].get(currency, 1.0)  # 转换为对HKD的汇率
                
                # 保存到数据库
                if date:
                    self.save_exchange_rate(currency, rate, date)
                return rate
                
        except Exception as e:
            logger.error(f"获取汇率失败: {str(e)}")
            
        # 如果API调用失败，返回默认值1.0
        return 1.0
        
    def save_exchange_rate(self, currency, rate, date):
        """保存汇率到数据库"""
        try:
            rate_date = datetime.strptime(date, '%Y-%m-%d').date()
            exchange_rate = ExchangeRate(
                currency=currency,
                rate=rate,
                rate_date=rate_date
            )
            db.session.add(exchange_rate)
            db.session.commit()
        except Exception as e:
            logger.error(f"保存汇率失败: {str(e)}")
            db.session.rollback() 