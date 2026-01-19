# encoding: utf-8
"""
数据库配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': '8.155.168.11',
    'port': 3306,
    'user': 'root',
    'password': 'MicroXLab',
    'database': 'infoplan',
    'charset': 'utf8mb4'
}

# 数据库URL
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"

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
