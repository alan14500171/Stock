from flask import Flask
from config.config import config
from config.database import db
from services.exchange_rate import ExchangeRateService
from flask_cors import CORS
from flask_login import LoginManager
from models.user import User

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化数据库连接
    db_config = {
        'host': '172.16.0.109',
        'user': 'root',
        'password': 'Zxc000123',
        'database': 'Stock',
        'port': 3306
    }
    if not db.connect(db_config):
        raise Exception("数据库连接失败")
    
    # 初始化Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))
    
    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:9009"],
            "supports_credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })
    
    # 初始化汇率服务
    exchange_rate_service = ExchangeRateService()
    exchange_rate_service.init_app(app)
    
    # 注册蓝图
    from routes import auth_bp, stock_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(stock_bp, url_prefix='/api/stock')
    
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