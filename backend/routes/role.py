"""
角色管理API路由
"""
from flask import Blueprint, request, jsonify
from models import Role, Permission, RolePermission
from utils.auth import login_required, permission_required
from config.database import db
import logging

logger = logging.getLogger(__name__)
role_bp = Blueprint('role', __name__)

@role_bp.route('/list', methods=['GET'])
@login_required
@permission_required('system:role:view')
def get_role_list():
    """获取角色列表"""
    try:
        # 获取查询参数
        name = request.args.get('name', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # 构建SQL
        sql = "SELECT * FROM roles WHERE 1=1"
        params = []
        
        if name:
            sql += " AND name LIKE %s"
            params.append(f"%{name}%")
            
        # 获取总数
        count_sql = sql.replace("*", "COUNT(*) as count")
        total = db.fetch_one(count_sql, params)['count']
        
        # 分页
        sql += " ORDER BY id DESC LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        # 查询数据
        roles_data = db.fetch_all(sql, params)
        roles = []
        
        for role_data in roles_data:
            role = Role(role_data)
            role_dict = role.to_dict()
            
            # 获取角色权限
            permissions = Permission.get_role_permissions(role.id)
            role_dict['permissions'] = [permission.to_dict() for permission in permissions]
            
            roles.append(role_dict)
            
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'items': roles
            }
        })
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取角色列表失败: {str(e)}"
        }), 500

@role_bp.route('/all', methods=['GET'])
@login_required
def get_all_roles():
    """获取所有角色（不分页）"""
    try:
        roles = Role.get_all()
        return jsonify({
            'success': True,
            'data': [role.to_dict() for role in roles]
        })
    except Exception as e:
        logger.error(f"获取所有角色失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取所有角色失败: {str(e)}"
        }), 500

@role_bp.route('/detail/<int:role_id>', methods=['GET'])
@login_required
@permission_required('system:role:view')
def get_role_detail(role_id):
    """获取角色详情"""
    try:
        role = Role.get_by_id(role_id)
        if not role:
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404
            
        role_dict = role.to_dict()
        
        # 获取角色权限
        permissions = Permission.get_role_permissions(role.id)
        role_dict['permissions'] = [permission.to_dict() for permission in permissions]
        
        return jsonify({
            'success': True,
            'data': role_dict
        })
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取角色详情失败: {str(e)}"
        }), 500

@role_bp.route('/add', methods=['POST'])
@login_required
@permission_required('system:role:add')
def add_role():
    """添加角色"""
    try:
        data = request.get_json()
        
        # 验证数据
        name = data.get('name')
        description = data.get('description')
        
        if not name:
            return jsonify({
                'success': False,
                'message': '角色名称不能为空'
            }), 400
            
        # 检查角色名称是否已存在
        check_sql = "SELECT COUNT(*) as count FROM roles WHERE name = %s"
        result = db.fetch_one(check_sql, [name])
        if result and result['count'] > 0:
            return jsonify({
                'success': False,
                'message': f'角色名称 {name} 已存在'
            }), 400
            
        # 创建角色
        insert_sql = """
            INSERT INTO roles (name, description, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
        """
        role_id = db.insert(insert_sql, [name, description])
        
        if not role_id:
            return jsonify({
                'success': False,
                'message': '添加角色失败'
            }), 500
            
        # 分配权限
        permission_ids = data.get('permission_ids', [])
        if permission_ids:
            RolePermission.assign_permissions_to_role(role_id, permission_ids)
            
        # 获取新创建的角色
        sql = "SELECT * FROM roles WHERE id = %s"
        role = db.fetch_one(sql, [role_id])
            
        return jsonify({
            'success': True,
            'message': '添加角色成功',
            'data': role
        })
    except Exception as e:
        logger.error(f"添加角色失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"添加角色失败: {str(e)}"
        }), 500

@role_bp.route('/update/<int:role_id>', methods=['PUT'])
@login_required
@permission_required('system:role:edit')
def update_role(role_id):
    """更新角色"""
    try:
        data = request.get_json()
        
        # 获取角色
        sql = "SELECT * FROM roles WHERE id = %s"
        role = db.fetch_one(sql, [role_id])
        if not role:
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404
            
        # 更新角色信息
        name = data.get('name')
        description = data.get('description')
        
        if name:
            # 检查角色名称是否已存在
            check_sql = "SELECT COUNT(*) as count FROM roles WHERE name = %s AND id != %s"
            result = db.fetch_one(check_sql, [name, role_id])
            if result and result['count'] > 0:
                return jsonify({
                    'success': False,
                    'message': f'角色名称 {name} 已存在'
                }), 400
                
        # 更新角色
        update_sql = """
            UPDATE roles 
            SET name = %s, description = %s, updated_at = NOW()
            WHERE id = %s
        """
        if not db.execute(update_sql, [name, description, role_id]):
            return jsonify({
                'success': False,
                'message': '更新角色失败'
            }), 500
            
        # 分配权限
        if 'permission_ids' in data:
            RolePermission.assign_permissions_to_role(role_id, data['permission_ids'])
            
        # 获取更新后的角色
        sql = "SELECT * FROM roles WHERE id = %s"
        updated_role = db.fetch_one(sql, [role_id])
            
        return jsonify({
            'success': True,
            'message': '更新角色成功',
            'data': updated_role
        })
    except Exception as e:
        logger.error(f"更新角色失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"更新角色失败: {str(e)}"
        }), 500

@role_bp.route('/delete/<int:role_id>', methods=['DELETE'])
@login_required
@permission_required('system:role:delete')
def delete_role(role_id):
    """删除角色"""
    try:
        # 获取角色
        sql = "SELECT * FROM roles WHERE id = %s"
        role = db.fetch_one(sql, [role_id])
        if not role:
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404
            
        # 删除角色
        delete_sql = "DELETE FROM roles WHERE id = %s"
        if not db.execute(delete_sql, [role_id]):
            return jsonify({
                'success': False,
                'message': '删除角色失败'
            }), 500
            
        return jsonify({
            'success': True,
            'message': '删除角色成功'
        })
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"删除角色失败: {str(e)}"
        }), 500

@role_bp.route('/assign-permissions/<int:role_id>', methods=['POST'])
@login_required
@permission_required('system:role:assign')
def assign_permissions(role_id):
    """为角色分配权限"""
    try:
        data = request.get_json()
        permission_ids = data.get('permission_ids', [])
        
        # 获取角色
        role = Role.get_by_id(role_id)
        if not role:
            return jsonify({
                'success': False,
                'message': '角色不存在'
            }), 404
            
        # 分配权限
        if RolePermission.assign_permissions_to_role(role.id, permission_ids):
            return jsonify({
                'success': True,
                'message': '分配权限成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '分配权限失败'
            }), 500
    except Exception as e:
        logger.error(f"分配权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"分配权限失败: {str(e)}"
        }), 500 