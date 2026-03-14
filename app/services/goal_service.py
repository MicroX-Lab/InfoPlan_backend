# encoding: utf-8
"""目标规划服务层：目标 CRUD + LLM 计划生成 + 关键词匹配 fallback

重构自 XHS_Learing_Agent/model_service/learning_agent.py，
改为通过 vLLM OpenAI 兼容 API 调用，替代本地 transformers 推理。
"""
import json
import re
import threading
from datetime import datetime

from flask import current_app
from loguru import logger

from app.extensions import db
from app.models.goal import Goal, PlanStep, step_notes
from app.models.note import Note
from app.models.bookmark import UserBookmark
from app.models.blogger import Blogger
from app.services.llm_service import llm_service
from app.services.xhs_service import xhs_service


# 后台任务状态: {user_id: {"status": ..., "goal_id": ..., "msg": ...}}
_plan_tasks = {}
_tasks_lock = threading.Lock()

# 配置常量
MAX_NOTES_FOR_MATCHING = 50
NOTES_PER_STEP = 3


class GoalService:
    """目标规划服务"""

    # ─── Goal CRUD ───────────────────────────────────

    @staticmethod
    def create_goal(user_id: int, title: str, description: str = None) -> tuple[bool, str, dict | None]:
        if not title or not title.strip():
            return False, "目标标题不能为空", None
        goal = Goal(user_id=user_id, title=title.strip(), description=description)
        db.session.add(goal)
        db.session.commit()
        return True, "目标创建成功", goal.to_dict()

    @staticmethod
    def list_goals(user_id: int) -> list[dict]:
        goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()
        return [g.to_dict() for g in goals]

    @staticmethod
    def get_goal(user_id: int, goal_id: int) -> dict | None:
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        return goal.to_dict() if goal else None

    @staticmethod
    def update_goal(user_id: int, goal_id: int, title: str = None,
                    description: str = None, status: str = None) -> tuple[bool, str, dict | None]:
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        if not goal:
            return False, "目标不存在", None
        if title is not None:
            goal.title = title.strip()
        if description is not None:
            goal.description = description
        if status is not None:
            if status not in ("active", "completed", "paused", "cancelled"):
                return False, "无效的状态值", None
            goal.status = status
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "目标更新成功", goal.to_dict()

    @staticmethod
    def delete_goal(user_id: int, goal_id: int) -> tuple[bool, str]:
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        if not goal:
            return False, "目标不存在"
        db.session.delete(goal)
        db.session.commit()
        return True, "目标已删除"

    @staticmethod
    def update_step(user_id: int, goal_id: int, step_id: int,
                    status: str = None) -> tuple[bool, str, dict | None]:
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        if not goal:
            return False, "目标不存在", None
        step = PlanStep.query.filter_by(id=step_id, goal_id=goal_id).first()
        if not step:
            return False, "步骤不存在", None
        if status is not None:
            if status not in ("pending", "in_progress", "completed", "skipped"):
                return False, "无效的步骤状态", None
            step.status = status
        db.session.commit()
        return True, "步骤已更新", step.to_dict()

    # ─── 计划生成（后台线程） ─────────────────────────

    @staticmethod
    def get_plan_task_status(user_id: int) -> dict | None:
        with _tasks_lock:
            return _plan_tasks.get(user_id)

    @staticmethod
    def generate_plan(user_id: int, goal_id: int) -> tuple[bool, str, dict | None]:
        """触发 LLM 生成计划（后台线程）"""
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        if not goal:
            return False, "目标不存在", None

        with _tasks_lock:
            task = _plan_tasks.get(user_id)
            if task and task["status"] == "processing":
                return False, "正在生成计划，请稍候", {"status": "processing"}

        with _tasks_lock:
            _plan_tasks[user_id] = {"status": "processing", "goal_id": goal_id, "msg": "正在生成..."}

        app = current_app._get_current_object()
        thread = threading.Thread(
            target=GoalService._generate_plan_in_background,
            args=(app, user_id, goal_id),
            daemon=True,
        )
        thread.start()
        return True, "计划生成已启动", {"status": "processing"}

    @staticmethod
    def _generate_plan_in_background(app, user_id: int, goal_id: int):
        """后台线程：LLM 目标拆解 + 笔记匹配"""
        with app.app_context():
            try:
                goal = Goal.query.get(goal_id)
                if not goal:
                    raise ValueError("目标不存在")

                # 1. 收集用户相关笔记（收藏 + 内容池博主笔记）
                notes = GoalService._collect_user_notes(user_id)
                notes_context = GoalService._build_notes_context(notes)

                logger.info(f"用户 {user_id}: 收集到 {len(notes)} 条笔记用于计划生成")

                # 2. 调用 LLM 拆解目标
                plan_result = llm_service.decompose_goal(goal.title, notes_context)

                if not plan_result or "steps" not in plan_result:
                    raise ValueError("LLM 目标拆解失败，未返回有效步骤")

                raw_steps = plan_result["steps"]

                # 3. 删除旧步骤（如果有），创建新步骤
                PlanStep.query.filter_by(goal_id=goal_id).delete()
                db.session.flush()

                new_steps = []
                for i, s in enumerate(raw_steps, 1):
                    if isinstance(s, str):
                        step = PlanStep(
                            goal_id=goal_id, step_number=i,
                            title=s, description="", time_estimate=""
                        )
                    else:
                        step = PlanStep(
                            goal_id=goal_id, step_number=i,
                            title=s.get("title", f"步骤{i}"),
                            description=s.get("description", ""),
                            time_estimate=s.get("time_estimate", ""),
                            start_date=s.get("start_date"),
                            end_date=s.get("end_date"),
                        )
                    db.session.add(step)
                    new_steps.append(step)

                db.session.flush()

                # 4. 笔记匹配（LLM + 关键词 fallback）
                if notes:
                    GoalService._match_and_link_notes(new_steps, notes)

                goal.updated_at = datetime.utcnow()
                db.session.commit()

                logger.info(f"用户 {user_id}: 目标 {goal_id} 计划生成完成，共 {len(new_steps)} 个步骤")

                with _tasks_lock:
                    _plan_tasks[user_id] = {
                        "status": "done", "goal_id": goal_id,
                        "msg": f"计划生成完成，共 {len(new_steps)} 个步骤"
                    }

            except Exception as e:
                logger.error(f"用户 {user_id}: 计划生成失败: {e}", exc_info=True)
                with _tasks_lock:
                    _plan_tasks[user_id] = {
                        "status": "error", "goal_id": goal_id,
                        "msg": f"生成失败: {str(e)}"
                    }

    @staticmethod
    def _collect_user_notes(user_id: int) -> list[Note]:
        """收集用户相关笔记：收藏笔记 + 内容池博主的笔记"""
        notes = []

        # 收藏的笔记
        bookmarks = UserBookmark.query.filter_by(user_id=user_id).all()
        for bm in bookmarks:
            if bm.note:
                notes.append(bm.note)

        # 内容池博主的笔记（已抓取的）
        bloggers = Blogger.query.filter_by(user_id=user_id).all()
        blogger_ids = [b.id for b in bloggers]
        if blogger_ids:
            blogger_notes = Note.query.filter(
                Note.blogger_id.in_(blogger_ids)
            ).order_by(Note.fetched_at.desc()).limit(MAX_NOTES_FOR_MATCHING).all()
            # 去重
            existing_ids = {n.id for n in notes}
            for n in blogger_notes:
                if n.id not in existing_ids:
                    notes.append(n)

        return notes[:MAX_NOTES_FOR_MATCHING]

    @staticmethod
    def _build_notes_context(notes: list[Note]) -> str:
        """构建笔记上下文字符串，用于 LLM 输入"""
        if not notes:
            return ""
        lines = []
        for n in notes[:15]:
            tags = ""
            if n.tags_json:
                try:
                    tags = ", ".join(json.loads(n.tags_json))
                except (json.JSONDecodeError, TypeError):
                    pass
            line = f"- {n.title or '无标题'}"
            if n.description:
                line += f"：{n.description[:80]}"
            if tags:
                line += f" [{tags}]"
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _match_and_link_notes(steps: list[PlanStep], notes: list[Note]):
        """将笔记匹配到步骤：先尝试 LLM，失败则用关键词 fallback"""
        steps_dicts = [{"title": s.title, "description": s.description or ""} for s in steps]
        notes_dicts = [
            {
                "note_id": n.note_id,
                "title": n.title or "",
                "desc": n.description or "",
            }
            for n in notes
        ]

        # 尝试 LLM 匹配
        match_result = llm_service.match_notes_to_steps(steps_dicts, notes_dicts)
        matches = match_result.get("matches", {})

        # 构建 note_id -> Note 映射
        note_map = {n.note_id: n for n in notes}

        llm_matched = False
        for step_key, matched_note_ids in matches.items():
            if not isinstance(matched_note_ids, list):
                continue
            # 找到对应的步骤（步骤编号 1-based）
            try:
                step_idx = int(re.search(r'\d+', str(step_key)).group()) - 1
            except (AttributeError, ValueError):
                continue
            if 0 <= step_idx < len(steps):
                for nid in matched_note_ids:
                    note = note_map.get(str(nid))
                    if note and note not in steps[step_idx].related_notes:
                        steps[step_idx].related_notes.append(note)
                        llm_matched = True

        # 如果 LLM 匹配没有结果，使用关键词 fallback
        if not llm_matched:
            logger.info("LLM 匹配无结果，使用关键词匹配 fallback")
            GoalService._match_by_keywords(steps, notes)

    @staticmethod
    def _match_by_keywords(steps: list[PlanStep], notes: list[Note]):
        """关键词匹配 fallback（复用 learning_agent.py 的逻辑）"""

        def extract_keywords(text: str) -> list[str]:
            keywords = []
            chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
            keywords.extend(chinese_words)
            english_words = re.findall(r'\b[A-Za-z]{3,}\b', text)
            keywords.extend([w.lower() for w in english_words])
            return keywords

        for step in steps:
            step_text = f"{step.title} {step.description or ''}"
            step_keywords = extract_keywords(step_text)
            if not step_keywords:
                continue

            note_scores = []
            for note in notes:
                score = 0
                note_title = (note.title or "").lower()
                note_desc = (note.description or "").lower()
                note_tags_str = ""
                if note.tags_json:
                    try:
                        note_tags_str = " ".join(json.loads(note.tags_json)).lower()
                    except (json.JSONDecodeError, TypeError):
                        pass

                note_text = f"{note_title} {note_desc} {note_tags_str}"

                for kw in step_keywords:
                    kw_lower = kw.lower()
                    if kw_lower in note_text:
                        score += 2
                    if kw_lower in note_title:
                        score += 3
                    if kw_lower in note_tags_str:
                        score += 2

                if score > 0:
                    note_scores.append((score, note))

            note_scores.sort(reverse=True, key=lambda x: x[0])
            for _, note in note_scores[:NOTES_PER_STEP]:
                if note not in step.related_notes:
                    step.related_notes.append(note)

    # ─── Bookmarks ───────────────────────────────────

    @staticmethod
    def add_bookmark(user_id: int, note_id: str,
                     custom_tags: list[str] = None) -> tuple[bool, str, dict | None]:
        """用户收藏笔记"""
        note = Note.query.filter_by(note_id=note_id).first()
        if not note:
            return False, "笔记不存在，请先通过摘要或分享链接获取笔记", None

        existing = UserBookmark.query.filter_by(user_id=user_id, note_id=note.id).first()
        if existing:
            return False, "已收藏该笔记", existing.to_dict()

        bookmark = UserBookmark(
            user_id=user_id,
            note_id=note.id,
            custom_tags_json=json.dumps(custom_tags, ensure_ascii=False) if custom_tags else None,
        )
        db.session.add(bookmark)
        db.session.commit()
        return True, "收藏成功", bookmark.to_dict()

    @staticmethod
    def list_bookmarks(user_id: int, page: int = 1, per_page: int = 20) -> dict:
        """列出用户收藏的笔记"""
        pagination = UserBookmark.query.filter_by(user_id=user_id) \
            .order_by(UserBookmark.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": [bm.to_dict() for bm in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }

    @staticmethod
    def delete_bookmark(user_id: int, bookmark_id: int) -> tuple[bool, str]:
        """取消收藏"""
        bookmark = UserBookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
        if not bookmark:
            return False, "收藏记录不存在"
        db.session.delete(bookmark)
        db.session.commit()
        return True, "已取消收藏"
