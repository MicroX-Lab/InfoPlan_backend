# encoding: utf-8
"""
小红书爬虫API服务，负责所有数据获取功能
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from apis.auth_apis import (
    register_api, verify_email_api, login_api,
    request_reset_password_api, reset_password_api
)
from xhs_utils.common_util import load_env
from xhs_utils.note_fetcher import NoteFetcher
from xhs_utils.share_link_parser import ShareLinkParser
from xhs_utils.data_util import handle_note_info
from auth.email import init_mail
from typing import Optional

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化邮件服务
init_mail(app)

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


# @app.route('/api/user/notes/<user_id>', methods=['GET'])
# def get_user_notes_single(user_id: str):
#     """
#     获取单个用户的所有笔记（简化版）
#     查询参数:
#     - limit: 限制返回数量，默认20
#     """
#     try:
#         limit = request.args.get('limit', 20, type=int)
        
#         logger.info(f'收到获取用户笔记请求: user_id={user_id}, limit={limit}')
        
#         # 构建用户URL
#         user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
        
#         # 获取用户所有笔记
#         success, msg, notes = xhs_apis.get_user_all_notes(user_url, cookies_str)
        
#         if success and notes:
#             # 限制数量
#             notes = notes[:limit]
            
#             # 转换为标准格式
#             formatted_notes = []
#             for note_data in notes:
#                 formatted_notes.append({
#                     "note_id": note_data.get('note_id', ''),
#                     "title": note_data.get('display_title', note_data.get('title', '')),
#                     "desc": note_data.get('desc', ''),
#                     "type": note_data.get('type', 'normal'),
#                     "user_id": user_id
#                 })
            
#             return jsonify({
#                 "success": True,
#                 "msg": "获取笔记成功",
#                 "data": {
#                     "notes": formatted_notes,
#                     "count": len(formatted_notes)
#                 }
#             }), 200
#         else:
#             return jsonify({
#                 "success": False,
#                 "msg": msg or "获取笔记失败",
#                 "data": None
#             }), 500
            
#     except Exception as e:
#         logger.error(f'获取用户笔记接口错误: {str(e)}', exc_info=True)
#         return jsonify({
#             "success": False,
#             "msg": f"服务器错误: {str(e)}",
#             "data": None
#         }), 500


