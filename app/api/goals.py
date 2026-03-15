# encoding: utf-8
"""目标规划 API: /api/goals/*"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.goal_service import GoalService

goals_bp = Blueprint("goals", __name__)


@goals_bp.route("", methods=["POST"])
@jwt_required()
def create_goal():
    """创建目标
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
          properties:
            title:
              type: string
              description: 目标标题
              example: "学习Python"
            description:
              type: string
              description: 目标描述
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
        description: 参数错误
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    description = data.get("description")

    if not title:
        return jsonify({"success": False, "msg": "目标标题不能为空"}), 400

    success, msg, result = GoalService.create_goal(user_id, title, description)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 201
    return jsonify({"success": False, "msg": msg}), 400


@goals_bp.route("", methods=["GET"])
@jwt_required()
def list_goals():
    """列出用户目标
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    responses:
      200:
        description: 目标列表
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
    """
    user_id = int(get_jwt_identity())
    goals = GoalService.list_goals(user_id)
    return jsonify({"success": True, "data": goals}), 200


@goals_bp.route("/<int:goal_id>", methods=["GET"])
@jwt_required()
def get_goal(goal_id):
    """获取目标详情（含计划步骤和关联笔记）
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    parameters:
      - in: path
        name: goal_id
        type: integer
        required: true
        description: 目标ID
    responses:
      200:
        description: 目标详情
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      404:
        description: 目标不存在
    """
    user_id = int(get_jwt_identity())
    goal = GoalService.get_goal(user_id, goal_id)
    if goal:
        return jsonify({"success": True, "data": goal}), 200
    return jsonify({"success": False, "msg": "目标不存在"}), 404


@goals_bp.route("/<int:goal_id>", methods=["PUT"])
@jwt_required()
def update_goal(goal_id):
    """更新目标
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    parameters:
      - in: path
        name: goal_id
        type: integer
        required: true
        description: 目标ID
      - in: body
        name: body
        schema:
          type: object
          properties:
            title:
              type: string
              description: 目标标题
            description:
              type: string
              description: 目标描述
            status:
              type: string
              description: 状态
              enum: [active, completed, archived]
    responses:
      200:
        description: 更新成功
      400:
        description: 参数错误
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    success, msg, result = GoalService.update_goal(
        user_id, goal_id,
        title=data.get("title"),
        description=data.get("description"),
        status=data.get("status"),
    )
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 200
    return jsonify({"success": False, "msg": msg}), 400


@goals_bp.route("/<int:goal_id>", methods=["DELETE"])
@jwt_required()
def delete_goal(goal_id):
    """删除目标
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    parameters:
      - in: path
        name: goal_id
        type: integer
        required: true
        description: 目标ID
    responses:
      200:
        description: 删除成功
      404:
        description: 目标不存在
    """
    user_id = int(get_jwt_identity())
    success, msg = GoalService.delete_goal(user_id, goal_id)
    if success:
        return jsonify({"success": True, "msg": msg}), 200
    return jsonify({"success": False, "msg": msg}), 404


@goals_bp.route("/<int:goal_id>/generate-plan", methods=["POST"])
@jwt_required()
def generate_plan(goal_id):
    """LLM 生成学习计划（后台线程处理）
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    parameters:
      - in: path
        name: goal_id
        type: integer
        required: true
        description: 目标ID
    responses:
      202:
        description: 计划生成任务已提交
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
        description: 已有任务进行中
    """
    user_id = int(get_jwt_identity())
    success, msg, result = GoalService.generate_plan(user_id, goal_id)
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 202
    return jsonify({"success": False, "msg": msg, "data": result}), 400


@goals_bp.route("/<int:goal_id>/plan-status", methods=["GET"])
@jwt_required()
def plan_status(goal_id):
    """查询计划生成任务状态
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    parameters:
      - in: path
        name: goal_id
        type: integer
        required: true
        description: 目标ID
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
    """
    user_id = int(get_jwt_identity())
    task = GoalService.get_plan_task_status(user_id)
    if task:
        return jsonify({"success": True, "data": task}), 200
    return jsonify({"success": True, "data": {"status": "idle", "msg": "无进行中的任务"}}), 200


@goals_bp.route("/<int:goal_id>/steps/<int:step_id>", methods=["PUT"])
@jwt_required()
def update_step(goal_id, step_id):
    """更新步骤状态
    ---
    tags:
      - 目标规划
    security:
      - Bearer: []
    parameters:
      - in: path
        name: goal_id
        type: integer
        required: true
        description: 目标ID
      - in: path
        name: step_id
        type: integer
        required: true
        description: 步骤ID
      - in: body
        name: body
        schema:
          type: object
          properties:
            status:
              type: string
              description: 步骤状态
    responses:
      200:
        description: 更新成功
      400:
        description: 参数错误
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    success, msg, result = GoalService.update_step(
        user_id, goal_id, step_id,
        status=data.get("status"),
    )
    if success:
        return jsonify({"success": True, "msg": msg, "data": result}), 200
    return jsonify({"success": False, "msg": msg}), 400
