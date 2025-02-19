from flask import Flask
from flask_login import LoginManager
from config.config import config
from config.database import init_db
from models.user import User
from services.exchange_rate import ExchangeRateService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# 初始化汇率服务
exchange_rate_service = ExchangeRateService()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化数据库
    init_db(app)
    
    # 初始化 Flask-Login
    login_manager.init_app(app)
    
    # 初始化汇率服务
    exchange_rate_service.init_app(app)
    
    # 注册蓝图
    from routes.stock_routes import stock_bp
    from routes.user_routes import user_bp
    
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    return app
    
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 