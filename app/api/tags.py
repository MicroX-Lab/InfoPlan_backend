# encoding: utf-8
"""标签管理 API: /api/tags/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.content_pool_service import ContentPoolService

tags_bp = Blueprint("tags", __name__)


@tags_bp.route("", methods=["GET"])
@jwt_required()
def list_tags():
    """列出用户的标签"""
    user_id = int(get_jwt_identity())
    tags = ContentPoolService.list_tags(user_id)
    return jsonify({"success": True, "data": tags}), 200


@tags_bp.route("", methods=["POST"])
@jwt_required()
def create_tag():
    """创建标签"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "msg": "标签名不能为空"}), 400

    success, msg, result = ContentPoolService.create_tag(user_id, name)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 201
    return jsonify({"success": False, "msg": msg, "data": result}), 400


@tags_bp.route("/<int:tag_id>", methods=["DELETE"])
@jwt_required()
def delete_tag(tag_id):
    """删除标签"""
    user_id = int(get_jwt_identity())
    success, msg = ContentPoolService.delete_tag(user_id, tag_id)
    if success:
        return jsonify({"success": True, "msg": msg}), 200
    return jsonify({"success": False, "msg": msg}), 404
