# encoding: utf-8
"""
数据库初始化脚本
"""
import pymysql
from db_config import DB_CONFIG


# 先创建数据库
try:
    print("正在创建数据库...")
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset=DB_CONFIG['charset']
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET {DB_CONFIG['charset']}")
    print(f"✅ 数据库 {DB_CONFIG['database']} 创建成功")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ 创建数据库失败: {str(e)}")
    exit(1)


# 现在导入其他模块
from db_connection import init_db, engine


if __name__ == '__main__':
    try:
        # 测试数据库连接
        with engine.connect() as conn:
            print("✅ 数据库连接成功")
        
        # 初始化数据库表
        init_db()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
