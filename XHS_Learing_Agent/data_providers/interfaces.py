from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel


class NoteInfo(BaseModel):
    """笔记信息数据模型"""
    note_id: str
    title: str
    desc: str
    type: str = "normal"  # normal: 图集, video: 视频
    liked_count: int = 0
    collected_count: int = 0
    comment_count: int = 0
    user_id: str = ""
    nickname: str = ""
    tags: List[str] = []
    
    class Config:
        extra = "allow"  # 允许额外字段


class DataProvider(ABC):
    """数据提供者抽象接口"""
    
    @abstractmethod
    def get_user_notes(self, user_ids: List[str], max_notes_per_user: int = 20) -> List[NoteInfo]:
        """
        获取指定用户的笔记列表
        :param user_ids: 用户ID列表
        :param max_notes_per_user: 每个用户最多获取的笔记数
        :return: 笔记列表
        """
        pass
    
    @abstractmethod
    def get_note_detail(self, note_id: str) -> Optional[NoteInfo]:
        """
        获取笔记详细信息
        :param note_id: 笔记ID
        :return: 笔记详细信息，如果不存在返回None
        """
        pass