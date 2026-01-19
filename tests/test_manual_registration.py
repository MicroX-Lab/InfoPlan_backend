# encoding: utf-8
"""
手动用户注册测试脚本
测试邮箱：1165699654@qq.com
"""
import json
import sys
import os
import pymysql

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app
from db_config import DB_CONFIG


def test_manual_registration():
    """手动用户注册测试"""
    print("=== InfoPlan 用户注册测试 ===")
    print(f"测试邮箱: 1165699654@qq.com")
    print("=" * 40)
    
    # 初始化测试客户端
    test_client = app.test_client()
    app.testing = False  # 设置为 False 以实际发送邮件
    
    # 测试邮箱和密码
    test_email = "1165699654@qq.com"
    test_password = "tps11600"
    
    # 先删除已存在的用户（如果有）
    print("\n0. 检查并删除已存在的用户...")
    from db_connection import get_db, UserModel
    db = next(get_db())
    existing_user = db.query(UserModel).filter(UserModel.email == test_email).first()
    if existing_user:
        print(f"删除已存在的用户: {test_email}")
        db.delete(existing_user)
        db.commit()
        print("用户删除成功")
    else:
        print("用户不存在，无需删除")
    
    # 1. 发送注册请求
    print("\n1. 发送注册请求...")
    response = test_client.post(
        '/api/auth/register',
        data=json.dumps({
            "email": test_email,
            "password": test_password
        }),
        content_type='application/json'
    )
    
    # 检查响应
    data = json.loads(response.get_data(as_text=True))
    print(f"响应状态码: {response.status_code}")
    print(f"响应消息: {data['msg']}")
    
    if not data['success']:
        print("注册请求失败，退出测试")
        return False
    
    print("✅ 注册请求成功，验证码已发送")
    print(f"验证码有效期: 30分钟")
    
    # 从数据库获取验证码（测试用）
    db = next(get_db())
    user = db.query(UserModel).filter(UserModel.email == test_email).first()
    if user:
        verification_code = user.verification_code
        print(f"[测试模式] 自动使用验证码: {verification_code}")
    else:
        print("未找到用户，退出测试")
        return False
    
    # 3. 发送验证请求
    print("\n3. 发送验证请求...")
    verify_response = test_client.post(
        '/api/auth/verify-email',
        data=json.dumps({
            "email": test_email,
            "code": verification_code
        }),
        content_type='application/json'
    )
    
    # 检查验证响应
    verify_data = json.loads(verify_response.get_data(as_text=True))
    print(f"响应状态码: {verify_response.status_code}")
    print(f"响应消息: {verify_data['msg']}")
    
    if not verify_data['success']:
        print("邮箱验证失败，退出测试")
        return False
    
    print("✅ 邮箱验证成功")
    
    # 4. 测试登录
    print("\n4. 测试登录...")
    login_response = test_client.post(
        '/api/auth/login',
        data=json.dumps({
            "email": test_email,
            "password": test_password
        }),
        content_type='application/json'
    )
    
    # 检查登录响应
    login_data = json.loads(login_response.get_data(as_text=True))
    print(f"响应状态码: {login_response.status_code}")
    print(f"响应消息: {login_data['msg']}")
    
    if not login_data['success']:
        print("登录失败，退出测试")
        return False
    
    print("✅ 登录成功")
    print(f"访问令牌: {login_data['data']['access_token'][:50]}...")
    
    # 5. 显示数据库表结构
    print("\n5. 显示用户表结构和数据...")
    show_user_table()
    
    print("\n" + "=" * 40)
    print("🎉 测试完成！用户注册流程成功")
    print("=" * 40)
    return True


def show_user_table():
    """显示用户表结构和数据"""
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset']
        )
        cursor = conn.cursor()
        
        # 显示表结构
        print("\n用户表结构:")
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  {column[0]} ({column[1]}) - {column[2]}")
        
        # 显示表数据
        print("\n用户表数据:")
        cursor.execute("SELECT id, email, is_verified, created_at FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("  无用户数据")
        else:
            print("  ID | 邮箱 | 已验证 | 创建时间")
            print("  " + "-" * 60)
            for user in users:
                is_verified = "✓" if user[2] else "✗"
                print(f"  {user[0]} | {user[1]} | {is_verified} | {user[3]}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"显示表结构失败: {str(e)}")


if __name__ == '__main__':
    test_manual_registration()
