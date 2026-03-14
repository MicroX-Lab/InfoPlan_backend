# encoding: utf-8
"""用户收藏笔记 API: /api/bookmarks/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.goal_service import GoalService

bookmarks_bp = Blueprint("bookmarks", __name__)


@bookmarks_bp.route("", methods=["POST"])
@jwt_required()
def add_bookmark():
    """收藏笔记"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    note_id = data.get("note_id", "").strip()

    if not note_id:
        return jsonify({"success": False, "msg": "note_id 不能为空"}), 400

    custom_tags = data.get("custom_tags")
    success, msg, result = GoalService.add_bookmark(user_id, note_id, custom_tags)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 201
    return jsonify({"success": False, "msg": msg, "data": result}), 400


@bookmarks_bp.route("", methods=["GET"])
@jwt_required()
def list_bookmarks():
    """列出用户收藏的笔记"""
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    result = GoalService.list_bookmarks(user_id, page, per_page)
    return jsonify({"success": True, "data": result}), 200


@bookmarks_bp.route("/<int:bookmark_id>", methods=["DELETE"])
@jwt_required()
def delete_bookmark(bookmark_id):
    """取消收藏"""
    user_id = int(get_jwt_identity())
    success, msg = GoalService.delete_bookmark(user_id, bookmark_id)
    if success:
        return jsonify({"success": True, "msg": msg}), 200
    return jsonify({"success": False, "msg": msg}), 404
