# encoding: utf-8
"""
数据库连接管理
"""
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from db_config import DB_CONFIG, DATABASE_URL
from models.user import User

# 创建基类
Base = declarative_base()


# 定义用户模型
class UserModel(Base, User):
    __tablename__ = 'users'


# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_database():
    """
    创建数据库
    """
    try:
        # 先连接到MySQL服务器
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET {DB_CONFIG['charset']}")
        print(f"✅ 数据库 {DB_CONFIG['database']} 创建成功")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ 创建数据库失败: {str(e)}")
        raise


def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库（创建表）
    """
    # 先创建数据库
    create_database()
    
    # 再创建表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表初始化完成")


def drop_db():
    """
    删除所有表（谨慎使用）
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  数据库表已删除")
