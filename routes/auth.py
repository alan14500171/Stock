from flask import Blueprint, request, session, jsonify
from models.user import User
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册API"""
    username = request.form.get('username')
    password = request.form.get('password')
    
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
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': '用户名和密码不能为空'
        }), 400
    
    user = User.find_by_username(username)
    if user and user.check_password(password):
        login_user(user)
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
        logout_user()
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