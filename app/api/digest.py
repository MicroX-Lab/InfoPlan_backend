# encoding: utf-8
"""每日摘要 API: /api/digest/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.digest_service import DigestService

digest_bp = Blueprint("digest", __name__)


@digest_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_digest():
    """触发生成每日摘要（后台线程处理）
    ---
    tags:
      - 每日摘要
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            max_bloggers:
              type: integer
              description: 最大博主数
              default: 5
            notes_per_blogger:
              type: integer
              description: 每个博主笔记数
              default: 3
    responses:
      202:
        description: 任务已提交
        schema:
          type: object
          properties:
            success:
              type: boolean
            msg:
              type: string
            data:
              type: object
              properties:
                task_id:
                  type: string
      400:
        description: 已有任务进行中
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    max_bloggers = data.get("max_bloggers", 5)
    notes_per_blogger = data.get("notes_per_blogger", 3)

    success, msg, result = DigestService.generate_digest(
        user_id, max_bloggers, notes_per_blogger
    )
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 202
    return jsonify({"success": False, "msg": msg, "data": result}), 400


@digest_bp.route("/status", methods=["GET"])
@jwt_required()
def digest_status():
    """查询摘要生成任务状态
    ---
    tags:
      - 每日摘要
    security:
      - Bearer: []
    responses:
      200:
        description: 任务状态
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                status:
                  type: string
                  enum: [pending, processing, completed, failed, idle]
                msg:
                  type: string
    """
    user_id = int(get_jwt_identity())
    task = DigestService.get_task_status(user_id)
    if task:
        return jsonify({"success": True, "data": task}), 200
    return jsonify({"success": True, "data": {"status": "idle", "msg": "无进行中的任务"}}), 200


@digest_bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_digest():
    """获取最新摘要
    ---
    tags:
      - 每日摘要
    security:
      - Bearer: []
    responses:
      200:
        description: 最新摘要
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      404:
        description: 暂无摘要
    """
    user_id = int(get_jwt_identity())
    digest = DigestService.get_latest_digest(user_id)
    if digest:
        return jsonify({"success": True, "data": digest}), 200
    return jsonify({"success": False, "msg": "暂无摘要"}), 404


@digest_bp.route("/history", methods=["GET"])
@jwt_required()
def get_digest_history():
    """获取摘要历史列表
    ---
    tags:
      - 每日摘要
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
        default: 10
        description: 每页数量
    responses:
      200:
        description: 摘要历史
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
    per_page = request.args.get("per_page", 10, type=int)
    result = DigestService.get_digest_history(user_id, page, per_page)
    return jsonify({"success": True, "data": result}), 200


@digest_bp.route("/<int:digest_id>", methods=["GET"])
@jwt_required()
def get_digest_detail(digest_id):
    """获取特定摘要详情
    ---
    tags:
      - 每日摘要
    security:
      - Bearer: []
    parameters:
      - in: path
        name: digest_id
        type: integer
        required: true
        description: 摘要ID
    responses:
      200:
        description: 摘要详情
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      404:
        description: 摘要不存在
    """
    user_id = int(get_jwt_identity())
    digest = DigestService.get_digest_by_id(user_id, digest_id)
    if digest:
        return jsonify({"success": True, "data": digest}), 200
    return jsonify({"success": False, "msg": "摘要不存在"}), 404
