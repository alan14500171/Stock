from flask import Flask
from models import db, StockTransaction
from config import Config

def migrate_market_codes():
    """将市场代码从US更新为USA"""
    try:
        # 创建Flask应用
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            # 查找所有使用US市场代码的记录
            transactions = StockTransaction.query.filter_by(market='US').all()
            count = len(transactions)
            
            if count == 0:
                print('没有需要更新的记录')
                return
            
            # 更新市场代码
            for transaction in transactions:
                transaction.market = 'USA'
            
            # 提交更改
            db.session.commit()
            print(f'成功更新 {count} 条记录的市场代码从 US 到 USA')
            
    except Exception as e:
        print(f'迁移失败: {str(e)}')
        db.session.rollback()

if __name__ == '__main__':
    migrate_market_codes() 