# encoding: utf-8
"""内容池服务层：博主/标签管理"""
from loguru import logger
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.blogger import Blogger
from app.models.tag import Tag, blogger_tags
from app.services.xhs_service import xhs_service
from app.services.llm_service import llm_service


class ContentPoolService:
    """博主和标签管理"""

    # ── 博主搜索 ──

    @staticmethod
    def search_blogger(query: str, page: int = 1) -> tuple[bool, str, dict | None]:
        """搜索小红书博主（封装 xhs_service）"""
        return xhs_service.search_user(query, page)

    # ── 博主 CRUD ──

    @staticmethod
    def add_blogger(user_id: int, xhs_user_id: str, nickname: str = None,
                    avatar_url: str = None, description: str = None,
                    fans_count: str = None) -> tuple[bool, str, dict | None]:
        """添加博主到用户的内容池"""
        existing = Blogger.query.filter_by(
            user_id=user_id, xhs_user_id=xhs_user_id
        ).first()
        if existing:
            return False, "该博主已在内容池中", existing.to_dict()

        blogger = Blogger(
            user_id=user_id,
            xhs_user_id=xhs_user_id,
            nickname=nickname,
            avatar_url=avatar_url,
            description=description,
            fans_count=fans_count,
        )
        db.session.add(blogger)
        try:
            db.session.commit()
            return True, "添加成功", blogger.to_dict()
        except IntegrityError:
            db.session.rollback()
            return False, "添加失败：重复记录", None

    @staticmethod
    def list_bloggers(user_id: int, tag_name: str = None) -> list[dict]:
        """列出用户的博主列表，可按标签筛选"""
        query = Blogger.query.filter_by(user_id=user_id)
        if tag_name:
            query = query.filter(Blogger.tags.any(Tag.name == tag_name))
        bloggers = query.order_by(Blogger.created_at.desc()).all()
        return [b.to_dict() for b in bloggers]

    @staticmethod
    def delete_blogger(user_id: int, blogger_id: int) -> tuple[bool, str]:
        """移除博主"""
        blogger = Blogger.query.filter_by(id=blogger_id, user_id=user_id).first()
        if not blogger:
            return False, "博主不存在"
        db.session.delete(blogger)
        db.session.commit()
        return True, "删除成功"

    # ── 博主打标签 ──

    @staticmethod
    def add_tags_to_blogger(user_id: int, blogger_id: int,
                            tag_names: list[str]) -> tuple[bool, str, dict | None]:
        """给博主打标签（标签不存在则自动创建）"""
        blogger = Blogger.query.filter_by(id=blogger_id, user_id=user_id).first()
        if not blogger:
            return False, "博主不存在", None

        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag = Tag.query.filter_by(name=name, user_id=user_id).first()
            if not tag:
                tag = Tag(name=name, user_id=user_id, is_auto_generated=False)
                db.session.add(tag)
                db.session.flush()
            if tag not in blogger.tags.all():
                blogger.tags.append(tag)

        db.session.commit()
        return True, "标签添加成功", blogger.to_dict()

    @staticmethod
    def auto_tag_blogger(user_id: int, blogger_id: int) -> tuple[bool, str, dict | None]:
        """AI 自动为博主生成标签（Qwen3-4B）"""
        blogger = Blogger.query.filter_by(id=blogger_id, user_id=user_id).first()
        if not blogger:
            return False, "博主不存在", None

        # 获取博主最新笔记用于分析
        try:
            notes = xhs_service.get_users_latest_notes(
                [blogger.xhs_user_id], max_users=1, notes_per_user=5
            )
        except Exception as e:
            logger.error(f"获取博主笔记失败: {e}")
            return False, f"获取博主笔记失败: {e}", None

        if not notes:
            return False, "无法获取博主笔记，无法生成标签", None

        notes_info = [
            {"title": n.get("title", ""), "desc": n.get("desc", n.get("description", ""))}
            for n in notes
        ]

        tag_names = llm_service.generate_tags(notes_info)
        if not tag_names:
            return False, "AI 未能生成标签", None

        # 保存标签并关联
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag = Tag.query.filter_by(name=name, user_id=user_id).first()
            if not tag:
                tag = Tag(name=name, user_id=user_id, is_auto_generated=True)
                db.session.add(tag)
                db.session.flush()
            if tag not in blogger.tags.all():
                blogger.tags.append(tag)

        db.session.commit()
        return True, f"AI 生成了 {len(tag_names)} 个标签", blogger.to_dict()

    # ── 标签 CRUD ──

    @staticmethod
    def list_tags(user_id: int) -> list[dict]:
        """列出用户的所有标签"""
        tags = Tag.query.filter_by(user_id=user_id).order_by(Tag.id.desc()).all()
        return [t.to_dict() for t in tags]

    @staticmethod
    def create_tag(user_id: int, name: str) -> tuple[bool, str, dict | None]:
        """创建标签"""
        name = name.strip()
        if not name:
            return False, "标签名不能为空", None

        existing = Tag.query.filter_by(name=name, user_id=user_id).first()
        if existing:
            return False, "标签已存在", existing.to_dict()

        tag = Tag(name=name, user_id=user_id, is_auto_generated=False)
        db.session.add(tag)
        db.session.commit()
        return True, "创建成功", tag.to_dict()

    @staticmethod
    def delete_tag(user_id: int, tag_id: int) -> tuple[bool, str]:
        """删除标签"""
        tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
        if not tag:
            return False, "标签不存在"
        db.session.delete(tag)
        db.session.commit()
        return True, "删除成功"
