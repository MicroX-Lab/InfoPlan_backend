# encoding: utf-8
"""笔记工具接口 API: /api/note/*
迁移自 api_server.py 的 /api/note/share 和 /api/note/parse
"""
from flask import Blueprint, request, jsonify
from loguru import logger

from app.services.xhs_service import xhs_service

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/share", methods=["POST"])
def get_note_by_share_link():
    """通过分享链接获取笔记详情
    ---
    tags:
      - 笔记
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - share_link
          properties:
            share_link:
              type: string
              description: 小红书分享链接
              example: "https://www.xiaohongshu.com/explore/xxx"
            get_comments:
              type: boolean
              description: 是否获取评论
              default: false
    responses:
      200:
        description: 获取成功
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
        description: 获取失败
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    share_link = data.get("share_link", "")
    if not share_link:
        return jsonify({"success": False, "msg": "share_link 参数不能为空"}), 400

    get_comments = data.get("get_comments", False)
    logger.info(f"收到通过分享链接获取笔记请求: {share_link[:100]}...")

    try:
        success, msg, note = xhs_service.get_note_by_share_link(share_link, get_comments)
        if success:
            return jsonify({"success": True, "msg": msg, "data": note}), 200
        return jsonify({"success": False, "msg": msg}), 500
    except Exception as e:
        logger.error(f"获取笔记失败: {e}", exc_info=True)
        return jsonify({"success": False, "msg": f"服务器错误: {str(e)}"}), 500


@notes_bp.route("/parse", methods=["POST"])
def parse_share_link():
    """仅解析分享链接，不获取笔记详情
    ---
    tags:
      - 笔记
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - share_link
          properties:
            share_link:
              type: string
              description: 小红书分享链接
              example: "https://www.xiaohongshu.com/explore/xxx"
    responses:
      200:
        description: 解析成功
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
        description: 参数缺失或无法解析
      500:
        description: 服务器错误
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "请求体不能为空"}), 400

    share_link = data.get("share_link", "")
    if not share_link:
        return jsonify({"success": False, "msg": "share_link 参数不能为空"}), 400

    logger.info(f"收到解析分享链接请求: {share_link[:100]}...")

    try:
        parsed = xhs_service.parse_share_link(share_link)
        if parsed:
            return jsonify({"success": True, "msg": "解析成功", "data": parsed}), 200
        return jsonify({"success": False, "msg": "无法解析分享链接"}), 400
    except Exception as e:
        logger.error(f"解析分享链接失败: {e}", exc_info=True)
        return jsonify({"success": False, "msg": f"服务器错误: {str(e)}"}), 500
