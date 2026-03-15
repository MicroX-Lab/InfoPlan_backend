# encoding: utf-8
"""认证模块 API: /api/auth/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册
    ---
    tags:
      - 认证
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: 用户名
              example: "testuser"
            password:
              type: string
              description: 密码
              example: "123456"
            nickname:
              type: string
              description: 昵称（可选）
              example: "小明"
    responses:
      201:
        description: 注册成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            msg:
              type: string
            data:
              type: object
              properties:
                access_token:
                  type: string
                user:
                  type: object
      400:
        description: 参数错误或用户名已存在
    """
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
    """用户登录，返回 JWT
    ---
    tags:
      - 认证
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: "testuser"
            password:
              type: string
              example: "123456"
    responses:
      200:
        description: 登录成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            msg:
              type: string
            data:
              type: object
              properties:
                access_token:
                  type: string
                user:
                  type: object
      401:
        description: 用户名或密码错误
    """
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
    """获取当前用户信息
    ---
    tags:
      - 认证
    security:
      - Bearer: []
    responses:
      200:
        description: 成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                nickname:
                  type: string
      401:
        description: 未认证
      404:
        description: 用户不存在
    """
    user_id = int(get_jwt_identity())
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "msg": "用户不存在"}), 404
    return jsonify({"success": True, "data": user.to_dict()}), 200
