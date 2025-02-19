from flask import Blueprint, request, session, jsonify
from models import db, User
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
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            'success': False,
            'message': '用户名已存在'
        }), 400
    
    new_user = User(username=username)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '注册成功'
    })

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
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        session['user_id'] = user.id
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
    return jsonify({
        'success': True,
        'is_authenticated': is_authenticated,
        'user': User.query.get(session.get('user_id')).to_dict() if is_authenticated else None
    }) 