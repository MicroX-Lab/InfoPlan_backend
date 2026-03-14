# encoding: utf-8
"""统一配置"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # SQLite (WAL 模式)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URI", "sqlite:///infoplan.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "pool_pre_ping": True,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # XHS
    COOKIES = os.getenv("COOKIES", "")

    # 沐曦 GPU 模型服务
    MUXI_API_BASE = os.getenv("MUXI_API_BASE", "http://localhost")
    LLM_HEAVY_PORT = int(os.getenv("LLM_HEAVY_PORT", "8000"))  # Qwen3-8B
    LLM_LIGHT_PORT = int(os.getenv("LLM_LIGHT_PORT", "8001"))  # Qwen3-4B
    LLM_VISION_PORT = int(os.getenv("LLM_VISION_PORT", "8002"))  # Qwen3-VL-8B


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
