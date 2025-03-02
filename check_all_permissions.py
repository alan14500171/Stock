import sys
sys.path.append('/Users/par/Desktop/Cursor/stock/backend')

from config.database import db

# 查询所有权限
print('所有权限:')
permissions = db.fetch_all('SELECT * FROM permissions ORDER BY id')
for p in permissions:
    print(f"{p['id']} - {p['name']} ({p['code']})")

# 特别检查profit:stats:view权限
print('\n特别检查profit:stats:view权限:')
profit_perm = db.fetch_one('SELECT * FROM permissions WHERE code = %s', ['profit:stats:view'])
if profit_perm:
    print(f"找到权限: {profit_perm['id']} - {profit_perm['name']} ({profit_perm['code']})")
else:
    print("未找到profit:stats:view权限") 