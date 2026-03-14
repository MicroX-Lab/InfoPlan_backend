# encoding: utf-8
"""用户认证服务"""
from flask_jwt_extended import create_access_token
from loguru import logger

from app.extensions import db
from app.models.user import User


class AuthService:

    @staticmethod
    def register(username: str, password: str, nickname: str = None) -> tuple[bool, str, dict | None]:
        """用户注册"""
        if not username or not password:
            return False, "用户名和密码不能为空", None

        if len(username) < 3 or len(username) > 50:
            return False, "用户名长度需在 3-50 字符之间", None

        if len(password) < 6:
            return False, "密码长度至少 6 位", None

        existing = User.query.filter_by(username=username).first()
        if existing:
            return False, "用户名已存在", None

        user = User(username=username, nickname=nickname or username)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"用户注册成功: {username}")
            return True, "注册成功", user.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"注册失败: {e}")
            return False, f"注册失败: {str(e)}", None

    @staticmethod
    def login(username: str, password: str) -> tuple[bool, str, dict | None]:
        """用户登录，返回 JWT"""
        if not username or not password:
            return False, "用户名和密码不能为空", None

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return False, "用户名或密码错误", None

        access_token = create_access_token(identity=str(user.id))
        logger.info(f"用户登录成功: {username}")
        return True, "登录成功", {
            "access_token": access_token,
            "user": user.to_dict(),
        }

    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:
        return User.query.get(user_id)
