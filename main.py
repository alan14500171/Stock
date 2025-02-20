from flask import Flask, make_response, request, jsonify
from config.config import config
from config.database import db
from services.exchange_rate import ExchangeRateService
import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_app(config_name='development'):
    # 创建日志目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 添加RotatingFileHandler
    handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 设置 session 配置
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设置为False
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # session过期时间
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.secret_key = os.environ.get('SECRET_KEY') or 'dev'
    
    # 初始化数据库连接
    db_config = {
        'host': '172.16.0.109',
        'user': 'root',
        'password': 'Zxc000123',
        'database': 'stock',
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
    
    # 错误处理
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器错误: {error}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在'
        }), 404
    
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