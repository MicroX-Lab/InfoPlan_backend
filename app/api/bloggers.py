# encoding: utf-8
"""博主管理 API: /api/bloggers/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.content_pool_service import ContentPoolService

bloggers_bp = Blueprint("bloggers", __name__)


@bloggers_bp.route("/search", methods=["POST"])
@jwt_required()
def search_blogger():
    """搜索小红书博主"""
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
    """添加博主到内容池"""
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
    """列出用户的博主列表（支持按标签筛选）"""
    user_id = int(get_jwt_identity())
    tag_name = request.args.get("tag")
    bloggers = ContentPoolService.list_bloggers(user_id, tag_name)
    return jsonify({"success": True, "data": bloggers}), 200


@bloggers_bp.route("/<int:blogger_id>", methods=["DELETE"])
@jwt_required()
def delete_blogger(blogger_id):
    """移除博主"""
    user_id = int(get_jwt_identity())
    success, msg = ContentPoolService.delete_blogger(user_id, blogger_id)
    if success:
        return jsonify({"success": True, "msg": msg}), 200
    return jsonify({"success": False, "msg": msg}), 404


@bloggers_bp.route("/<int:blogger_id>/tags", methods=["POST"])
@jwt_required()
def add_tags_to_blogger(blogger_id):
    """给博主打标签"""
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
    """AI 自动生成标签"""
    user_id = int(get_jwt_identity())
    success, msg, result = ContentPoolService.auto_tag_blogger(user_id, blogger_id)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 200
    return jsonify({"success": False, "msg": msg}), 500
