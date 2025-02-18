from main import app
from models import db, StockTransaction
from routes.stock import calculate_stats

def test_smr():
    with app.app_context():
        # 获取SMR的所有交易记录
        transactions = StockTransaction.query.filter_by(stock_code='SMR').all()
        
        # 计算统计数据
        market_stats, stock_stats = calculate_stats(transactions)
        
        # 打印SMR的交易详情
        if 'SMR' in stock_stats:
            smr = stock_stats['SMR']
            print('\n=== SMR交易统计 ===')
            print(f'市场: {smr["market"]}')
            print(f'总买入: {smr["total_buy"]}')
            print(f'总卖出: {smr["total_sell"]}')
            print(f'总费用: {smr["total_fees"]}')
            print(f'已实现盈亏: {smr["realized_profit"]}')
            print('\n=== 交易明细 ===')
            for trans in smr['transactions']:
                print(f'\n日期: {trans["transaction_date"]}')
                print(f'类型: {trans["transaction_type"]}')
                print(f'数量: {trans["total_quantity"]}')
                print(f'金额: {trans["total_amount"]}')
                print(f'费用: {trans["total_fees"]}')
                if trans["transaction_type"] == 'SELL':
                    print(f'盈亏: {trans.get("profit")}')
                    print(f'盈亏率: {trans.get("profit_rate")}%')
                    print('成本明细:')
                    for detail in trans.get("fifo_cost_details", []):
                        print(f'  - {detail["quantity"]}股 @ {detail["price"]} (含费用: {detail["fees"]})')
        else:
            print('未找到SMR的交易记录')

if __name__ == '__main__':
    test_smr() 