@app.route('/api/user/notes/<user_id>', methods=['GET'])
def get_user_notes_single(user_id: str):
    """
    获取单个用户的所有笔记
    查询参数:
    - limit: 限制返回数量，默认20
    - search_keyword: 可选，用于搜索用户获取xsec_token的关键词
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        search_keyword = request.args.get('search_keyword', None)
        
        logger.info(f'收到获取用户笔记请求: user_id={user_id}, limit={limit}')
        
        # 构建用户URL
        user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
        
        # 如果提供了搜索关键词，尝试获取完整URL（包含xsec_token）
        if search_keyword:
            try:
                # 搜索用户获取xsec_token
                success_search, msg_search, res_json = xhs_apis.search_user(
                    search_keyword, cookies_str, page=1
                )
                if success_search and res_json:
                    users = res_json.get('data', {}).get('users', [])
                    for user in users:
                        if user.get('id') == user_id:
                            xsec_token = user.get('xsec_token', '')
                            if xsec_token:
                                user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token={xsec_token}&xsec_source=pc_search"
                                logger.info(f"✅ 通过搜索获取到完整URL")
                                break
            except Exception as e:
                logger.warning(f"搜索用户获取token失败: {e}，将使用基础URL")
        
        # 获取用户所有笔记
        success, msg, all_note_info = xhs_apis.get_user_all_notes(user_url, cookies_str)
        
        if success:
            logger.info(f'用户 {user_id} 作品数量: {len(all_note_info)}')
            
            # 限制数量
            all_note_info = all_note_info[:limit]
            
            # 转换为标准格式（按照main.py的方式遍历）
            formatted_notes = []
            for simple_note_info in all_note_info:
                try:
                    # 按照main.py的方式获取字段
                    note_id = simple_note_info.get('note_id', '')
                    xsec_token = simple_note_info.get('xsec_token', '')
                    
                    if note_id:
                        formatted_notes.append({
                            "note_id": note_id,
                            "title": simple_note_info.get('display_title', simple_note_info.get('title', '无标题')),
                            "desc": simple_note_info.get('desc', ''),
                            "type": simple_note_info.get('type', 'normal'),
                            "user_id": user_id,
                            "xsec_token": xsec_token,
                            "note_url": f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_user" if xsec_token else f"https://www.xiaohongshu.com/explore/{note_id}"
                        })
                except Exception as e:
                    logger.warning(f'处理笔记数据时出错: {e}')
                    continue
            
            return jsonify({
                "success": True,
                "msg": "获取笔记成功",
                "data": {
                    "notes": formatted_notes,
                    "count": len(formatted_notes),
                    "total": len(all_note_info) if isinstance(all_note_info, list) else 0
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "msg": msg or "获取笔记失败",
                "data": None,
                "hint": "提示：可以尝试提供search_keyword参数来获取xsec_token"
            }), 500
            
    except Exception as e:
        logger.error(f'获取用户笔记接口错误: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


# 获取用户完整url的user_url

@app.route('/api/user/url/<user_id>', methods=['GET'])
def get_user_url_with_token(user_id: str):
    """
    通过用户ID获取包含xsec_token的完整URL
    查询参数:
    - search_keyword: 搜索关键词（用于搜索用户）
    """
    try:
        search_keyword = request.args.get('search_keyword', None)
        
        logger.info(f'收到获取用户URL请求: user_id={user_id}')
        
        # 基础URL
        base_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
        
        # 如果提供了搜索关键词，尝试获取完整URL
        if search_keyword:
            try:
                success, msg, res_json = xhs_apis.search_user(
                    search_keyword, cookies_str, page=1
                )
                
                if success and res_json:
                    users = res_json.get('data', {}).get('users', [])
                    
                    # 查找匹配的用户
                    for user in users:
                        if user.get('id') == user_id:
                            xsec_token = user.get('xsec_token', '')
                            if xsec_token:
                                full_url = f"{base_url}?xsec_token={xsec_token}&xsec_source=pc_search"
                                return jsonify({
                                    "success": True,
                                    "msg": "获取完整URL成功",
                                    "data": {
                                        "user_id": user_id,
                                        "base_url": base_url,
                                        "full_url": full_url,
                                        "xsec_token": xsec_token
                                    }
                                }), 200
                    
                    return jsonify({
                        "success": False,
                        "msg": "未在搜索结果中找到该用户",
                        "data": {
                            "user_id": user_id,
                            "base_url": base_url
                        }
                    }), 404
                else:
                    return jsonify({
                        "success": False,
                        "msg": f"搜索失败: {msg}",
                        "data": {
                            "user_id": user_id,
                            "base_url": base_url
                        }
                    }), 500
            except Exception as e:
                logger.error(f"搜索用户失败: {e}")
                return jsonify({
                    "success": False,
                    "msg": f"搜索用户时出错: {str(e)}",
                    "data": {
                        "user_id": user_id,
                        "base_url": base_url
                    }
                }), 500
        else:
            # 没有提供搜索关键词，返回基础URL
            return jsonify({
                "success": True,
                "msg": "返回基础URL（未提供search_keyword）",
                "data": {
                    "user_id": user_id,
                    "base_url": base_url,
                    "full_url": base_url,
                    "hint": "可以提供search_keyword参数来获取包含xsec_token的完整URL"
                }
            }), 200
            
    except Exception as e:
        logger.error(f'获取用户URL接口错误: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route('/api/note/share', methods=['POST'])
def get_note_by_share_link():
    """
    通过分享链接获取笔记详情
    请求参数（JSON）:
    {
        "share_link": "分享链接或分享文本",
        "get_comments": false  # 可选，是否获取评论，默认false
    }

    返回格式:
    {
        "success": true,
        "msg": "获取笔记成功",
        "data": {
            "note_id": "...",
            "title": "...",
            "desc": "...",
            "type": "normal",
            "user": {
                "user_id": "...",
                "nickname": "..."
            },
            "interact_info": {
                "liked_count": 100,
                "collected_count": 50,
                "comment_count": 10
            },
            "tags": ["tag1", "tag2"],
            "images": [...],
            "video": {...}
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

        share_link = data.get('share_link', '')
        if not share_link:
            return jsonify({
                "success": False,
                "msg": "share_link 参数不能为空",
                "data": None
            }), 400

        get_comments = data.get('get_comments', False)

        logger.info(f'收到通过分享链接获取笔记请求: {share_link[:100]}...')

        # 1. 解析分享链接
        parser = ShareLinkParser()
        parsed_info = parser.parse_share_link(share_link)

        if not parsed_info or not parsed_info.get('note_id'):
            return jsonify({
                "success": False,
                "msg": "无法解析分享链接，请检查链接格式",
                "data": None,
                "hint": "支持的格式: https://www.xiaohongshu.com/discovery/item/{note_id} 或 https://www.xiaohongshu.com/explore/{note_id}"
            }), 400

        note_id = parsed_info['note_id']
        explore_url = parsed_info['explore_url']

        logger.info(f'解析成功: note_id={note_id}')

        # 2. 获取笔记详情
        success, msg, note_info = xhs_apis.get_note_info(explore_url, cookies_str)

        if not success:
            return jsonify({
                "success": False,
                "msg": f"获取笔记失败: {msg}",
                "data": None,
                "hint": "可能原因：1) 笔记不存在或已删除 2) xsec_token过期 3) Cookie失效"
            }), 500

        # 检查API业务层返回是否成功
        if note_info and not note_info.get('success', True):
            api_msg = note_info.get('msg', '未知错误')
            api_code = note_info.get('code', 0)
            logger.warning(f'小红书API返回业务错误: code={api_code}, msg={api_msg}')
            return jsonify({
                "success": False,
                "msg": f"小红书API返回错误: {api_msg}",
                "data": None,
                "hint": "可能原因：1) Cookie已过期，请更新cookies 2) 笔记不存在或已删除 3) xsec_token过期"
            }), 500

        # 3. 处理笔记数据
        try:
            items = note_info.get('data', {}).get('items', [])
            if not items or len(items) == 0:
                return jsonify({
                    "success": False,
                    "msg": "笔记数据为空",
                    "data": None
                }), 404

            note_data = items[0]
            note_data['url'] = explore_url

            # 使用data_util处理笔记信息
            handled_note = handle_note_info(note_data)

            # 添加解析的额外信息
            handled_note['parsed_info'] = {
                'note_id': note_id,
                'xsec_token': parsed_info.get('xsec_token', ''),
                'xsec_source': parsed_info.get('xsec_source', ''),
                'original_share_link': share_link[:200] if len(share_link) > 200 else share_link
            }

            # 4. 如果需要获取评论
            if get_comments:
                try:
                    xsec_token = parsed_info.get('xsec_token', '')
                    if xsec_token:
                        logger.info(f'正在获取笔记评论...')
                        success_comment, msg_comment, comments = xhs_apis.get_note_all_out_comment(
                            note_id, xsec_token, cookies_str
                        )
                        if success_comment:
                            handled_note['comments'] = comments
                            handled_note['comments_count'] = len(comments)
                            logger.info(f'成功获取 {len(comments)} 条评论')
                        else:
                            logger.warning(f'获取评论失败: {msg_comment}')
                            handled_note['comments'] = []
                            handled_note['comments_error'] = msg_comment
                    else:
                        handled_note['comments'] = []
                        handled_note['comments_error'] = "缺少xsec_token，无法获取评论"
                except Exception as e:
                    logger.error(f'获取评论时出错: {e}')
                    handled_note['comments'] = []
                    handled_note['comments_error'] = str(e)

            return jsonify({
                "success": True,
                "msg": "获取笔记成功",
                "data": handled_note
            }), 200

        except Exception as e:
            logger.error(f'处理笔记数据时出错: {e}', exc_info=True)
            return jsonify({
                "success": False,
                "msg": f"处理笔记数据失败: {str(e)}",
                "data": None
            }), 500

    except Exception as e:
        logger.error(f'通过分享链接获取笔记接口错误: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route('/api/note/parse', methods=['POST'])
def parse_share_link_only():
    """
    仅解析分享链接，不获取笔记详情
    请求参数（JSON）:
    {
        "share_link": "分享链接或分享文本"
    }

    返回格式:
    {
        "success": true,
        "msg": "解析成功",
        "data": {
            "note_id": "...",
            "xsec_token": "...",
            "xsec_source": "...",
            "explore_url": "...",
            "title": "...",  # 从分享文本提取
            "author": "..."  # 从分享文本提取
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

        share_link = data.get('share_link', '')
        if not share_link:
            return jsonify({
                "success": False,
                "msg": "share_link 参数不能为空",
                "data": None
            }), 400

        logger.info(f'收到解析分享链接请求: {share_link[:100]}...')

        # 解析分享链接
        parser = ShareLinkParser()
        parsed_info = parser.parse_share_link(share_link)

        if not parsed_info or not parsed_info.get('note_id'):
            return jsonify({
                "success": False,
                "msg": "无法解析分享链接，请检查链接格式",
                "data": None
            }), 400

        # 尝试从分享文本中提取标题和作者
        title = parser.extract_title_from_share_text(share_link)
        author = parser.extract_author_from_share_text(share_link)

        if title:
            parsed_info['title'] = title
        if author:
            parsed_info['author'] = author

        return jsonify({
            "success": True,
            "msg": "解析成功",
            "data": parsed_info
        }), 200

    except Exception as e:
        logger.error(f'解析分享链接接口错误: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


# 认证相关路由
@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册接口"""
    return register_api()


@app.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    """邮箱验证接口"""
    return verify_email_api()


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录接口"""
    return login_api()


@app.route('/api/auth/request-reset', methods=['POST'])
def request_reset():
    """请求重置密码接口"""
    return request_reset_password_api()


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """重置密码接口"""
    return reset_password_api()


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
    logger.info('认证相关接口:')
    logger.info('用户注册: POST /api/auth/register')
    logger.info('邮箱验证: POST /api/auth/verify-email')
    logger.info('用户登录: POST /api/auth/login')
    logger.info('请求重置密码: POST /api/auth/request-reset')
    logger.info('重置密码: POST /api/auth/reset-password')
    logger.info('')
    logger.info('爬虫相关接口:')
    logger.info('搜索用户: POST /api/search/user')
    logger.info('批量搜索用户: POST /api/search/user/batch')
    logger.info('获取用户笔记: POST /api/users/notes')
    logger.info('获取单个用户笔记: GET /api/user/notes/<user_id>')
    logger.info('获取用户URL: GET /api/user/url/<user_id>')
    logger.info('通过分享链接获取笔记: POST /api/note/share')
    logger.info('解析分享链接: POST /api/note/parse')
    logger.info('健康检查接口: GET /health')
    logger.info('=' * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)
