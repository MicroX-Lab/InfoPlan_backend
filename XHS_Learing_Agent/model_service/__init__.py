# model_service/__init__.py

# 方式1：直接导入（推荐）
from .learning_agent import XHSLearningAgent
from .interfaces import DataProvider, NoteInfo

__all__ = ['XHSLearningAgent', 'DataProvider', 'NoteInfo']