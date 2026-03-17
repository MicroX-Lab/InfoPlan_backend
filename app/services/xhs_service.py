# encoding: utf-8
"""XHS 爬虫服务封装层，包装现有 XHS_Apis + TTLCache 缓存"""
from cachetools import TTLCache
from flask import current_app
from loguru import logger

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.note_fetcher import NoteFetcher
from xhs_utils.share_link_parser import ShareLinkParser
from xhs_utils.data_util import handle_note_info


class XHSService:
    """封装 XHS API 调用，提供缓存和统一错误处理"""

    def __init__(self):
        self.api = XHS_Apis()
        self.parser = ShareLinkParser()
        # 缓存：最多 256 条，TTL 10 分钟
        self._user_cache = TTLCache(maxsize=256, ttl=600)
        self._note_cache = TTLCache(maxsize=512, ttl=600)

    @property
    def cookies(self) -> str:
        return current_app.config["COOKIES"]

    def search_user(self, query: str, page: int = 1) -> tuple[bool, str, dict | None]:
        """搜索小红书用户"""
        cache_key = f"search_user:{query}:{page}"
        if cache_key in self._user_cache:
            return True, "搜索成功(缓存)", self._user_cache[cache_key]

        success, msg, res_json = self.api.search_user(query, self.cookies, page)
        if success and res_json:
            data = res_json.get("data", {})
            result_code = data.get("result", {}).get("code")
            if result_code == 1000:
                # 业务成功，缓存并返回
                self._user_cache[cache_key] = data
                return True, "搜索成功", data
            # 非 1000（如 3002 无更多结果）：不缓存，返回空数据
            logger.warning(f"XHS search_user 业务码: code={result_code}, msg={msg}")
            return True, "没有更多结果", {"users": [], "has_more": False}
        return False, msg, None

    def get_users_latest_notes(
        self, user_ids: list[str], max_users: int = 5, notes_per_user: int = 5
    ) -> list[dict]:
        """批量获取多个用户最新笔记"""
        fetcher = NoteFetcher(self.cookies)
        notes = fetcher.get_users_latest_notes(user_ids, max_users, notes_per_user)
        return notes

    def parse_share_link(self, share_text: str) -> dict | None:
        """解析分享链接"""
        parsed = self.parser.parse_share_link(share_text)
        if not parsed or not parsed.get("note_id"):
            return None

        # 尝试提取标题和作者
        title = self.parser.extract_title_from_share_text(share_text)
        author = self.parser.extract_author_from_share_text(share_text)
        if title:
            parsed["title"] = title
        if author:
            parsed["author"] = author
        return parsed

    def get_note_by_share_link(
        self, share_text: str, get_comments: bool = False
    ) -> tuple[bool, str, dict | None]:
        """通过分享链接获取笔记详情"""
        parsed = self.parse_share_link(share_text)
        if not parsed:
            return False, "无法解析分享链接", None

        note_id = parsed["note_id"]
        explore_url = parsed["explore_url"]

        # 查缓存
        if note_id in self._note_cache and not get_comments:
            return True, "获取成功(缓存)", self._note_cache[note_id]

        # 获取笔记详情
        success, msg, note_info = self.api.get_note_info(explore_url, self.cookies)
        if not success:
            return False, f"获取笔记失败: {msg}", None

        # 检查业务错误
        if note_info and not note_info.get("success", True):
            api_msg = note_info.get("msg", "未知错误")
            return False, f"小红书API返回错误: {api_msg}", None

        # 处理数据
        data = note_info.get("data", {})
        items = data.get("items", [])
        if not items:
            if not data:
                return False, "笔记数据为空，可能原因：Cookie失效或触发反爬验证，请更新Cookie后重试", None
            return False, "笔记数据为空，笔记可能已被删除", None

        note_data = items[0]
        note_data["url"] = explore_url
        handled_note = handle_note_info(note_data)
        handled_note["parsed_info"] = {
            "note_id": note_id,
            "xsec_token": parsed.get("xsec_token", ""),
            "xsec_source": parsed.get("xsec_source", ""),
        }

        # 获取评论
        if get_comments:
            handled_note["comments"] = self._fetch_comments(
                note_id, parsed.get("xsec_token", "")
            )

        self._note_cache[note_id] = handled_note
        return True, "获取笔记成功", handled_note

    def _fetch_comments(self, note_id: str, xsec_token: str) -> list:
        """获取笔记评论"""
        if not xsec_token:
            return []
        try:
            success, msg, comments = self.api.get_note_all_out_comment(
                note_id, xsec_token, self.cookies
            )
            if success:
                return comments
            logger.warning(f"获取评论失败: {msg}")
        except Exception as e:
            logger.error(f"获取评论异常: {e}")
        return []


# 全局单例
xhs_service = XHSService()
