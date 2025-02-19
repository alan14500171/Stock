import requests
import json

BASE_URL = 'http://localhost:9099'

def test_api():
    # 创建会话对象
    session = requests.Session()
    
    # 先进行注册
    print("\n尝试注册新用户:")
    register_data = {
        'username': 'testuser',
        'password': 'testpass'
    }
    response = session.post(f'{BASE_URL}/auth/register', data=register_data)
    print(f"Register Status Code: {response.status_code}")
    print(f"Register Headers: {dict(response.headers)}")
    print(f"Register Cookies: {dict(session.cookies)}")
    try:
        print(f"Register Response: {json.dumps(response.json() if response.status_code == 200 else response.text, indent=2, ensure_ascii=False)}")
    except:
        print(f"Register Raw Response: {response.text}")
    
    # 进行登录
    print("\n尝试登录:")
    login_data = {
        'username': 'testuser',
        'password': 'testpass'
    }
    response = session.post(f'{BASE_URL}/auth/login', data=login_data)
    print(f"Login Status Code: {response.status_code}")
    print(f"Login Headers: {dict(response.headers)}")
    print(f"Login Cookies: {dict(session.cookies)}")
    try:
        print(f"Login Response: {json.dumps(response.json() if response.status_code == 200 else response.text, indent=2, ensure_ascii=False)}")
    except:
        print(f"Login Raw Response: {response.text}")
    
    # 测试获取盈利统计数据
    print("\n测试获取盈利统计数据:")
    response = session.get(f'{BASE_URL}/api/profit')
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Cookies: {dict(session.cookies)}")
    try:
        print(f"Response: {json.dumps(response.json() if response.status_code == 200 else response.text, indent=2, ensure_ascii=False)}")
    except:
        print(f"Raw Response: {response.text}")

    # 测试获取市值数据
    print("\n测试获取市值数据:")
    response = session.get(f'{BASE_URL}/api/portfolio/market-value')
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Cookies: {dict(session.cookies)}")
    try:
        print(f"Response: {json.dumps(response.json() if response.status_code == 200 else response.text, indent=2, ensure_ascii=False)}")
    except:
        print(f"Raw Response: {response.text}")

    # 测试获取交易记录
    print("\n测试获取交易记录:")
    response = session.get(f'{BASE_URL}/api/transactions')
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Cookies: {dict(session.cookies)}")
    try:
        print(f"Response: {json.dumps(response.json() if response.status_code == 200 else response.text, indent=2, ensure_ascii=False)}")
    except:
        print(f"Raw Response: {response.text}")

if __name__ == '__main__':
    test_api() 