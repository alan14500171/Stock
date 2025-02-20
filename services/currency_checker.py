import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CurrencyChecker:
    @staticmethod
    def get_exchange_rate(query):
        """
        从谷歌获取实时汇率或股票价格
        :param query: 查询字符串，可以是股票代码(如 '0700:HKG') 或货币对(如 'USD/HKD')
        :return: 汇率值或股票价格，或 None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }

            # 构建 Google Finance URL
            if ':' in query:  # 股票查询
                url = f'https://www.google.com/finance/quote/{query}'
            else:  # 汇率查询
                if '/' in query:
                    from_currency, to_currency = query.split('/')
                    url = f'https://www.google.com/finance/quote/{from_currency}-{to_currency}'
                else:
                    url = f'https://www.google.com/finance/quote/{query}'

            logger.info(f"访问URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试不同的价格元素选择器
            price_div = soup.find('div', {'data-last-price': True})
            if price_div and price_div.get('data-last-price'):
                price = float(price_div.get('data-last-price'))
                return price
                
            # 如果找不到 data-last-price，尝试其他选择器
            price_span = soup.find('div', class_='YMlKec fxKbKc')
            if price_span:
                price_text = price_span.text.strip().replace(',', '')
                if price_text.startswith('$'):
                    price_text = price_text[1:]
                try:
                    return float(price_text)
                except ValueError:
                    pass
            
            logger.error('未找到价格元素')
            return None
                
        except Exception as e:
            logger.error(f'获取价格时出错: {str(e)}')
            return None
            
    @staticmethod
    def get_historical_rate(currency_pair, date):
        """
        获取历史汇率（待实现）
        :param currency_pair: 货币对或股票代码
        :param date: 日期
        :return: 汇率值或股票价格，或 None
        """
        # TODO: 实现历史汇率获取逻辑
        return None 