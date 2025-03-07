# 导入蓝图
from routes.auth import auth_bp
from routes.stock import stock_bp
from routes.transaction import transaction_bp
from routes.transaction_split import transaction_split_bp
from routes.transaction_detail import transaction_detail_bp
from routes.holder import holder_bp
from routes.profit import profit_bp
from routes.dashboard import dashboard_bp

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(transaction_bp)
app.register_blueprint(transaction_split_bp)
app.register_blueprint(transaction_detail_bp)
app.register_blueprint(holder_bp)
app.register_blueprint(profit_bp)
app.register_blueprint(dashboard_bp) 