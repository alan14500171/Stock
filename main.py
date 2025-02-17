from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from config import Config
from models import db
from routes.auth import auth_bp
from routes.stock import stock_bp

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap5(app)
db.init_app(app)

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(stock_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG']) 