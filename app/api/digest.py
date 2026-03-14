# encoding: utf-8
"""每日摘要 API: /api/digest/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.digest_service import DigestService

digest_bp = Blueprint("digest", __name__)


@digest_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_digest():
    """触发生成每日摘要（后台线程处理）"""
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
    """查询摘要生成任务状态"""
    user_id = int(get_jwt_identity())
    task = DigestService.get_task_status(user_id)
    if task:
        return jsonify({"success": True, "data": task}), 200
    return jsonify({"success": True, "data": {"status": "idle", "msg": "无进行中的任务"}}), 200


@digest_bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_digest():
    """获取最新摘要"""
    user_id = int(get_jwt_identity())
    digest = DigestService.get_latest_digest(user_id)
    if digest:
        return jsonify({"success": True, "data": digest}), 200
    return jsonify({"success": False, "msg": "暂无摘要"}), 404


@digest_bp.route("/history", methods=["GET"])
@jwt_required()
def get_digest_history():
    """获取摘要历史列表"""
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    result = DigestService.get_digest_history(user_id, page, per_page)
    return jsonify({"success": True, "data": result}), 200


@digest_bp.route("/<int:digest_id>", methods=["GET"])
@jwt_required()
def get_digest_detail(digest_id):
    """获取特定摘要详情"""
    user_id = int(get_jwt_identity())
    digest = DigestService.get_digest_by_id(user_id, digest_id)
    if digest:
        return jsonify({"success": True, "data": digest}), 200
    return jsonify({"success": False, "msg": "摘要不存在"}), 404
