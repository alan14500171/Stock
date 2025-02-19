from flask import Flask, render_template
from config.config import config
from config.database import init_db, db
from services.exchange_rate import ExchangeRateService

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    init_db(app)
    
    # 初始化汇率服务
    exchange_rate_service = ExchangeRateService()
    exchange_rate_service.init_app(app)
    
    # 注册蓝图
    from routes import auth_bp, stock_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(stock_bp)
    
    # 注册主页路由
    @app.route('/')
    def index():
        return render_template('index.html')
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    ) 