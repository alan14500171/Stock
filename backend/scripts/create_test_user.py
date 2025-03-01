"""
创建测试用户脚本
"""
from models.user import User
from config.database import db

def create_test_user():
    try:
        # 检查用户是否已存在
        existing_user = User.find_by_username('alan')
        if existing_user:
            print("更新已存在用户的密码...")
            existing_user.set_password('123123')
            if existing_user.save():
                print("密码更新成功！")
                print(f"用户名: {existing_user.username}")
                print(f"密码: 123123")
            else:
                print("密码更新失败！")
        else:
            # 创建新用户
            user = User()
            user.username = 'alan'
            user.set_password('123123')
            if user.save():
                print("测试用户创建成功！")
                print(f"用户名: {user.username}")
                print(f"密码: 123123")
            else:
                print("测试用户创建失败！")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == '__main__':
    create_test_user() 