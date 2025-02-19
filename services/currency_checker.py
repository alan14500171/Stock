import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CurrencyChecker:
    @staticmethod
    def get_exchange_rate(currency_pair):
        """
        从谷歌获取实时汇率
        :param currency_pair: 货币对，例如 'USD/HKD'
        :return: 汇率值或 None
        """
        try:
            url = f'https://www.google.com/search?q={currency_pair}+exchange+rate'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rate_element = soup.find('div', {'class': 'BNeawe iBp4i AP7Wnd'})
            
            if rate_element:
                rate_text = rate_element.text.strip()
                try:
                    return float(rate_text)
                except ValueError:
                    logger.error(f'无法解析汇率值: {rate_text}')
                    return None
            else:
                logger.error('未找到汇率元素')
                return None
                
        except Exception as e:
            logger.error(f'获取汇率时出错: {str(e)}')
            return None
            
    @staticmethod
    def get_historical_rate(currency_pair, date):
        """
        获取历史汇率（待实现）
        :param currency_pair: 货币对
        :param date: 日期
        :return: 汇率值或 None
        """
        # TODO: 实现历史汇率获取逻辑
        return None 