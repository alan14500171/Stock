#!/usr/bin/env python
"""
权限检查脚本
用于检查权限是否已经整理完成
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

def check_permissions():
    """检查权限是否已经整理完成"""
    logger.info("开始检查权限结构...")
    
    # 获取所有权限
    permissions = Permission.get_all()
    logger.info(f"获取到 {len(permissions)} 个权限")
    
    # 检查权限类型
    type_counts = {1: 0, 2: 0, 3: 0}
    for p in permissions:
        if p.type in type_counts:
            type_counts[p.type] += 1
        else:
            logger.warning(f"权限 {p.code} 的类型 {p.type} 不在预期范围内")
    
    logger.info(f"权限类型统计: 模块({type_counts[1]}), 菜单({type_counts[2]}), 按钮({type_counts[3]})")
    
    # 检查权限路径
    path_issues = []
    for p in permissions:
        # 检查路径是否为空
        if not p.path:
            path_issues.append(f"权限 {p.code} 的路径为空")
            continue
        
        # 检查路径是否与父子关系一致
        path_parts = p.path.split('/')
        if len(path_parts) == 1:
            # 顶级权限
            if p.parent_id is not None:
                path_issues.append(f"权限 {p.code} 的路径 {p.path} 表明它是顶级权限，但它有父ID {p.parent_id}")
        else:
            # 子权限
            parent_id_in_path = int(path_parts[-2]) if len(path_parts) > 1 else None
            if p.parent_id != parent_id_in_path:
                path_issues.append(f"权限 {p.code} 的路径 {p.path} 与其父ID {p.parent_id} 不一致")
    
    if path_issues:
        logger.warning("发现路径问题:")
        for issue in path_issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("所有权限路径检查通过")
    
    # 检查权限代码格式
    code_issues = []
    for p in permissions:
        parts = p.code.split(':')
        if len(parts) < 1 or len(parts) > 3:
            code_issues.append(f"权限 {p.code} 的代码格式不符合预期 (模块:菜单:操作)")
        
        # 检查类型与代码格式是否一致
        if len(parts) == 1 and p.type != 1:
            code_issues.append(f"权限 {p.code} 的代码格式表明它是模块，但类型是 {p.type}")
        elif len(parts) == 2 and p.type != 2:
            code_issues.append(f"权限 {p.code} 的代码格式表明它是菜单，但类型是 {p.type}")
        elif len(parts) == 3 and p.type != 3:
            code_issues.append(f"权限 {p.code} 的代码格式表明它是按钮，但类型是 {p.type}")
    
    if code_issues:
        logger.warning("发现代码格式问题:")
        for issue in code_issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("所有权限代码格式检查通过")
    
    # 检查父子关系
    parent_issues = []
    for p in permissions:
        if p.parent_id:
            parent = next((x for x in permissions if x.id == p.parent_id), None)
            if not parent:
                parent_issues.append(f"权限 {p.code} 的父ID {p.parent_id} 不存在")
                continue
            
            # 检查父子类型关系
            if p.type <= parent.type:
                parent_issues.append(f"权限 {p.code} (类型 {p.type}) 的父权限 {parent.code} (类型 {parent.type}) 类型关系不正确")
            
            # 检查代码前缀
            if not p.code.startswith(parent.code + ':'):
                parent_issues.append(f"权限 {p.code} 的代码前缀与其父权限 {parent.code} 不一致")
    
    if parent_issues:
        logger.warning("发现父子关系问题:")
        for issue in parent_issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("所有权限父子关系检查通过")
    
    # 总结
    if not path_issues and not code_issues and not parent_issues:
        logger.info("恭喜！所有权限检查通过，权限结构已经整理完成")
        return True
    else:
        logger.warning(f"权限检查发现问题: {len(path_issues)} 个路径问题, {len(code_issues)} 个代码格式问题, {len(parent_issues)} 个父子关系问题")
        return False

if __name__ == '__main__':
    check_permissions() 