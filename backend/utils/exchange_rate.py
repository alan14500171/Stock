from datetime import datetime
from services.currency_checker import CurrencyChecker

checker = CurrencyChecker()

def get_exchange_rate(currency, date=None):
    """获取指定货币对港币的汇率
    
    Args:
        currency: 货币代码（如 'USD'）
        date: 日期对象或日期字符串（格式：YYYY-MM-DD），如果为 None 则获取实时汇率
        
    Returns:
        float: 汇率值，如果获取失败则返回 None
    """
    if currency == 'HK':
        return 1.0
        
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
        
    return checker.get_exchange_rate(currency, date) 