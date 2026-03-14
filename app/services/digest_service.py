# encoding: utf-8
"""每日摘要服务层：笔记抓取 + LLM 摘要生成 + 后台线程处理"""
import json
import threading
from datetime import datetime

from flask import current_app
from loguru import logger

from app.extensions import db
from app.models.blogger import Blogger
from app.models.note import Note
from app.models.digest import Digest
from app.services.xhs_service import xhs_service
from app.services.llm_service import llm_service


# 存储后台任务状态: {user_id: {"status": "processing"|"done"|"error", "digest_id": int|None, "msg": str}}
_digest_tasks = {}
_tasks_lock = threading.Lock()


class DigestService:
    """每日摘要生成服务"""

    @staticmethod
    def get_task_status(user_id: int) -> dict | None:
        """获取用户当前摘要生成任务状态"""
        with _tasks_lock:
            return _digest_tasks.get(user_id)

    @staticmethod
    def generate_digest(user_id: int, max_bloggers: int = 5,
                        notes_per_blogger: int = 3) -> tuple[bool, str, dict | None]:
        """
        触发摘要生成（后台线程处理）

        流程：选 max_bloggers 个博主 x notes_per_blogger 条笔记 -> 存 notes 表 -> Qwen3-8B 摘要
        """
        # 检查是否有正在进行的任务
        with _tasks_lock:
            task = _digest_tasks.get(user_id)
            if task and task["status"] == "processing":
                return False, "正在生成摘要，请稍候", {"status": "processing"}

        # 检查用户是否有博主
        bloggers = Blogger.query.filter_by(user_id=user_id).all()
        if not bloggers:
            return False, "内容池为空，请先添加博主", None

        # 标记任务开始
        with _tasks_lock:
            _digest_tasks[user_id] = {"status": "processing", "digest_id": None, "msg": "正在生成..."}

        # 获取 app 引用，用于后台线程的 app context
        app = current_app._get_current_object()

        thread = threading.Thread(
            target=DigestService._generate_in_background,
            args=(app, user_id, bloggers, max_bloggers, notes_per_blogger),
            daemon=True,
        )
        thread.start()
        return True, "摘要生成已启动", {"status": "processing"}

    @staticmethod
    def _generate_in_background(app, user_id: int, bloggers: list,
                                max_bloggers: int, notes_per_blogger: int):
        """后台线程中执行摘要生成"""
        with app.app_context():
            try:
                # 1. 选取博主（最多 max_bloggers 个）
                selected_bloggers = bloggers[:max_bloggers]
                xhs_user_ids = [b.xhs_user_id for b in selected_bloggers]
                blogger_map = {b.xhs_user_id: b for b in selected_bloggers}

                logger.info(f"用户 {user_id}: 开始为 {len(xhs_user_ids)} 个博主获取笔记")

                # 2. 批量获取笔记
                raw_notes = xhs_service.get_users_latest_notes(
                    xhs_user_ids, max_users=max_bloggers, notes_per_user=notes_per_blogger
                )

                if not raw_notes:
                    with _tasks_lock:
                        _digest_tasks[user_id] = {
                            "status": "error", "digest_id": None,
                            "msg": "未能获取到任何笔记"
                        }
                    return

                logger.info(f"用户 {user_id}: 获取到 {len(raw_notes)} 条笔记，开始生成摘要")

                # 3. 存储笔记到 notes 表 + 生成摘要
                digest_items = []
                for raw in raw_notes:
                    note_id = raw.get("note_id", "")
                    if not note_id:
                        continue

                    title = raw.get("title", raw.get("display_title", ""))
                    desc = raw.get("desc", raw.get("description", ""))
                    note_type = raw.get("note_type", raw.get("type", "normal"))
                    xhs_uid = raw.get("user_id", "")

                    # 查找或创建 Note 记录
                    note = Note.query.filter_by(note_id=note_id).first()
                    if not note:
                        blogger_obj = blogger_map.get(xhs_uid)
                        note = Note(
                            note_id=note_id,
                            blogger_id=blogger_obj.id if blogger_obj else None,
                            title=title,
                            description=desc,
                            note_type=note_type,
                            liked_count=raw.get("liked_count", 0),
                            collected_count=raw.get("collected_count", 0),
                            comment_count=raw.get("comment_count", 0),
                            note_url=raw.get("url", raw.get("note_url", "")),
                            upload_time=raw.get("upload_time", raw.get("time", "")),
                            tags_json=json.dumps(raw.get("tags", []), ensure_ascii=False)
                            if raw.get("tags") else None,
                            image_urls_json=json.dumps(raw.get("image_urls", []), ensure_ascii=False)
                            if raw.get("image_urls") else None,
                        )
                        db.session.add(note)
                        db.session.flush()

                    # 生成摘要（如果还没有）
                    if not note.summary:
                        tags = raw.get("tags", [])
                        summary = llm_service.summarize_note(title, desc, tags)
                        if summary:
                            note.summary = summary

                    db.session.commit()

                    # 构建摘要条目
                    blogger_obj = blogger_map.get(xhs_uid)
                    digest_items.append({
                        "note_id": note_id,
                        "title": title,
                        "summary": note.summary or desc[:100],
                        "note_type": note_type,
                        "note_url": note.note_url or "",
                        "blogger_nickname": blogger_obj.nickname if blogger_obj else "",
                        "blogger_xhs_id": xhs_uid,
                    })

                # 4. 保存摘要
                digest = Digest(
                    user_id=user_id,
                    digest_json=json.dumps({
                        "total_notes": len(digest_items),
                        "bloggers_count": len(set(i["blogger_xhs_id"] for i in digest_items)),
                        "items": digest_items,
                    }, ensure_ascii=False),
                )
                db.session.add(digest)
                db.session.commit()

                logger.info(f"用户 {user_id}: 摘要生成完成，共 {len(digest_items)} 条")

                with _tasks_lock:
                    _digest_tasks[user_id] = {
                        "status": "done", "digest_id": digest.id,
                        "msg": f"摘要生成完成，包含 {len(digest_items)} 篇笔记"
                    }

            except Exception as e:
                logger.error(f"用户 {user_id}: 摘要生成失败: {e}", exc_info=True)
                with _tasks_lock:
                    _digest_tasks[user_id] = {
                        "status": "error", "digest_id": None,
                        "msg": f"生成失败: {str(e)}"
                    }

    @staticmethod
    def get_latest_digest(user_id: int) -> dict | None:
        """获取用户最新一条摘要"""
        digest = Digest.query.filter_by(user_id=user_id)\
            .order_by(Digest.created_at.desc()).first()
        return digest.to_dict() if digest else None

    @staticmethod
    def get_digest_history(user_id: int, page: int = 1,
                           per_page: int = 10) -> dict:
        """获取摘要历史列表（分页）"""
        pagination = Digest.query.filter_by(user_id=user_id)\
            .order_by(Digest.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": [d.to_dict() for d in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }

    @staticmethod
    def get_digest_by_id(user_id: int, digest_id: int) -> dict | None:
        """获取特定摘要详情"""
        digest = Digest.query.filter_by(id=digest_id, user_id=user_id).first()
        return digest.to_dict() if digest else None
