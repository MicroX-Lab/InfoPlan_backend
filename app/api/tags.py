# encoding: utf-8
"""标签管理 API: /api/tags/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.content_pool_service import ContentPoolService

tags_bp = Blueprint("tags", __name__)


@tags_bp.route("", methods=["GET"])
@jwt_required()
def list_tags():
    """列出用户的标签
    ---
    tags:
      - 标签
    security:
      - Bearer: []
    responses:
      200:
        description: 标签列表
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
    """
    user_id = int(get_jwt_identity())
    tags = ContentPoolService.list_tags(user_id)
    return jsonify({"success": True, "data": tags}), 200


@tags_bp.route("", methods=["POST"])
@jwt_required()
def create_tag():
    """创建标签
    ---
    tags:
      - 标签
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: 标签名
              example: "美食"
    responses:
      201:
        description: 创建成功
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
        description: 参数错误或标签已存在
    """
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
    """删除标签
    ---
    tags:
      - 标签
    security:
      - Bearer: []
    parameters:
      - in: path
        name: tag_id
        type: integer
        required: true
        description: 标签ID
    responses:
      200:
        description: 删除成功
      404:
        description: 标签不存在
    """
    user_id = int(get_jwt_identity())
    success, msg = ContentPoolService.delete_tag(user_id, tag_id)
    if success:
        return jsonify({"success": True, "msg": msg}), 200
    return jsonify({"success": False, "msg": msg}), 404
