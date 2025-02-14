import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

def get_hsbc_rate():
    """从汇丰银行网站获取实时汇率"""
    try:
        url = 'https://www.hsbc.com.hk/zh-cn/investments/products/foreign-exchange/currency-rate/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找页面中所有的表格
        tables = soup.find_all('table')
        
        # 遍历所有表格查找USD汇率
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    currency = cells[0].get_text(strip=True)
                    if 'USD' in currency:
                        try:
                            rate = cells[1].get_text(strip=True)
                            # 移除可能的非数字字符
                            rate = ''.join(c for c in rate if c.isdigit() or c == '.')
                            return float(rate)
                        except (ValueError, IndexError) as e:
                            print(f"无法解析汇丰银行汇率值: {e}")
                            continue
        
        print("在汇丰银行网站上未找到USD汇率信息")
        return None
        
    except Exception as e:
        print(f"从汇丰银行获取汇率时发生错误: {str(e)}")
        return None

def get_xe_rate(date_str):
    """从XE.com获取历史汇率"""
    try:
        # 构建URL
        url = f'https://www.xe.com/zh-cn/currencytables/?from=USD&date={date_str}#table-section'
        
        # 发送请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"网络请求失败: {str(e)}")
                    return None
                time.sleep(1)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print("未找到汇率表格")
            return None
            
        table_rows = table.find_all('tr')
        
        for row in table_rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                currency_text = cells[0].get_text(strip=True)
                if 'HKD' in currency_text:
                    try:
                        rate = cells[2].get_text(strip=True)
                        return float(rate)
                    except (ValueError, IndexError):
                        print("无法解析汇率值")
                        return None
        
        print("未找到HKD的汇率信息")
        return None
    
    except Exception as e:
        print(f"从XE.com获取汇率时发生错误: {str(e)}")
        return None

def get_hkd_rate(date_str):
    try:
        # 验证日期格式
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # 检查是否是未来日期
        if date_obj > datetime.now():
            print("错误：不能查询未来日期的汇率")
            return None
            
        # 计算日期差异
        days_difference = (datetime.now() - date_obj).days
        
        # 如果是最近2天内的数据，从汇丰银行获取
        if days_difference <= 2:
            print("正在从汇丰银行获取实时汇率...")
            rate = get_hsbc_rate()
            if rate:
                return 1/rate  # 转换为HKD/USD的格式
            else:
                print("从汇丰银行获取汇率失败，尝试从XE.com获取...")
                return get_xe_rate(date_str)
        else:
            print("正在从XE.com获取历史汇率...")
            return get_xe_rate(date_str)
    
    except ValueError as e:
        print(f"日期格式错误: {str(e)}")
        return None
    except Exception as e:
        print(f"发生未知错误: {str(e)}")
        return None

def main():
    print("欢迎使用汇率查询程序！")
    print("说明：")
    print("1. 输入日期格式为：YYYY-MM-DD")
    print("2. 最近2天内的汇率将从汇丰银行获取实时数据")
    print("3. 更早的历史汇率将从XE.com获取")
    print("4. 输入 'q' 退出程序")
    print("-" * 50)
    
    while True:
        try:
            date_str = input("\n请输入日期 (格式: YYYY-MM-DD，输入 'q' 退出): ").strip()
            if date_str.lower() == 'q':
                print("感谢使用，再见！")
                break
                
            rate = get_hkd_rate(date_str)
            if rate:
                print(f"\n在 {date_str} 的 HKD/USD 汇率为: {rate}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")
            continue

if __name__ == "__main__":
    main() 