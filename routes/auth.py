from flask import Blueprint, request, session, jsonify
from functools import wraps
from models.user import User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册API"""
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': '用户名和密码不能为空'
        }), 400
    
    if User.find_by_username(username):
        return jsonify({
            'success': False,
            'message': '用户名已存在'
        }), 400
    
    new_user = User()
    new_user.username = username
    new_user.set_password(password)
    
    if new_user.save():
        return jsonify({
            'success': True,
            'message': '注册成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '注册失败'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录API"""
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': '用户名和密码不能为空'
        }), 400
    
    user = User.find_by_username(username)
    if user and user.check_password(password):
        session['user_id'] = user.id
        user.update_last_login()
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': user.to_dict()
        })
    
    return jsonify({
        'success': False,
        'message': '用户名或密码错误'
    }), 401

@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录API"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': '退出登录成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth_bp.route('/check_login')
def check_login():
    """检查登录状态API"""
    is_authenticated = 'user_id' in session
    user = None
    if is_authenticated:
        user = User.get_by_id(session.get('user_id'))
        if not user:
            is_authenticated = False
            session.clear()
    
    return jsonify({
        'success': True,
        'is_authenticated': is_authenticated,
        'user': user.to_dict() if user else None
    }) 