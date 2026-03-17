# encoding: utf-8
"""
认证工具函数
"""
import random
import string
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from db_config import JWT_CONFIG


# 密码加密上下文 - 使用 pbkdf2_sha256 代替 bcrypt 以避免库 bug
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希值
    """
    try:
        hashed = pwd_context.hash(password)
        return hashed
    except Exception as e:
        print(f"哈希生成失败: {str(e)}")
        # 尝试使用更简单的方式
        import hashlib
        try:
            # 使用简单的 SHA-256 哈希（仅用于测试）
            hashed = hashlib.sha256(password.encode()).hexdigest()
            print("使用 SHA-256 哈希成功")
            return f"sha256${hashed}"
        except Exception as e2:
            print(f"使用 SHA-256 哈希失败: {str(e2)}")
            raise


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    创建访问令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_CONFIG['ACCESS_TOKEN_EXPIRE_MINUTES'])
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_CONFIG['SECRET_KEY'], algorithm=JWT_CONFIG['ALGORITHM'])
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    解码令牌
    """
    try:
        payload = jwt.decode(token, JWT_CONFIG['SECRET_KEY'], algorithms=[JWT_CONFIG['ALGORITHM']])
        return payload
    except JWTError:
        return None


def generate_verification_code(length: int = 6) -> str:
    """
    生成验证码
    """
    digits = string.digits
    return ''.join(random.choice(digits) for _ in range(length))


def generate_reset_token() -> str:
    """
    生成重置密码令牌
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(32))


def is_valid_email(email: str) -> bool:
    """
    验证邮箱格式
    """
    import re
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email))
