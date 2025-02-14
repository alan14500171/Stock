import yfinance as yf

def test_stock_price():
    # 测试港股
    tencent = yf.Ticker("0700.HK")
    print("\n腾讯控股 (0700.HK):")
    print(f"当前价格: {tencent.info.get('currentPrice', '未获取到')} HKD")
    
    # 测试美股
    apple = yf.Ticker("AAPL")
    print("\n苹果公司 (AAPL):")
    print(f"当前价格: {apple.info.get('currentPrice', '未获取到')} USD")

if __name__ == "__main__":
    print("开始测试 yfinance 股票数据获取...")
    test_stock_price()
    print("\n测试完成!") 