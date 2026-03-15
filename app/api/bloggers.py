# encoding: utf-8
"""博主管理 API: /api/bloggers/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.content_pool_service import ContentPoolService

bloggers_bp = Blueprint("bloggers", __name__)


@bloggers_bp.route("/search", methods=["POST"])
@jwt_required()
def search_blogger():
    """搜索小红书博主
    ---
    tags:
      - 博主
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - query
          properties:
            query:
              type: string
              description: 搜索关键词
              example: "美食博主"
            page:
              type: integer
              description: 页码
              default: 1
    responses:
      200:
        description: 搜索结果
        schema:
          type: object
          properties:
            success:
              type: boolean
            msg:
              type: string
            data:
              type: object
      400:
        description: 参数缺失
      500:
        description: 搜索失败
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "msg": "query 参数不能为空"}), 400

    page = data.get("page", 1)
    success, msg, result = ContentPoolService.search_blogger(query, page)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 200
    return jsonify({"success": False, "msg": msg}), 500


@bloggers_bp.route("", methods=["POST"])
@jwt_required()
def add_blogger():
    """添加博主到内容池
    ---
    tags:
      - 博主
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - xhs_user_id
          properties:
            xhs_user_id:
              type: string
              description: 小红书用户ID
              example: "5f2b3c4d5e6f7a8b9c0d1e2f"
            nickname:
              type: string
              description: 昵称
            avatar_url:
              type: string
              description: 头像URL
            description:
              type: string
              description: 简介
            fans_count:
              type: integer
              description: 粉丝数
    responses:
      201:
        description: 添加成功
        schema:
          type: object
          properties:
            success:
              type: boolean
            msg:
              type: string
            data:
              type: object
      400:
        description: 参数错误或已存在
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    xhs_user_id = data.get("xhs_user_id", "").strip()
    if not xhs_user_id:
        return jsonify({"success": False, "msg": "xhs_user_id 不能为空"}), 400

    success, msg, result = ContentPoolService.add_blogger(
        user_id=user_id,
        xhs_user_id=xhs_user_id,
        nickname=data.get("nickname"),
        avatar_url=data.get("avatar_url"),
        description=data.get("description"),
        fans_count=data.get("fans_count"),
    )
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 201
    return jsonify({"success": False, "msg": msg, "data": result}), 400


@bloggers_bp.route("", methods=["GET"])
@jwt_required()
def list_bloggers():
    """列出用户的博主列表（支持按标签筛选）
    ---
    tags:
      - 博主
    security:
      - Bearer: []
    parameters:
      - in: query
        name: tag
        type: string
        required: false
        description: 按标签名筛选
    responses:
      200:
        description: 博主列表
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
    """
    user_id = int(get_jwt_identity())
    tag_name = request.args.get("tag")
    bloggers = ContentPoolService.list_bloggers(user_id, tag_name)
    return jsonify({"success": True, "data": bloggers}), 200


@bloggers_bp.route("/<int:blogger_id>", methods=["DELETE"])
@jwt_required()
def delete_blogger(blogger_id):
    """移除博主
    ---
    tags:
      - 博主
    security:
      - Bearer: []
    parameters:
      - in: path
        name: blogger_id
        type: integer
        required: true
        description: 博主ID
    responses:
      200:
        description: 删除成功
      404:
        description: 博主不存在
    """
    user_id = int(get_jwt_identity())
    success, msg = ContentPoolService.delete_blogger(user_id, blogger_id)
    if success:
        return jsonify({"success": True, "msg": msg}), 200
    return jsonify({"success": False, "msg": msg}), 404


@bloggers_bp.route("/<int:blogger_id>/tags", methods=["POST"])
@jwt_required()
def add_tags_to_blogger(blogger_id):
    """给博主打标签
    ---
    tags:
      - 博主
    security:
      - Bearer: []
    parameters:
      - in: path
        name: blogger_id
        type: integer
        required: true
        description: 博主ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - tags
          properties:
            tags:
              type: array
              items:
                type: string
              description: 标签名列表
              example: ["美食", "探店"]
    responses:
      200:
        description: 打标签成功
      404:
        description: 博主不存在
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    tag_names = data.get("tags", [])
    if not tag_names:
        return jsonify({"success": False, "msg": "tags 列表不能为空"}), 400

    success, msg, result = ContentPoolService.add_tags_to_blogger(
        user_id, blogger_id, tag_names
    )
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 200
    return jsonify({"success": False, "msg": msg}), 404


@bloggers_bp.route("/<int:blogger_id>/auto-tag", methods=["POST"])
@jwt_required()
def auto_tag_blogger(blogger_id):
    """AI 自动生成标签
    ---
    tags:
      - 博主
    security:
      - Bearer: []
    parameters:
      - in: path
        name: blogger_id
        type: integer
        required: true
        description: 博主ID
    responses:
      200:
        description: 自动标签成功
        schema:
          type: object
          properties:
            success:
              type: boolean
            msg:
              type: string
            data:
              type: object
      500:
        description: AI 标签生成失败
    """
    user_id = int(get_jwt_identity())
    success, msg, result = ContentPoolService.auto_tag_blogger(user_id, blogger_id)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 200
    return jsonify({"success": False, "msg": msg}), 500
