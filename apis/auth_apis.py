# encoding: utf-8
"""
认证API接口
"""
from flask import request, jsonify
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db_connection import get_db, UserModel
from auth.utils import (
    get_password_hash, verify_password, create_access_token,
    generate_verification_code, is_valid_email
)
from auth.email import send_verification_email


def register_api():
    """
    邮箱注册接口
    请求参数（JSON）:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "msg": "邮箱和密码不能为空",
                "data": None
            }), 400
        
        if not is_valid_email(email):
            return jsonify({
                "success": False,
                "msg": "邮箱格式不正确",
                "data": None
            }), 400
        
        if len(password) < 6:
            return jsonify({
                "success": False,
                "msg": "密码长度至少为6位",
                "data": None
            }), 400
        
        # 获取数据库会话
        db = next(get_db())
        
        # 检查邮箱是否已存在
        existing_user = db.query(UserModel).filter(UserModel.email == email).first()
        if existing_user:
            return jsonify({
                "success": False,
                "msg": "该邮箱已被注册",
                "data": None
            }), 400
        
        # 生成验证码
        code = generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        # 创建新用户
        print(f"密码长度: {len(password)}")
        print(f"密码: {password}")
        hashed_password = get_password_hash(password)
        print(f"哈希后密码长度: {len(hashed_password)}")
        new_user = UserModel(
            email=email,
            password_hash=hashed_password,
            verification_code=code,
            verification_expiry=expires_at
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 发送验证邮件
        from flask import current_app
        send_success = send_verification_email(email, code, is_test=current_app.testing)
        if not send_success:
            return jsonify({
                "success": False,
                "msg": "验证码发送失败，请稍后重试",
                "data": None
            }), 500
        
        return jsonify({
            "success": True,
            "msg": "注册成功，验证码已发送至您的邮箱",
            "data": {
                "email": email,
                "verification_expiry": expires_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"注册接口错误: {str(e)}")
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


def verify_email_api():
    """
    邮箱验证接口
    请求参数（JSON）:
    {
        "email": "user@example.com",
        "code": "123456"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({
                "success": False,
                "msg": "邮箱和验证码不能为空",
                "data": None
            }), 400
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找用户
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return jsonify({
                "success": False,
                "msg": "用户不存在",
                "data": None
            }), 404
        
        # 检查验证码
        if user.verification_code != code:
            return jsonify({
                "success": False,
                "msg": "验证码错误",
                "data": None
            }), 400
        
        # 检查验证码是否过期
        if user.verification_expiry and datetime.utcnow() > user.verification_expiry:
            return jsonify({
                "success": False,
                "msg": "验证码已过期",
                "data": None
            }), 400
        
        # 验证成功
        user.is_verified = True
        user.verification_code = None
        user.verification_expiry = None
        
        db.commit()
        
        return jsonify({
            "success": True,
            "msg": "邮箱验证成功",
            "data": {
                "email": email,
                "is_verified": True
            }
        }), 200
        
    except Exception as e:
        print(f"验证接口错误: {str(e)}")
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


def login_api():
    """
    邮箱登录接口
    请求参数（JSON）:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "msg": "邮箱和密码不能为空",
                "data": None
            }), 400
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找用户
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return jsonify({
                "success": False,
                "msg": "邮箱或密码错误",
                "data": None
            }), 401
        
        # 检查邮箱是否已验证
        if not user.is_verified:
            return jsonify({
                "success": False,
                "msg": "邮箱未验证，请先验证邮箱",
                "data": None
            }), 401
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return jsonify({
                "success": False,
                "msg": "邮箱或密码错误",
                "data": None
            }), 401
        
        # 创建访问令牌
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        return jsonify({
            "success": True,
            "msg": "登录成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email
                }
            }
        }), 200
        
    except Exception as e:
        print(f"登录接口错误: {str(e)}")
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


def request_reset_password_api():
    """
    请求重置密码接口
    请求参数（JSON）:
    {
        "email": "user@example.com"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        email = data.get('email')
        
        if not email:
            return jsonify({
                "success": False,
                "msg": "邮箱不能为空",
                "data": None
            }), 400
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找用户
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return jsonify({
                "success": False,
                "msg": "该邮箱未注册",
                "data": None
            }), 404
        
        # 生成重置令牌
        from auth.utils import generate_reset_token
        reset_token = generate_reset_token()
        reset_expiry = datetime.utcnow() + timedelta(hours=1)
        
        user.reset_token = reset_token
        user.reset_expiry = reset_expiry
        
        db.commit()
        
        # 生成重置链接
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}&email={email}"
        
        # 发送重置邮件
        from auth.email import send_password_reset_email
        send_success = send_password_reset_email(email, reset_link)
        if not send_success:
            return jsonify({
                "success": False,
                "msg": "重置邮件发送失败，请稍后重试",
                "data": None
            }), 500
        
        return jsonify({
            "success": True,
            "msg": "重置密码邮件已发送，请查收",
            "data": None
        }), 200
        
    except Exception as e:
        print(f"重置密码接口错误: {str(e)}")
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


def reset_password_api():
    """
    重置密码接口
    请求参数（JSON）:
    {
        "email": "user@example.com",
        "token": "reset_token",
        "new_password": "new_password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        email = data.get('email')
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not email or not token or not new_password:
            return jsonify({
                "success": False,
                "msg": "邮箱、令牌和新密码不能为空",
                "data": None
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                "success": False,
                "msg": "新密码长度至少为6位",
                "data": None
            }), 400
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找用户
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return jsonify({
                "success": False,
                "msg": "用户不存在",
                "data": None
            }), 404
        
        # 检查重置令牌
        if user.reset_token != token:
            return jsonify({
                "success": False,
                "msg": "无效的重置令牌",
                "data": None
            }), 400
        
        # 检查令牌是否过期
        if user.reset_expiry and datetime.utcnow() > user.reset_expiry:
            return jsonify({
                "success": False,
                "msg": "重置令牌已过期",
                "data": None
            }), 400
        
        # 更新密码
        hashed_password = get_password_hash(new_password)
        user.password_hash = hashed_password
        user.reset_token = None
        user.reset_expiry = None
        
        db.commit()
        
        return jsonify({
            "success": True,
            "msg": "密码重置成功",
            "data": None
        }), 200
        
    except Exception as e:
        print(f"重置密码接口错误: {str(e)}")
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500
