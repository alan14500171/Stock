"""
用户管理API路由
"""
from flask import Blueprint, request, jsonify, session
from models import User, Role, UserRole
from utils.auth import login_required, permission_required, get_current_user
from config.database import db
import logging

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)

@user_bp.route('/list', methods=['GET'])
@login_required
@permission_required('system:user:view')
def get_user_list():
    """获取用户列表"""
    try:
        # 获取查询参数
        username = request.args.get('username', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # 构建SQL
        sql = "SELECT * FROM stock.users WHERE 1=1"
        params = []
        
        if username:
            sql += " AND username LIKE %s"
            params.append(f"%{username}%")
            
        # 获取总数
        count_sql = sql.replace("*", "COUNT(*) as count")
        total = db.fetch_one(count_sql, params)['count']
        
        # 分页
        sql += " ORDER BY id DESC LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        # 查询数据
        users_data = db.fetch_all(sql, params)
        users = []
        
        for user_data in users_data:
            user = User(user_data)
            user_dict = user.to_dict()
            
            # 获取用户角色
            roles = Role.get_user_roles(user.id)
            user_dict['roles'] = [role.to_dict() for role in roles]
            
            users.append(user_dict)
            
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'items': users
            }
        })
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取用户列表失败: {str(e)}"
        }), 500

@user_bp.route('/info', methods=['GET'])
@login_required
def get_user_info():
    """获取当前用户信息"""
    try:
        user = get_current_user()
        logger.info(f"获取用户信息: {user.username if user else 'None'}")
        
        if not user:
            return jsonify({
                'success': False,
                'message': '获取用户信息失败'
            }), 401
            
        user_dict = user.to_dict()
        logger.info(f"用户基本信息: {user_dict}")
        
        # 获取用户角色
        roles = Role.get_user_roles(user.id)
        logger.info(f"用户角色: {[role.name for role in roles]}")
        user_dict['roles'] = [role.to_dict() for role in roles]
        
        # 获取用户权限
        from models import Permission
        permissions = Permission.get_user_permissions(user.id)
        logger.info(f"用户权限数量: {len(permissions)}")
        
        # 详细记录权限信息
        permission_details = []
        for p in permissions:
            permission_details.append({
                'id': p.id,
                'name': p.name,
                'code': p.code,
                'is_menu': p.is_menu
            })
        logger.info(f"用户权限详情: {permission_details}")
        
        # 只返回权限代码列表
        permission_codes = [permission.code for permission in permissions]
        logger.info(f"用户权限代码: {permission_codes}")
        user_dict['permissions'] = permission_codes
        
        # 获取用户菜单
        menus = [p for p in permissions if p.is_menu]
        logger.info(f"用户菜单数量: {len(menus)}")
        user_dict['menus'] = [menu.to_dict() for menu in menus]
        
        # 记录最终返回的用户信息
        logger.info(f"返回的用户信息: {user_dict}")
        
        return jsonify({
            'success': True,
            'data': user_dict
        })
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取用户信息失败: {str(e)}"
        }), 500

@user_bp.route('/available', methods=['GET'])
@login_required
def get_available_users():
    """获取可用于关联持有人的用户列表"""
    try:
        # 查询所有已激活的用户，允许一个用户关联多个持有人
        sql = """
        SELECT u.id, u.username, u.display_name 
        FROM stock.users u 
        WHERE u.is_active = 1
        ORDER BY u.username
        """
        users_data = db.fetch_all(sql)
        
        return jsonify({
            'success': True,
            'data': users_data
        })
    except Exception as e:
        logger.error(f"获取可用用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取可用用户列表失败: {str(e)}"
        }), 500

