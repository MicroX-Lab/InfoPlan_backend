# encoding: utf-8
"""
小红书爬虫API服务（整合版）
部署在服务器A，负责所有数据获取功能
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env
from xhs_utils.note_fetcher import NoteFetcher
from typing import Optional

app = Flask(__name__)
CORS(app)  # 允许跨域请求

xhs_apis = XHS_Apis()

# 从环境变量加载 cookies
cookies_str = load_env()


@app.route('/api/search/user', methods=['POST'])
def search_user_api():
    """
    搜索用户接口
    请求参数（JSON）:
    {
        "query": "搜索关键词",
        "page": 1,  # 可选，默认为1
        "proxies": {}  # 可选，代理设置
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        query = data.get('query')
        if not query:
            return jsonify({
                "success": False,
                "msg": "query 参数不能为空",
                "data": None
            }), 400
        
        page = data.get('page', 1)
        proxies = data.get('proxies', None)
        
        logger.info(f'收到搜索用户请求: query={query}, page={page}')
        
        success, msg, res_json = xhs_apis.search_user(query, cookies_str, page, proxies)
        
        if success:
            return jsonify({
                "success": True,
                "msg": msg,
                "data": res_json.get('data', {}) if res_json else {}
            }), 200
        else:
            return jsonify({
                "success": False,
                "msg": msg,
                "data": None
            }), 500
            
    except Exception as e:
        logger.error(f'搜索用户接口错误: {str(e)}')
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route('/api/search/user/batch', methods=['POST'])
def search_user_batch_api():
    """
    批量搜索用户接口（获取指定数量的用户）
    请求参数（JSON）:
    {
        "query": "搜索关键词",
        "require_num": 15,  # 需要获取的用户数量
        "proxies": {}  # 可选，代理设置
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        query = data.get('query')
        if not query:
            return jsonify({
                "success": False,
                "msg": "query 参数不能为空",
                "data": None
            }), 400
        
        require_num = data.get('require_num', 15)
        proxies = data.get('proxies', None)
        
        logger.info(f'收到批量搜索用户请求: query={query}, require_num={require_num}')
        
        success, msg, user_list = xhs_apis.search_some_user(query, require_num, cookies_str, proxies)
        
        if success:
            return jsonify({
                "success": True,
                "msg": msg,
                "data": {
                    "users": user_list,
                    "count": len(user_list)
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "msg": msg,
                "data": None
            }), 500
            
    except Exception as e:
        logger.error(f'批量搜索用户接口错误: {str(e)}')
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route('/api/users/notes', methods=['POST'])
def get_users_notes():
    """
    获取多个用户的最新笔记接口
    请求参数（JSON）:
    {
        "user_ids": ["user_id1", "user_id2", ...],
        "max_users": 5,  # 可选，最多处理几个用户，默认5
        "notes_per_user": 5  # 可选，每个用户获取几条笔记，默认5
    }
    
    返回格式:
    {
        "success": true,
        "msg": "获取笔记成功",
        "data": {
            "notes": [
                {
                    "note_id": "...",
                    "title": "...",
                    "desc": "...",
                    "type": "normal",
                    "liked_count": 100,
                    "collected_count": 50,
                    "comment_count": 10,
                    "user_id": "...",
                    "nickname": "...",
                    "tags": ["tag1", "tag2"]
                },
                ...
            ],
            "count": 25,
            "users_processed": 5
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        user_ids = data.get('user_ids', [])
        if not user_ids:
            return jsonify({
                "success": False,
                "msg": "user_ids 参数不能为空",
                "data": None
            }), 400
        
        max_users = data.get('max_users', 5)
        notes_per_user = data.get('notes_per_user', 5)
        
        logger.info(f'收到获取用户笔记请求: {len(user_ids)}个用户')
        
        # 限制用户数量
        user_ids = user_ids[:max_users]
        
        # 获取笔记
        fetcher = NoteFetcher(cookies_str)
        notes = fetcher.get_users_latest_notes(user_ids, max_users, notes_per_user)
        
        # 转换为标准格式
        formatted_notes = []
        for note in notes:
            formatted_notes.append({
                "note_id": note.get('note_id', ''),
                "title": note.get('title', ''),
                "desc": note.get('desc', ''),
                "type": note.get('note_type', 'normal'),
                "liked_count": note.get('liked_count', 0),
                "collected_count": note.get('collected_count', 0),
                "comment_count": note.get('comment_count', 0),
                "user_id": note.get('user_id', ''),
                "nickname": note.get('nickname', ''),
                "tags": note.get('tags', [])
            })
        
        return jsonify({
            "success": True,
            "msg": "获取笔记成功",
            "data": {
                "notes": formatted_notes,
                "count": len(formatted_notes),
                "users_processed": min(len(user_ids), max_users)
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取用户笔记接口错误: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route('/api/user/notes/<user_id>', methods=['GET'])
def get_user_notes_single(user_id: str):
    """
    获取单个用户的所有笔记（简化版）
    查询参数:
    - limit: 限制返回数量，默认20
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        
        logger.info(f'收到获取用户笔记请求: user_id={user_id}, limit={limit}')
        
        # 构建用户URL
        user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
        
        # 获取用户所有笔记
        success, msg, notes = xhs_apis.get_user_all_notes(user_url, cookies_str)
        
        if success and notes:
            # 限制数量
            notes = notes[:limit]
            
            # 转换为标准格式
            formatted_notes = []
            for note_data in notes:
                formatted_notes.append({
                    "note_id": note_data.get('note_id', ''),
                    "title": note_data.get('display_title', note_data.get('title', '')),
                    "desc": note_data.get('desc', ''),
                    "type": note_data.get('type', 'normal'),
                    "user_id": user_id
                })
            
            return jsonify({
                "success": True,
                "msg": "获取笔记成功",
                "data": {
                    "notes": formatted_notes,
                    "count": len(formatted_notes)
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "msg": msg or "获取笔记失败",
                "data": None
            }), 500
            
    except Exception as e:
        logger.error(f'获取用户笔记接口错误: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "service": "XHS Spider Service",
        "message": "爬虫服务运行正常"
    }), 200


if __name__ == '__main__':
    logger.info('=' * 60)
    logger.info('启动小红书爬虫API服务（服务器A）')
    logger.info('=' * 60)
    logger.info('搜索用户接口: POST /api/search/user')
    logger.info('批量搜索用户接口: POST /api/search/user/batch')
    logger.info('获取用户笔记接口: POST /api/users/notes')
    logger.info('获取单个用户笔记: GET /api/user/notes/<user_id>')
    logger.info('健康检查接口: GET /health')
    logger.info('=' * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)