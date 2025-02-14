import os
import sys

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from flask import Flask
from models import db, ExchangeRate
from config import Config
from datetime import datetime
from sqlalchemy import text

def add_source_field():
    """为汇率表添加来源字段并更新现有记录"""
    try:
        # 创建Flask应用
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            # 添加source字段
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE exchange_rates ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT "MANUAL"'))
                conn.commit()
            
            print('成功添加source字段')
            
            # 更新现有记录
            today = datetime.now().date()
            
            # 将今天的记录标记为实时汇率
            db.session.query(ExchangeRate).filter(
                ExchangeRate.rate_date == today
            ).update({
                'source': 'GOOGLE_REALTIME'
            })
            
            # 将历史记录标记为历史汇率
            db.session.query(ExchangeRate).filter(
                ExchangeRate.rate_date < today
            ).update({
                'source': 'GOOGLE_YTD'
            })
            
            db.session.commit()
            print('成功更新现有记录的来源字段')
            
    except Exception as e:
        print(f'迁移失败: {str(e)}')
        if 'app_context' in locals():
            with app.app_context():
                db.session.rollback()

if __name__ == '__main__':
    add_source_field() 