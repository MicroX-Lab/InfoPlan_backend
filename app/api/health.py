# encoding: utf-8
"""健康检查 API"""
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "service": "InfoPlan Backend",
        "message": "服务运行正常",
    }), 200
