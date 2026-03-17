# encoding: utf-8
"""
数据库配置文件 - SQLite版本
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'infoplan.db')

# 确保data目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 数据库URL (SQLite)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 保留DB_CONFIG用于兼容性
DB_CONFIG = {
    'path': DB_PATH,
    'database': 'infoplan'
}

# 邮件配置
MAIL_CONFIG = {
    'SERVER': 'smtp.exmail.qq.com',
    'PORT': 465,
    'USE_SSL': True,
    'USERNAME': 'nono@ycy.fan',
    'PASSWORD': os.getenv('MAIL_PASSWORD', ''),  # 从环境变量获取密码
    'DEFAULT_SENDER': 'nono@ycy.fan'
}

# JWT配置
JWT_CONFIG = {
    'SECRET_KEY': os.getenv('JWT_SECRET', 'your-secret-key-here'),
    'ALGORITHM': 'HS256',
    'ACCESS_TOKEN_EXPIRE_MINUTES': 30
}
