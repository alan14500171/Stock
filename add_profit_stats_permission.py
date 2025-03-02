import sys
sys.path.append('/Users/par/Desktop/Cursor/stock/backend')

from config.database import db

# 添加profit:stats:view权限
print('添加profit:stats:view权限')
profit_parent = db.fetch_one('SELECT * FROM permissions WHERE code = %s', ['profit'])
if not profit_parent:
    print('未找到profit父权限，无法添加')
    sys.exit(1)

# 检查是否已存在profit:stats模块
profit_stats = db.fetch_one('SELECT * FROM permissions WHERE code = %s', ['profit:stats'])
if not profit_stats:
    # 添加profit:stats模块
    print('添加profit:stats模块')
    insert_sql = """
    INSERT INTO permissions (name, code, description, type, parent_id, path, level, sort_order, is_menu)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    # 查看permissions表的type字段类型
    type_info = db.fetch_one("SHOW COLUMNS FROM permissions WHERE Field = 'type'")
    print(f"type字段信息: {type_info}")
    
    # 使用数字类型
    profit_stats_id = db.insert(insert_sql, [
        '收益统计', 'profit:stats', '收益统计模块', 1, 
        profit_parent['id'], f"{profit_parent['path']}/{profit_parent['id']}", profit_parent['level'] + 1, 
        27, 0
    ])
    print(f'添加profit:stats模块成功，ID: {profit_stats_id}')
    profit_stats = db.fetch_one('SELECT * FROM permissions WHERE id = %s', [profit_stats_id])
    if not profit_stats:
        print('无法获取新添加的profit:stats模块')
        sys.exit(1)
else:
    print(f'profit:stats模块已存在，ID: {profit_stats["id"]}')

# 检查是否已存在profit:stats:view权限
profit_stats_view = db.fetch_one('SELECT * FROM permissions WHERE code = %s', ['profit:stats:view'])
if not profit_stats_view:
    # 添加profit:stats:view权限
    print('添加profit:stats:view权限')
    insert_sql = """
    INSERT INTO permissions (name, code, description, type, parent_id, path, level, sort_order, is_menu)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    profit_stats_view_id = db.insert(insert_sql, [
        '查看收益统计', 'profit:stats:view', '查看收益统计权限', 2, 
        profit_stats['id'], f"{profit_stats['path']}/{profit_stats['id']}", profit_stats['level'] + 1, 
        28, 0
    ])
    print(f'添加profit:stats:view权限成功，ID: {profit_stats_view_id}')
    
    # 分配给user角色
    user_role = db.fetch_one('SELECT * FROM roles WHERE name = %s', ['user'])
    if user_role:
        # 检查是否已分配
        existing = db.fetch_one('SELECT * FROM role_permissions WHERE role_id = %s AND permission_id = %s', 
                               [user_role['id'], profit_stats_view_id])
        if not existing:
            # 分配权限
            db.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)', 
                      [user_role['id'], profit_stats_view_id])
            print(f'已将profit:stats:view权限分配给user角色')
        else:
            print('user角色已有此权限')
    else:
        print('未找到user角色')
else:
    print(f'profit:stats:view权限已存在，ID: {profit_stats_view["id"]}')
    
    # 检查user角色是否有此权限
    user_role = db.fetch_one('SELECT * FROM roles WHERE name = %s', ['user'])
    if user_role:
        existing = db.fetch_one('SELECT * FROM role_permissions WHERE role_id = %s AND permission_id = %s', 
                               [user_role['id'], profit_stats_view['id']])
        if not existing:
            # 分配权限
            db.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)', 
                      [user_role['id'], profit_stats_view['id']])
            print(f'已将profit:stats:view权限分配给user角色')
        else:
            print('user角色已有此权限')
    else:
        print('未找到user角色') 