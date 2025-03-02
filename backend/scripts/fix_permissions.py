#!/usr/bin/env python
"""
权限整理脚本
用于修复权限结构、路径和父子关系
"""
import sys
import os
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Permission

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_permission_paths():
    """修复权限路径和父子关系"""
    logger.info("开始修复权限结构...")
    
    # 获取所有权限
    permissions = Permission.get_all()
    logger.info(f"获取到 {len(permissions)} 个权限")
    
    # 创建权限代码到权限对象的映射
    perm_map = {p.code: p for p in permissions}
    
    # 定义权限结构
    # 格式: {权限代码: {父权限代码, 类型}}
    # 类型: 1=模块, 2=菜单, 3=按钮
    permission_structure = {
        # 股票管理模块
        'stock': {'parent': None, 'type': 1},
        'stock:list': {'parent': 'stock', 'type': 2},
        'stock:list:view': {'parent': 'stock:list', 'type': 3},
        'stock:list:add': {'parent': 'stock:list', 'type': 3},
        'stock:list:edit': {'parent': 'stock:list', 'type': 3},
        'stock:list:delete': {'parent': 'stock:list', 'type': 3},
        'stock:holdings': {'parent': 'stock', 'type': 2},
        'stock:holdings:view': {'parent': 'stock:holdings', 'type': 3},
        'stock:holdings:export': {'parent': 'stock:holdings', 'type': 3},
        
        # 交易管理模块
        'transaction': {'parent': None, 'type': 1},
        'transaction:records': {'parent': 'transaction', 'type': 2},
        'transaction:records:view': {'parent': 'transaction:records', 'type': 3},
        'transaction:records:add': {'parent': 'transaction:records', 'type': 3},
        'transaction:records:edit': {'parent': 'transaction:records', 'type': 3},
        'transaction:records:delete': {'parent': 'transaction:records', 'type': 3},
        'transaction:records:export': {'parent': 'transaction:records', 'type': 3},
        'transaction:stats': {'parent': 'transaction', 'type': 2},
        'transaction:stats:view': {'parent': 'transaction:stats', 'type': 3},
        'transaction:stats:export': {'parent': 'transaction:stats', 'type': 3},
        'transaction:split': {'parent': 'transaction', 'type': 2},
        'transaction:split:view': {'parent': 'transaction:split', 'type': 3},
        'transaction:split:add': {'parent': 'transaction:split', 'type': 3},
        'transaction:split:edit': {'parent': 'transaction:split', 'type': 3},
        'transaction:split:delete': {'parent': 'transaction:split', 'type': 3},
        
        # 收益统计模块
        'profit': {'parent': None, 'type': 1},
        'profit:overview': {'parent': 'profit', 'type': 2},
        'profit:overview:view': {'parent': 'profit:overview', 'type': 3},
        'profit:overview:export': {'parent': 'profit:overview', 'type': 3},
        'profit:details': {'parent': 'profit', 'type': 2},
        'profit:details:view': {'parent': 'profit:details', 'type': 3},
        'profit:details:export': {'parent': 'profit:details', 'type': 3},
        'profit:stats': {'parent': 'profit', 'type': 2},
        'profit:stats:view': {'parent': 'profit:stats', 'type': 3},
        
        # 汇率管理模块
        'exchange': {'parent': None, 'type': 1},
        'exchange:rates': {'parent': 'exchange', 'type': 2},
        'exchange:rates:view': {'parent': 'exchange:rates', 'type': 3},
        'exchange:rates:add': {'parent': 'exchange:rates', 'type': 3},
        'exchange:rates:edit': {'parent': 'exchange:rates', 'type': 3},
        'exchange:rates:delete': {'parent': 'exchange:rates', 'type': 3},
        'exchange:converter': {'parent': 'exchange', 'type': 2},
        'exchange:converter:use': {'parent': 'exchange:converter', 'type': 3},
        
        # 系统管理模块
        'system': {'parent': None, 'type': 1},
        'system:user': {'parent': 'system', 'type': 2},
        'system:user:view': {'parent': 'system:user', 'type': 3},
        'system:user:add': {'parent': 'system:user', 'type': 3},
        'system:user:edit': {'parent': 'system:user', 'type': 3},
        'system:user:delete': {'parent': 'system:user', 'type': 3},
        'system:user:assign': {'parent': 'system:user', 'type': 3},
        'system:role': {'parent': 'system', 'type': 2},
        'system:role:view': {'parent': 'system:role', 'type': 3},
        'system:role:add': {'parent': 'system:role', 'type': 3},
        'system:role:edit': {'parent': 'system:role', 'type': 3},
        'system:role:delete': {'parent': 'system:role', 'type': 3},
        'system:role:assign': {'parent': 'system:role', 'type': 3},
        'system:permission': {'parent': 'system', 'type': 2},
        'system:permission:view': {'parent': 'system:permission', 'type': 3},
        'system:permission:add': {'parent': 'system:permission', 'type': 3},
        'system:permission:edit': {'parent': 'system:permission', 'type': 3},
        'system:permission:delete': {'parent': 'system:permission', 'type': 3},
        'system:settings': {'parent': 'system', 'type': 2},
        'system:settings:view': {'parent': 'system:settings', 'type': 3},
        'system:settings:edit': {'parent': 'system:settings', 'type': 3},
        'system:holder': {'parent': 'system', 'type': 2},
        'system:holder:view': {'parent': 'system:holder', 'type': 3},
        'system:holder:add': {'parent': 'system:holder', 'type': 3},
        'system:holder:edit': {'parent': 'system:holder', 'type': 3},
        'system:holder:delete': {'parent': 'system:holder', 'type': 3},
    }
    
    # 检查是否有未定义的权限
    for p in permissions:
        if p.code not in permission_structure:
            logger.warning(f"权限 {p.code} 未在结构定义中，将保持不变")
    
    # 更新权限
    updated_count = 0
    for code, config in permission_structure.items():
        if code in perm_map:
            perm = perm_map[code]
            parent_code = config['parent']
            perm_type = config['type']
            
            # 获取父权限ID
            parent_id = None
            if parent_code and parent_code in perm_map:
                parent_id = perm_map[parent_code].id
            
            # 检查是否需要更新
            if perm.parent_id != parent_id or perm.type != perm_type:
                logger.info(f"更新权限 {code}: 父ID {perm.parent_id} -> {parent_id}, 类型 {perm.type} -> {perm_type}")
                perm.parent_id = parent_id
                perm.type = perm_type
                if perm.save():
                    updated_count += 1
                else:
                    logger.error(f"更新权限 {code} 失败")
        else:
            logger.warning(f"权限 {code} 不存在，需要创建")
            # 创建新权限
            parent_id = None
            if config['parent'] and config['parent'] in perm_map:
                parent_id = perm_map[config['parent']].id
            
            # 创建权限名称
            name_parts = code.split(':')
            name = name_parts[-1].capitalize()
            if name == 'View':
                name = '查看' + name_parts[-2].capitalize()
            elif name == 'Add':
                name = '添加' + name_parts[-2].capitalize()
            elif name == 'Edit':
                name = '编辑' + name_parts[-2].capitalize()
            elif name == 'Delete':
                name = '删除' + name_parts[-2].capitalize()
            elif name == 'Export':
                name = '导出' + name_parts[-2].capitalize()
            elif name == 'Assign':
                name = '分配' + name_parts[-2].capitalize()
            elif name == 'Use':
                name = '使用' + name_parts[-2].capitalize()
            
            # 创建新权限
            new_perm = Permission({
                'name': name,
                'code': code,
                'description': f'权限: {code}',
                'type': config['type'],
                'parent_id': parent_id,
                'level': 0,
                'sort_order': 0,
                'is_menu': 0
            })
            
            if new_perm.save():
                logger.info(f"创建权限成功: {code}")
                perm_map[code] = new_perm
                updated_count += 1
            else:
                logger.error(f"创建权限失败: {code}")
    
    logger.info(f"权限更新完成，共更新 {updated_count} 个权限")
    
    # 更新所有权限的路径
    logger.info("开始更新权限路径...")
    permissions = Permission.get_all()
    path_updated_count = 0
    
    for perm in permissions:
        # 构建路径
        path_parts = []
        current = perm
        
        while current:
            path_parts.insert(0, str(current.id))
            if current.parent_id:
                parent = next((p for p in permissions if p.id == current.parent_id), None)
                current = parent
            else:
                current = None
        
        new_path = '/'.join(path_parts)
        
        # 检查是否需要更新路径
        if perm.path != new_path:
            logger.info(f"更新权限 {perm.code} 的路径: {perm.path} -> {new_path}")
            perm.path = new_path
            if perm.save():
                path_updated_count += 1
            else:
                logger.error(f"更新权限 {perm.code} 的路径失败")
    
    logger.info(f"路径更新完成，共更新 {path_updated_count} 个权限路径")

if __name__ == '__main__':
    fix_permission_paths() 