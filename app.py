from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.stock import stock_bp
from routes.profit import profit_bp
import logging
from logging.handlers import RotatingFileHandler
import os

# 创建日志目录
if not os.path.exists('logs'):
    os.makedirs('logs')

# 配置日志
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)

# 创建Flask应用
app = Flask(__name__)

# 配置应用
app.config.update(
    SECRET_KEY='your-secret-key-here',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,  # 开发环境设置为False
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,  # 会话有效期1小时
)

# 配置CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://127.0.0.1:9009", "http://localhost:9009"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-Requested-With"],
        "supports_credentials": True
    }
})

# 添加日志处理器
app.logger.addHandler(handler)

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(stock_bp, url_prefix='/api/stock')
app.register_blueprint(profit_bp, url_prefix='/api/profit')

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return {
        'success': False,
        'message': '服务器内部错误'
    }, 500

@app.errorhandler(404)
def not_found_error(error):
    return {
        'success': False,
        'message': '请求的资源不存在'
    }, 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9099, debug=True) 