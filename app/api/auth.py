# encoding: utf-8
"""认证模块 API: /api/auth/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")
    nickname = data.get("nickname", "").strip() or None

    success, msg, result = AuthService.register(username, password, nickname)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 201
    return jsonify({"success": False, "msg": msg}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录，返回 JWT"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    success, msg, result = AuthService.login(username, password)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 200
    return jsonify({"success": False, "msg": msg}), 401


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "msg": "用户不存在"}), 404
    return jsonify({"success": True, "data": user.to_dict()}), 200
