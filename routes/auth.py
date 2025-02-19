from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models import db, User
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            })
        
        new_user = User(username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功'
        })
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.id
            return jsonify({
                'success': True,
                'message': '登录成功'
            })
        
        return jsonify({
            'success': False,
            'message': '用户名或密码错误'
        })
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    try:
        logout_user()
        session.clear()  # 清除所有会话数据
        return jsonify({
            'success': True,
            'message': '退出登录成功',
            'redirect': url_for('auth.login')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 