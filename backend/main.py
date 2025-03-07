from flask import Flask, send_from_directory, jsonify, request
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config.database import db
from flask_cors import CORS
from config.logging import setup_logging
from config.db_config import get_db_config

# 导入路由
from routes.auth import auth_bp
from routes.stock import stock_bp
from routes.profit import profit_bp
from routes.user import user_bp
from routes.role import role_bp
from routes.permission import permission_bp
from routes.transaction_split import transaction_split_bp
from routes.holder import holder_bp

# 设置日志
setup_logging()

def create_app():
    # 创建应用实例
    app = Flask(__name__, static_folder='../frontend/dist')

    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev_key'
    app.config['SESSION_COOKIE_SAMESITE'] = None  # 开发环境下允许跨站点请求
    app.config['SESSION_COOKIE_SECURE'] = False   # 开发环境使用HTTP
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_DOMAIN'] = None    # 允许所有域
    app.config['JSON_AS_ASCII'] = False  # 支持中文
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大请求大小16MB

    # 添加CORS支持
    CORS(app, supports_credentials=True, resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:9009",
                "http://127.0.0.1:9009",
                "http://10.188.18.196:9009"  # 添加本地网络地址
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True
        }
    })

    @app.after_request
    def after_request(response):
        allowed_origins = [
            'http://localhost:9009',
            'http://127.0.0.1:9009',
            'http://localhost:9099',
            'http://127.0.0.1:9099',
            'http://localhost:5173',
            'http://127.0.0.1:5173'
        ]
        origin = request.headers.get('Origin')
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Cache-Control, Pragma, Expires, X-CSRF-TOKEN, Accept, Origin, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Expose-Headers'] = 'Set-Cookie'
        return response

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(stock_bp, url_prefix='/api/stock')
    app.register_blueprint(profit_bp, url_prefix='/api/profit')
    
    # 注册权限管理相关蓝图
    app.register_blueprint(user_bp, url_prefix='/api/system/user')
    app.register_blueprint(role_bp, url_prefix='/api/system/role')
    app.register_blueprint(permission_bp, url_prefix='/api/system/permission')
    
    # 注册交易分单蓝图
    app.register_blueprint(transaction_split_bp)
    
    # 注册持有人管理蓝图
    app.register_blueprint(holder_bp)

    # 配置日志
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_file = os.path.join('logs', f'backend_{datetime.now().strftime("%Y%m%d")}.log')
    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # 初始化数据库连接
    try:
        db.init_pool('development')
        app.logger.info("数据库连接池初始化成功")
    except Exception as e:
        app.logger.error(f"数据库连接池初始化失败: {str(e)}")
        raise

    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'db_connected': db.is_connected()
        })

    # 错误处理
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'服务器错误: {str(error)}')
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'success': False,
            'message': '请求数据太大'
        }), 413

    # 前端路由处理
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app

if __name__ == '__main__':
    try:
        app = create_app()
        app.logger.info('应用启动成功')
        app.run(
            host='127.0.0.1',
            port=9099,
            debug=True,
            use_reloader=True
        )
    except Exception as e:
        logging.error(f'应用启动失败: {str(e)}')
        raise 