import pymysql
from pymysql.cursors import DictCursor

def test_user_access():
    """测试用户访问权限"""
    try:
        # 数据库连接配置
        conn = pymysql.connect(
            host='118.101.108.48',
            user='root',
            password='Zxc000123',
            database='stock',
            port=3306,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        cursor = conn.cursor()
        
        # 1. 检查用户信息
        user_sql = """
            SELECT id, username, display_name, is_active 
            FROM users 
            WHERE username = 'lili'
        """
        cursor.execute(user_sql)
        user = cursor.fetchone()
        print("\n用户信息:")
        print(user)
        
        if user:
            user_id = user['id']
            
            # 2. 检查持有人信息
            holders_sql = """
                SELECT id, name, user_id, status 
                FROM holders 
                WHERE user_id = %s OR name = 'lili'
            """
            cursor.execute(holders_sql, [user_id])
            holders = cursor.fetchall()
            print("\n持有人信息:")
            print(holders)
            
            # 3. 检查分单记录
            splits_sql = """
                SELECT ts.*, h.name as holder_name, h.user_id as holder_user_id,
                       st.transaction_code, st.user_id as transaction_user_id
                FROM transaction_splits ts
                JOIN holders h ON ts.holder_id = h.id
                JOIN stock_transactions st ON ts.original_transaction_id = st.id
                WHERE h.user_id = %s
            """
            cursor.execute(splits_sql, [user_id])
            splits = cursor.fetchall()
            print("\n分单记录:")
            print(splits)
            
            # 4. 检查特定交易记录的访问权限
            transaction_code = 'P-892469'  # 这是你提到的交易编号
            auth_check_sql = """
                SELECT DISTINCT st.id, st.transaction_code, st.user_id
                FROM stock_transactions st
                LEFT JOIN transaction_splits ts ON st.id = ts.original_transaction_id
                LEFT JOIN holders h ON ts.holder_id = h.id
                WHERE st.transaction_code = %s 
                AND (st.user_id = %s OR h.user_id = %s)
            """
            cursor.execute(auth_check_sql, [transaction_code, user_id, user_id])
            auth_result = cursor.fetchone()
            print("\n交易记录访问权限检查:")
            print(auth_result)
            
        else:
            print("未找到用户 lili")
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    test_user_access() 