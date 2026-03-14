# encoding: utf-8
"""Flask App Factory"""
import os

from flask import Flask
from flask_cors import CORS

from app.config import config_map
from app.extensions import db, jwt


def create_app(config_name=None):
    """创建 Flask 应用"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__, static_folder="../static")
    app.config.from_object(config_map[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # 启用 SQLite WAL 模式
    @app.after_request
    def after_request(response):
        return response

    with app.app_context():
        _register_blueprints(app)
        _enable_wal_mode(app)

    return app


def _register_blueprints(app):
    """注册所有 Blueprint"""
    from app.api import register_blueprints
    register_blueprints(app)


def _enable_wal_mode(app):
    """启用 SQLite WAL 模式提升并发性能"""
    if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        from sqlalchemy import event, text

        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