@user_bp.route('/detail/<int:user_id>', methods=['GET'])
@login_required
@permission_required('system:user:view')
def get_user_detail(user_id):
    """获取用户详情"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        user_dict = user.to_dict()
        
        # 获取用户角色
        roles = Role.get_user_roles(user.id)
        user_dict['roles'] = [role.to_dict() for role in roles]
        
        return jsonify({
            'success': True,
            'data': user_dict
        })
    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取用户详情失败: {str(e)}"
        }), 500

@user_bp.route('/add', methods=['POST'])
@login_required
@permission_required('system:user:add')
def add_user():
    """添加用户"""
    try:
        data = request.get_json()
        
        # 验证数据
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
            
        # 检查用户名是否已存在
        existing_user = User.find_by_username(username)
        if existing_user:
            return jsonify({
                'success': False,
                'message': f'用户名 {username} 已存在'
            }), 400
            
        # 创建用户
        user = User({
            'username': username,
            'is_active': data.get('is_active', True)
        })
        user.set_password(password)
        
        if not user.save():
            return jsonify({
                'success': False,
                'message': '添加用户失败'
            }), 500
            
        # 分配角色
        role_ids = data.get('role_ids', [])
        if role_ids:
            UserRole.assign_roles_to_user(user.id, role_ids)
            
        # 自动创建同名持有人
        try:
            # 检查持有人名称是否已存在
            check_sql = "SELECT COUNT(*) as count FROM holders WHERE name = %s"
            result = db.fetch_one(check_sql, [username])
            count = result['count'] if result else 0
            
            # 如果不存在，则创建持有人
            if count == 0:
                insert_sql = """
                INSERT INTO holders (name, type, user_id, status)
                VALUES (%s, %s, %s, %s)
                """
                db.execute(insert_sql, [username, 'individual', user.id, 1])
                logger.info(f"为用户 {username} 自动创建了同名持有人")
            
        except Exception as e:
            logger.error(f"为用户 {username} 创建持有人失败: {str(e)}")
            
        return jsonify({
            'success': True,
            'message': '添加用户成功',
            'data': user.to_dict()
        })
    except Exception as e:
        logger.error(f"添加用户失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"添加用户失败: {str(e)}"
        }), 500

@user_bp.route('/update/<int:user_id>', methods=['PUT'])
@login_required
@permission_required('system:user:edit')
def update_user(user_id):
    """更新用户信息"""
    try:
        data = request.get_json()
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404

        # 更新基本信息
        if 'username' in data:
            user.username = data['username']
        if 'name' in data:
            user.name = data['name']  # 将存储到 display_name 字段
        if 'email' in data:
            user.email = data['email']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'password' in data and data['password']:
            user.set_password(data['password'])

        if not user.save():
            return jsonify({'code': 500, 'message': '更新用户失败'}), 500

        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': user.to_dict()
        })

    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@login_required
@permission_required('system:user:delete')
def delete_user(user_id):
    """删除用户"""
    try:
        # 获取用户
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        # 不能删除自己
        current_user = get_current_user()
        if current_user.id == user.id:
            return jsonify({
                'success': False,
                'message': '不能删除当前登录用户'
            }), 400
            
        # 删除用户角色关联
        UserRole.delete_by_user(user.id)
        
        # 删除用户
        db.execute("DELETE FROM stock.users WHERE id = %s", (user.id,))
        
        return jsonify({
            'success': True,
            'message': '删除用户成功'
        })
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"删除用户失败: {str(e)}"
        }), 500

@user_bp.route('/assign-roles/<int:user_id>', methods=['POST'])
@login_required
@permission_required('system:user:assign')
def assign_roles(user_id):
    """为用户分配角色"""
    try:
        data = request.get_json()
        role_ids = data.get('role_ids', [])
        
        # 获取用户
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        # 分配角色
        if UserRole.assign_roles_to_user(user.id, role_ids):
            return jsonify({
                'success': True,
                'message': '分配角色成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '分配角色失败'
            }), 500
    except Exception as e:
        logger.error(f"分配角色失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"分配角色失败: {str(e)}"
        }), 500 