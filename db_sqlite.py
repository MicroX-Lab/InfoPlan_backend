# encoding: utf-8
"""
纯SQLite数据库工具模块
"""
import sqlite3
import os
from datetime import datetime

# 数据库文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'infoplan.db')


def get_connection():
    """
    获取数据库连接
    """
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    初始化数据库表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 创建用户表（整合schema）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nickname TEXT,
            avatar_url TEXT,
            is_verified BOOLEAN DEFAULT FALSE,
            verification_code TEXT,
            verification_expiry TIMESTAMP,
            reset_token TEXT,
            reset_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建博主表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bloggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            xhs_user_id TEXT NOT NULL,
            nickname TEXT,
            avatar_url TEXT,
            description TEXT,
            fans_count TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, xhs_user_id)
        )
    ''')
    
    # 创建标签表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            is_auto_generated BOOLEAN DEFAULT FALSE,
            UNIQUE(name, user_id)
        )
    ''')
    
    # 创建博主-标签关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blogger_tags (
            blogger_id INTEGER REFERENCES bloggers(id),
            tag_id INTEGER REFERENCES tags(id),
            PRIMARY KEY (blogger_id, tag_id)
        )
    ''')
    
    # 创建笔记缓存表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id TEXT UNIQUE NOT NULL,
            blogger_id INTEGER REFERENCES bloggers(id),
            title TEXT,
            description TEXT,
            note_type TEXT,
            liked_count INTEGER DEFAULT 0,
            collected_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            tags_json TEXT,
            image_urls_json TEXT,
            note_url TEXT,
            upload_time TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT
        )
    ''')
    
    # 创建笔记-标签关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER REFERENCES notes(id),
            tag_id INTEGER REFERENCES tags(id),
            PRIMARY KEY (note_id, tag_id)
        )
    ''')
    
    # 创建用户收藏笔记表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            note_id INTEGER NOT NULL REFERENCES notes(id),
            custom_tags_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, note_id)
        )
    ''')
    
    # 创建每日摘要表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            digest_json TEXT
        )
    ''')
    
    # 创建目标表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建计划步骤表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL REFERENCES goals(id),
            step_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            time_estimate TEXT,
            status TEXT DEFAULT 'pending',
            start_date TEXT,
            end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建步骤-笔记关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS step_notes (
            step_id INTEGER NOT NULL REFERENCES plan_steps(id),
            note_id INTEGER NOT NULL REFERENCES notes(id),
            relevance_score REAL DEFAULT 0.0,
            PRIMARY KEY (step_id, note_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库表初始化完成")


def check_user_exists(email):
    """
    检查用户是否存在（通过email）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()


def check_username_exists(username):
    """
    检查用户名是否已存在
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()


def get_user_by_email(email):
    """
    根据邮箱获取用户
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, email, password_hash, nickname, avatar_url, is_verified, 
                   verification_code, verification_expiry, 
                   reset_token, reset_expiry, created_at, updated_at
            FROM users 
            WHERE email = ?
        """, (email,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # 转换为字典
        user = {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'password_hash': row[3],
            'nickname': row[4],
            'avatar_url': row[5],
            'is_verified': bool(row[6]),
            'verification_code': row[7],
            'verification_expiry': row[8],
            'reset_token': row[9],
            'reset_expiry': row[10],
            'created_at': row[11],
            'updated_at': row[12]
        }
        
        return user
    finally:
        conn.close()


def get_user_by_username(username):
    """
    根据用户名获取用户
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, email, password_hash, nickname, avatar_url, is_verified, 
                   verification_code, verification_expiry, 
                   reset_token, reset_expiry, created_at, updated_at
            FROM users 
            WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # 转换为字典
        user = {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'password_hash': row[3],
            'nickname': row[4],
            'avatar_url': row[5],
            'is_verified': bool(row[6]),
            'verification_code': row[7],
            'verification_expiry': row[8],
            'reset_token': row[9],
            'reset_expiry': row[10],
            'created_at': row[11],
            'updated_at': row[12]
        }
        
        return user
    finally:
        conn.close()


def create_user(email, password_hash, verification_code, verification_expiry, username=None, nickname=None):
    """
    创建新用户
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (email, username, nickname, password_hash, is_verified, 
                             verification_code, verification_expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email, username, nickname, password_hash, False, verification_code, verification_expiry))
        
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_user_verification(email, is_verified):
    """
    更新用户验证状态
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET is_verified = ?, verification_code = NULL, verification_expiry = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (is_verified, email))
        
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_user_reset_token(email, reset_token, reset_expiry):
    """
    更新用户重置令牌
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET reset_token = ?, reset_expiry = ?, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (reset_token, reset_expiry, email))
        
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_user_password(email, new_password_hash):
    """
    更新用户密码
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, reset_token = NULL, reset_expiry = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (new_password_hash, email))
        
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_user_profile(email, nickname=None, avatar_url=None):
    """
    更新用户资料
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET nickname = COALESCE(?, nickname), 
                avatar_url = COALESCE(?, avatar_url),
                updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (nickname, avatar_url, email))
        
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_user_by_reset_token(email, token):
    """
    根据邮箱和重置令牌获取用户
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, email, reset_expiry 
            FROM users 
            WHERE email = ? AND reset_token = ?
        """, (email, token))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        user = {
            'id': row[0],
            'email': row[1],
            'reset_expiry': row[2]
        }
        
        return user
    finally:
        conn.close()


# 初始化数据库
if __name__ == "__main__":
    init_db()
