# encoding: utf-8
"""用户收藏笔记 API: /api/bookmarks/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.goal_service import GoalService

bookmarks_bp = Blueprint("bookmarks", __name__)


@bookmarks_bp.route("", methods=["POST"])
@jwt_required()
def add_bookmark():
    """收藏笔记
    ---
    tags:
      - 收藏
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - note_id
          properties:
            note_id:
              type: string
              description: 笔记ID
              example: "abc123"
            custom_tags:
              type: array
              items:
                type: string
              description: 自定义标签
    responses:
      201:
        description: 收藏成功
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
        description: 参数错误或已收藏
    """
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
    """列出用户收藏的笔记
    ---
    tags:
      - 收藏
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: 页码
      - in: query
        name: per_page
        type: integer
        default: 20
        description: 每页数量
    responses:
      200:
        description: 收藏列表
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                items:
                  type: array
                  items:
                    type: object
                total:
                  type: integer
                page:
                  type: integer
                per_page:
                  type: integer
    """
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    result = GoalService.list_bookmarks(user_id, page, per_page)
    return jsonify({"success": True, "data": result}), 200


@bookmarks_bp.route("/<int:bookmark_id>", methods=["DELETE"])
@jwt_required()
def delete_bookmark(bookmark_id):
    """取消收藏
    ---
    tags:
      - 收藏
    security:
      - Bearer: []
    parameters:
      - in: path
        name: bookmark_id
        type: integer
        required: true
        description: 收藏ID
    responses:
      200:
        description: 取消收藏成功
      404:
        description: 收藏不存在
    """
    user_id = int(get_jwt_identity())
    success, msg = GoalService.delete_bookmark(user_id, bookmark_id)
    if success:
        return jsonify({"success": True, "msg": msg}), 200
    return jsonify({"success": False, "msg": msg}), 404
