# encoding: utf-8
"""Flask App Factory"""
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from loguru import logger
from werkzeug.exceptions import HTTPException

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

    # Swagger / OpenAPI 文档
    Swagger(app, template={
        "info": {
            "title": "InfoPlan Backend API",
            "description": "InfoPlan 后端接口文档 —— 小红书信息流学习助手",
            "version": "1.0.0",
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT 认证，格式: Bearer <token>",
            }
        },
    })

    # 全局错误处理
    _register_error_handlers(app)

    with app.app_context():
        _register_blueprints(app)
        _enable_wal_mode(app)
        db.create_all()

    return app


def _register_error_handlers(app):
    """全局错误处理"""

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify({"success": False, "msg": e.description}), e.code

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "msg": "请求参数错误"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "msg": "资源不存在"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "msg": "请求方法不允许"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"内部服务器错误: {e}", exc_info=True)
        return jsonify({"success": False, "msg": "服务器内部错误"}), 500

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "msg": "登录已过期，请重新登录"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "msg": "无效的认证令牌"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "msg": "请先登录"}), 401


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
