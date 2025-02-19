from flask import Flask, make_response, request
from config.config import config
from config.database import db
from services.exchange_rate import ExchangeRateService
import os
import logging

def create_app(config_name='development'):
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 设置 session 密钥
    app.secret_key = os.environ.get('SECRET_KEY') or 'dev'
    
    # 初始化数据库连接
    db_config = {
        'host': '172.16.0.109',
        'user': 'root',
        'password': 'Zxc000123',
        'database': 'Stock',
        'port': 3306
    }
    if not db.connect(db_config):
        logger.error("数据库连接失败")
        raise Exception("数据库连接失败")
    else:
        logger.info("数据库连接成功")
    
    # 自定义CORS处理
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        allowed_origins = [
            'http://localhost:9009',
            'http://127.0.0.1:9009',
            'http://localhost:9099',
            'http://127.0.0.1:9099'
        ]
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            
            # 如果是 OPTIONS 请求，确保返回 200
            if request.method == 'OPTIONS':
                response.status_code = 200
                
        return response
    
    # 初始化汇率服务
    exchange_rate_service = ExchangeRateService()
    exchange_rate_service.init_app(app)
    
    # 注册蓝图
    from routes import auth_bp, stock_bp, profit_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(stock_bp, url_prefix='/api/stock')
    app.register_blueprint(profit_bp, url_prefix='/api/profit')
    
    return app

app = create_app()

if __name__ == '__main__':
    try:
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
    finally:
        db.close() 