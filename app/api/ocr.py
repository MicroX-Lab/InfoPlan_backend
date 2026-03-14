# encoding: utf-8
"""OCR 关注列表识别 API: /api/ocr/*"""
import base64

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.llm_service import llm_service

ocr_bp = Blueprint("ocr", __name__)

# 允许的图片 MIME 类型
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


@ocr_bp.route("/follow-list", methods=["POST"])
@jwt_required()
def ocr_follow_list():
    """上传关注列表截图，VL 模型识别博主昵称"""
    # 支持两种上传方式：文件上传 或 base64 JSON
    image_base64 = None

    if "image" in request.files:
        # 文件上传方式
        file = request.files["image"]
        if not file.filename:
            return jsonify({"success": False, "msg": "请上传图片文件"}), 400

        # 检查文件类型
        if file.content_type not in ALLOWED_MIME_TYPES:
            return jsonify({"success": False, "msg": "仅支持 PNG/JPEG/WebP 格式"}), 400

        # 读取并编码
        file_data = file.read()
        if len(file_data) > MAX_IMAGE_SIZE:
            return jsonify({"success": False, "msg": "图片大小不能超过 10MB"}), 400

        image_base64 = base64.b64encode(file_data).decode("utf-8")

    else:
        # JSON base64 方式
        data = request.get_json() or {}
        image_base64 = data.get("image_base64", "").strip()

    if not image_base64:
        return jsonify({"success": False, "msg": "请提供图片（文件上传或 base64）"}), 400

    # 调用 VL 模型 OCR
    nicknames = llm_service.ocr_follow_list(image_base64)

    if not nicknames:
        return jsonify({
            "success": False,
            "msg": "未能识别到博主昵称，请确保截图清晰完整"
        }), 200

    return jsonify({
        "success": True,
        "msg": f"识别到 {len(nicknames)} 个博主",
        "data": {"nicknames": nicknames, "count": len(nicknames)},
    }), 200
