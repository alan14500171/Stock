#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import logging
import pymysql
from utils.db import get_db_connection
from utils.auth import login_required, permission_required

holder_bp = Blueprint('holder', __name__)

@holder_bp.route('/api/holders', methods=['GET'])
@login_required
@permission_required('system:holder:view')
def get_holders():
    """
    获取持有人列表
    """
    try:
        # 获取查询参数
        name = request.args.get('name', '')
        holder_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询语句
        query = """
        SELECT h.*, u.username, u.display_name as user_display_name
        FROM holders h
        LEFT JOIN users u ON h.user_id = u.id
        WHERE 1=1
        """
        params = []
        
        if name:
            query += " AND h.name LIKE %s"
            params.append(f"%{name}%")
        
        if holder_type:
            query += " AND h.type = %s"
            params.append(holder_type)
        
        if status:
            query += " AND h.status = %s"
            params.append(int(status))
        
        # 添加排序
        query += " ORDER BY h.id"
        
        # 执行查询
        cursor.execute(query, tuple(params))
        holders = cursor.fetchall()
        
        # 处理日期格式
        for holder in holders:
            if holder.get('created_at'):
                holder['created_at'] = holder['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if holder.get('updated_at'):
                holder['updated_at'] = holder['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'data': holders
        })
        
    except Exception as e:
        current_app.logger.error(f"获取持有人列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取持有人列表失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@holder_bp.route('/api/holders/<int:holder_id>', methods=['GET'])
@login_required
@permission_required('system:holder:view')
def get_holder(holder_id):
    """
    获取持有人详情
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询持有人
        query = """
        SELECT h.*, u.username, u.display_name as user_display_name
        FROM holders h
        LEFT JOIN users u ON h.user_id = u.id
        WHERE h.id = %s
        """
        cursor.execute(query, (holder_id,))
        holder = cursor.fetchone()
        
        if not holder:
            return jsonify({
                'success': False,
                'message': '持有人不存在'
            }), 404
        
        # 处理日期格式
        if holder.get('created_at'):
            holder['created_at'] = holder['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if holder.get('updated_at'):
            holder['updated_at'] = holder['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'data': holder
        })
        
    except Exception as e:
        current_app.logger.error(f"获取持有人详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取持有人详情失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@holder_bp.route('/api/holders', methods=['POST'])
@login_required
@permission_required('system:holder:add')
def add_holder():
    """
    添加持有人
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供数据'
            }), 400
        
        name = data.get('name')
        holder_type = data.get('type', 'individual')
        user_id = data.get('user_id')
        status = data.get('status', 1)
        
        if not name:
            return jsonify({
                'success': False,
                'message': '持有人姓名不能为空'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查名称是否已存在
        check_query = "SELECT COUNT(*) FROM holders WHERE name = %s"
        cursor.execute(check_query, (name,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            return jsonify({
                'success': False,
                'message': f'持有人 {name} 已存在'
            }), 400
        
        # 插入持有人
        insert_query = """
        INSERT INTO holders (name, type, user_id, status)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (name, holder_type, user_id if user_id else None, status))
        conn.commit()
        
        holder_id = cursor.lastrowid
        
        return jsonify({
            'success': True,
            'message': '添加持有人成功',
            'data': {
                'id': holder_id
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"添加持有人失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加持有人失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@holder_bp.route('/api/holders/<int:holder_id>', methods=['PUT'])
@login_required
@permission_required('system:holder:edit')
def update_holder(holder_id):
    """
    更新持有人
    """
    current_app.logger.info(f"开始处理更新持有人请求，holder_id={holder_id}")
    current_app.logger.info(f"请求头: {dict(request.headers)}")
    current_app.logger.info(f"请求方法: {request.method}")
    current_app.logger.info(f"请求URL: {request.url}")
    
    conn = None
    cursor = None
    try:
        data = request.get_json()
        current_app.logger.info(f"更新持有人请求数据: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供数据'
            }), 400
        
        name = data.get('name')
        holder_type = data.get('type')
        user_id = data.get('user_id')
        status = data.get('status')
        
        current_app.logger.info(f"解析后的数据: name={name}, type={holder_type}, user_id={user_id}, status={status}")
        
        if not name:
            return jsonify({
                'success': False,
                'message': '持有人姓名不能为空'
            }), 400
        
        # 尝试获取数据库连接
        current_app.logger.info(f"尝试获取数据库连接...")
        conn = get_db_connection()
        current_app.logger.info(f"数据库连接获取成功")
        
        cursor = conn.cursor()
        
        # 检查持有人是否存在
        current_app.logger.info(f"检查持有人ID {holder_id} 是否存在")
        check_query = "SELECT COUNT(*) FROM holders WHERE id = %s"
        cursor.execute(check_query, (holder_id,))
        count = cursor.fetchone()['COUNT(*)']
        current_app.logger.info(f"持有人存在检查结果: {count}")
        
        if count == 0:
            return jsonify({
                'success': False,
                'message': '持有人不存在'
            }), 404
        
        # 检查名称是否已被其他持有人使用
        current_app.logger.info(f"检查名称 {name} 是否已被其他持有人使用")
        check_name_query = "SELECT COUNT(*) FROM holders WHERE name = %s AND id != %s"
        cursor.execute(check_name_query, (name, holder_id))
        name_count = cursor.fetchone()['COUNT(*)']
        current_app.logger.info(f"名称重复检查结果: {name_count}")
        
        if name_count > 0:
            return jsonify({
                'success': False,
                'message': f'持有人名称 {name} 已被使用'
            }), 400
        
        # 更新持有人
        current_app.logger.info(f"开始更新持有人...")
        update_query = """
        UPDATE holders
        SET name = %s, type = %s, user_id = %s, status = %s
        WHERE id = %s
        """
        
        # 准备参数
        params = (
            name, 
            holder_type, 
            user_id if user_id else None, 
            status, 
            holder_id
        )
        current_app.logger.info(f"更新SQL参数: {params}")
        
        cursor.execute(update_query, params)
        current_app.logger.info(f"SQL执行完成，受影响行数: {cursor.rowcount}")
        
        conn.commit()
        current_app.logger.info(f"事务提交成功")
        
        return jsonify({
            'success': True,
            'message': '更新持有人成功'
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"更新持有人失败: {str(e)}\n{error_details}")
        
        # 如果连接已建立，尝试回滚事务
        if conn:
            try:
                conn.rollback()
                current_app.logger.info("事务已回滚")
            except Exception as rollback_error:
                current_app.logger.error(f"事务回滚失败: {str(rollback_error)}")
        
        return jsonify({
            'success': False,
            'message': f'更新持有人失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            try:
                cursor.close()
                current_app.logger.info("游标已关闭")
            except Exception as cursor_error:
                current_app.logger.error(f"关闭游标失败: {str(cursor_error)}")
        
        if conn:
            try:
                conn.close()
                current_app.logger.info("数据库连接已关闭")
            except Exception as conn_error:
                current_app.logger.error(f"关闭数据库连接失败: {str(conn_error)}")

@holder_bp.route('/api/holders/<int:holder_id>', methods=['DELETE'])
@login_required
@permission_required('system:holder:delete')
def delete_holder(holder_id):
    """
    删除持有人
    """
    current_app.logger.info(f"开始处理删除持有人请求，holder_id={holder_id}")
    current_app.logger.info(f"请求头: {dict(request.headers)}")
    current_app.logger.info(f"请求方法: {request.method}")
    current_app.logger.info(f"请求URL: {request.url}")
    
    conn = None
    cursor = None
    try:
        current_app.logger.info(f"准备删除持有人ID: {holder_id}")
        
        # 尝试获取数据库连接
        current_app.logger.info(f"尝试获取数据库连接...")
        conn = get_db_connection()
        current_app.logger.info(f"数据库连接获取成功")
        
        cursor = conn.cursor()
        
        # 检查持有人是否存在
        current_app.logger.info(f"检查持有人ID {holder_id} 是否存在")
        check_query = "SELECT COUNT(*) FROM holders WHERE id = %s"
        cursor.execute(check_query, (holder_id,))
        count = cursor.fetchone()['COUNT(*)']
        current_app.logger.info(f"持有人存在检查结果: {count}")
        
        if count == 0:
            return jsonify({
                'success': False,
                'message': '持有人不存在'
            }), 404
        
        # 检查持有人是否被交易分单引用
        current_app.logger.info(f"检查持有人ID {holder_id} 是否被交易分单引用")
        check_ref_query = "SELECT COUNT(*) FROM transaction_splits WHERE holder_id = %s"
        cursor.execute(check_ref_query, (holder_id,))
        ref_count = cursor.fetchone()['COUNT(*)']
        current_app.logger.info(f"交易分单引用检查结果: {ref_count}")
        
        if ref_count > 0:
            # 如果被引用，则只禁用而不删除
            current_app.logger.info(f"持有人已被引用，将禁用而非删除")
            update_query = "UPDATE holders SET status = 0 WHERE id = %s"
            cursor.execute(update_query, (holder_id,))
            current_app.logger.info(f"SQL执行完成，受影响行数: {cursor.rowcount}")
            
            conn.commit()
            current_app.logger.info(f"事务提交成功")
            
            return jsonify({
                'success': True,
                'message': '持有人已被交易记录引用，已禁用而非删除'
            })
        else:
            # 如果未被引用，则删除
            current_app.logger.info(f"持有人未被引用，将直接删除")
            delete_query = "DELETE FROM holders WHERE id = %s"
            cursor.execute(delete_query, (holder_id,))
            current_app.logger.info(f"SQL执行完成，受影响行数: {cursor.rowcount}")
            
            conn.commit()
            current_app.logger.info(f"事务提交成功")
            
            return jsonify({
                'success': True,
                'message': '删除持有人成功'
            })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"删除持有人失败: {str(e)}\n{error_details}")
        
        # 如果连接已建立，尝试回滚事务
        if conn:
            try:
                conn.rollback()
                current_app.logger.info("事务已回滚")
            except Exception as rollback_error:
                current_app.logger.error(f"事务回滚失败: {str(rollback_error)}")
        
        return jsonify({
            'success': False,
            'message': f'删除持有人失败: {str(e)}'
        }), 500
    finally:
        if cursor:
            try:
                cursor.close()
                current_app.logger.info("游标已关闭")
            except Exception as cursor_error:
                current_app.logger.error(f"关闭游标失败: {str(cursor_error)}")
        
        if conn:
            try:
                conn.close()
                current_app.logger.info("数据库连接已关闭")
            except Exception as conn_error:
                current_app.logger.error(f"关闭数据库连接失败: {str(conn_error)}")

def register_routes(app):
    """
    注册路由
    """
    app.register_blueprint(holder_bp) 