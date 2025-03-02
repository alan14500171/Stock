"""
权限管理API路由
"""
from flask import Blueprint, request, jsonify
from models import Permission
from utils.auth import login_required, permission_required
import logging

logger = logging.getLogger(__name__)
permission_bp = Blueprint('permission', __name__)

@permission_bp.route('/list', methods=['GET'])
@login_required
@permission_required('system:permission:view')
def get_permission_list():
    """获取权限列表"""
    try:
        permissions = Permission.get_all()
        return jsonify({
            'success': True,
            'data': [permission.to_dict() for permission in permissions]
        })
    except Exception as e:
        logger.error(f"获取权限列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取权限列表失败: {str(e)}"
        }), 500

@permission_bp.route('/tree', methods=['GET'])
@login_required
@permission_required('system:permission:view')
def get_permission_tree():
    """获取权限树"""
    try:
        tree = Permission.get_permission_tree()
        return jsonify({
            'success': True,
            'data': tree
        })
    except Exception as e:
        logger.error(f"获取权限树失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取权限树失败: {str(e)}"
        }), 500

@permission_bp.route('/detail/<int:permission_id>', methods=['GET'])
@login_required
@permission_required('system:permission:view')
def get_permission_detail(permission_id):
    """获取权限详情"""
    try:
        permission = Permission.get_by_id(permission_id)
        if not permission:
            return jsonify({
                'success': False,
                'message': '权限不存在'
            }), 404
            
        return jsonify({
            'success': True,
            'data': permission.to_dict()
        })
    except Exception as e:
        logger.error(f"获取权限详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取权限详情失败: {str(e)}"
        }), 500

@permission_bp.route('/add', methods=['POST'])
@login_required
@permission_required('system:permission:add')
def add_permission():
    """添加权限"""
    try:
        data = request.get_json()
        
        # 验证数据
        name = data.get('name')
        code = data.get('code')
        
        if not name or not code:
            return jsonify({
                'success': False,
                'message': '权限名称和标识不能为空'
            }), 400
            
        # 检查权限标识是否已存在
        existing_permission = Permission.get_by_code(code)
        if existing_permission:
            return jsonify({
                'success': False,
                'message': f'权限标识 {code} 已存在'
            }), 400
            
        # 创建权限
        permission = Permission({
            'name': name,
            'code': code,
            'description': data.get('description'),
            'type': int(data.get('type', 3)),  # 确保处理type字段
            'parent_id': data.get('parent_id'),
            'sort_order': data.get('sort_order', 0),
            'is_menu': data.get('is_menu', False),
            'icon': data.get('icon'),
            'component': data.get('component'),
            'route_path': data.get('route_path')
        })
        
        if not permission.save():
            return jsonify({
                'success': False,
                'message': '添加权限失败'
            }), 500
            
        return jsonify({
            'success': True,
            'message': '添加权限成功',
            'data': permission.to_dict()
        })
    except Exception as e:
        logger.error(f"添加权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"添加权限失败: {str(e)}"
        }), 500

@permission_bp.route('/update/<int:permission_id>', methods=['PUT'])
@login_required
@permission_required('system:permission:edit')
def update_permission(permission_id):
    """更新权限"""
    try:
        data = request.get_json()
        
        # 获取权限
        permission = Permission.get_by_id(permission_id)
        if not permission:
            return jsonify({
                'success': False,
                'message': '权限不存在'
            }), 404
            
        # 更新权限信息
        if 'name' in data:
            permission.name = data['name']
            
        if 'code' in data:
            # 检查权限标识是否已存在
            existing_permission = Permission.get_by_code(data['code'])
            if existing_permission and existing_permission.id != permission.id:
                return jsonify({
                    'success': False,
                    'message': f'权限标识 {data["code"]} 已存在'
                }), 400
                
            permission.code = data['code']
            
        if 'description' in data:
            permission.description = data['description']
            
        if 'type' in data:
            permission.type = int(data['type'])
            
        if 'parent_id' in data:
            permission.parent_id = data['parent_id']
            
        if 'sort_order' in data:
            permission.sort_order = data['sort_order']
            
        if 'is_menu' in data:
            permission.is_menu = data['is_menu']
            
        if 'icon' in data:
            permission.icon = data['icon']
            
        if 'component' in data:
            permission.component = data['component']
            
        if 'route_path' in data:
            permission.route_path = data['route_path']
            
        if not permission.save():
            return jsonify({
                'success': False,
                'message': '更新权限失败'
            }), 500
            
        return jsonify({
            'success': True,
            'message': '更新权限成功',
            'data': permission.to_dict()
        })
    except Exception as e:
        logger.error(f"更新权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"更新权限失败: {str(e)}"
        }), 500

@permission_bp.route('/delete/<int:permission_id>', methods=['DELETE'])
@login_required
@permission_required('system:permission:delete')
def delete_permission(permission_id):
    """删除权限"""
    try:
        # 获取权限
        permission = Permission.get_by_id(permission_id)
        if not permission:
            return jsonify({
                'success': False,
                'message': '权限不存在'
            }), 404
            
        # 删除权限
        if not permission.delete():
            return jsonify({
                'success': False,
                'message': '删除权限失败，可能存在子权限'
            }), 500
            
        return jsonify({
            'success': True,
            'message': '删除权限成功'
        })
    except Exception as e:
        logger.error(f"删除权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"删除权限失败: {str(e)}"
        }), 500 