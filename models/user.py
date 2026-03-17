# encoding: utf-8
"""
用户数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime


class User:
    """用户模型基类"""
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6))
    verification_expiry = Column(DateTime)
    reset_token = Column(String(255))
    reset_expiry = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# 导入数据库连接实例时使用
# from db_connection import Base
# 
# class UserModel(Base, User):
#     __tablename__ = 'users'
