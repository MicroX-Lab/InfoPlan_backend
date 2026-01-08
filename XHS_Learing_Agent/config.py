import os
from pathlib import Path
from typing import Optional

class Config:
    """项目配置类（Jupyter友好版本）"""
    
    # 模型配置（可在Jupyter中直接修改）
    MODEL_PATH: str = "/mnt/moark-models/Qwen3-8B"
    
    # Cookie配置（可在Jupyter中直接设置）
    COOKIES: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = Path("logs")
    
    # Agent配置
    MAX_NOTES_PER_USER: int = 20
    MAX_NOTES_FOR_MATCHING: int = 50
    NOTES_PER_STEP: int = 3
    MAX_NEW_TOKENS: int = 1024
    TEMPERATURE: float = 0.7
    
    @classmethod
    def init_log_dir(cls):
        """初始化日志目录"""
        cls.LOG_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.MODEL_PATH:
            raise ValueError("MODEL_PATH未配置")
        if not Path(cls.MODEL_PATH).exists():
            raise ValueError(f"模型路径不存在: {cls.MODEL_PATH}")
        cls.init_log_dir()
    
    @classmethod
    def set_model_path(cls, path: str):
        """设置模型路径"""
        cls.MODEL_PATH = path
    
    @classmethod
    def set_cookies(cls, cookies: str):
        """设置Cookie"""
        cls.COOKIES = cookies