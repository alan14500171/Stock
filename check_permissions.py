import sys
sys.path.append('/Users/par/Desktop/Cursor/stock/backend')

from config.database import db

# 查询用户lili的信息
print('用户lili的信息:')
user = db.fetch_one('SELECT * FROM users WHERE username = %s', ['lili'])
print(user)

# 查询用户lili的角色
print('\n用户lili的角色:')
roles = db.fetch_all('SELECT r.* FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = %s', [user['id']])
print(roles)

# 查询角色的权限
print('\n角色的权限:')
for role in roles:
    perms = db.fetch_all('SELECT p.* FROM permissions p JOIN role_permissions rp ON p.id = rp.permission_id WHERE rp.role_id = %s', [role['id']])
    print(f'角色 {role["name"]} 的权限:')
    for p in perms:
        print(f'  - {p["name"]} ({p["code"]})')

# 特别检查profit:stats:view权限
print('\n特别检查profit:stats:view权限:')
profit_perm = db.fetch_one('SELECT * FROM permissions WHERE code = %s', ['profit:stats:view'])
print(f'权限存在: {profit_perm is not None}')
if profit_perm:
    # 检查角色是否有此权限
    for role in roles:
        has_perm = db.fetch_one('SELECT * FROM role_permissions WHERE role_id = %s AND permission_id = %s', [role['id'], profit_perm['id']])
        print(f'角色 {role["name"]} 是否有profit:stats:view权限: {has_perm is not None}') 