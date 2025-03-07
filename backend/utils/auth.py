"""
权限验证工具
"""
import functools
from flask import request, jsonify, session
from models import User, Permission

def login_required(f):
    """登录验证装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission_code):
    """权限验证装饰器"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证登录
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'message': '请先登录'
                }), 401
                
            user_id = session['user_id']
            
            # 获取用户权限
            user_permissions = Permission.get_user_permissions(user_id)
            user_permission_codes = [p.code for p in user_permissions]
            
            # 验证权限
            if permission_code not in user_permission_codes:
                return jsonify({
                    'success': False,
                    'message': '权限不足'
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """获取当前登录用户"""
    if 'user_id' not in session:
        return None
        
    user_id = session['user_id']
    return User.get_by_id(user_id)

def has_permission(user_id, permission_code):
    """检查用户是否有指定权限"""
    # 获取用户权限
    user_permissions = Permission.get_user_permissions(user_id)
    user_permission_codes = [p.code for p in user_permissions]
    
    # 验证权限
    return permission_code in user_permission_codes 