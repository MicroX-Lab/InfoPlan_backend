import json
import os
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import handle_note_info, download_note, save_to_xlsx


class Data_Spider():
    def __init__(self):
        self.xhs_apis = XHS_Apis()

    def spider_note(self, note_url: str, cookies_str: str, proxies=None):
        """
        爬取一个笔记的信息
        :param note_url:
        :param cookies_str:
        :return:
        """
        note_info = None
        try:
            success, msg, note_info = self.xhs_apis.get_note_info(note_url, cookies_str, proxies)
            if success:
                note_info = note_info['data']['items'][0]
                note_info['url'] = note_url
                note_info = handle_note_info(note_info)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取笔记信息 {note_url}: {success}, msg: {msg}')
        return success, msg, note_info

    def spider_some_note(self, notes: list, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes:
        :param cookies_str:
        :param base_path:
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        note_list = []
        for note_url in notes:
            success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
            if note_info is not None and success:
                note_list.append(note_info)
        for note_info in note_list:
            if save_choice == 'all' or 'media' in save_choice:
                download_note(note_info, base_path['media'], save_choice)
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(note_list, file_path)


    def spider_user_all_note(self, user_url: str, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一个用户的所有笔记
        :param user_url:
        :param cookies_str:
        :param base_path:
        :return:
        """
        note_list = []
        try:
            success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, cookies_str, proxies)
            if success:
                logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
                for simple_note_info in all_note_info:
                    note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = user_url.split('/')[-1].split('?')[0]
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取用户所有视频 {user_url}: {success}, msg: {msg}')
        return note_list, success, msg

    def spider_some_search_note(self, query: str, require_num: int, cookies_str: str, base_path: dict, save_choice: str, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo: dict = None,  excel_name: str = '', proxies=None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param base_path 保存路径
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            返回搜索的结果
        """
        note_list = []
        try:
            success, msg, notes = self.xhs_apis.search_some_note(query, require_num, cookies_str, sort_type_choice, note_type, note_time, note_range, pos_distance, geo, proxies)
            if success:
                notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
                for note in notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = query
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return note_list, success, msg

if __name__ == '__main__':
    """
        此文件为爬虫的入口文件，可以直接运行
        apis/xhs_pc_apis.py 为爬虫的api文件，包含小红书的全部数据接口，可以继续封装
        apis/xhs_creator_apis.py 为小红书创作者中心的api文件
        感谢star和follow
    """

    cookies_str, base_path = init()
    data_spider = Data_Spider()
    """
        save_choice: all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
        save_choice 为 excel 或者 all 时，excel_name 不能为空
    """

# ========== 测试搜索用户接口 ==========
logger.info("=" * 50)
logger.info("开始测试搜索用户接口")
logger.info("=" * 50)

# 测试搜索用户（单页）
search_query = "美食"
page = 1
logger.info(f"搜索关键词: {search_query}, 页码: {page}")

success, msg, res_json = data_spider.xhs_apis.search_user(search_query, cookies_str, page)

if success:
    logger.info(f"搜索成功！消息: {msg}")
    if res_json and 'data' in res_json:
        # 正确的数据路径：res_json['data']['users']
        users = res_json['data'].get('users', [])
        logger.info(f"找到 {len(users)} 个用户")
        
        # 打印前几个用户的信息（使用正确的字段名）
        for i, user in enumerate(users[:3], 1):
            logger.info(f"用户 {i}:")
            logger.info(f"  - 用户ID: {user.get('id', 'N/A')}")
            logger.info(f"  - 昵称: {user.get('name', 'N/A')}")
            logger.info(f"  - 小红书号: {user.get('red_id', 'N/A')}")
            logger.info(f"  - 简介: {user.get('sub_title', 'N/A')}")
            logger.info(f"  - 粉丝数: {user.get('fans', 'N/A')}")
            logger.info(f"  - 笔记数: {user.get('note_count', 'N/A')}")
            logger.info(f"  - 更新时间: {user.get('update_time', 'N/A')}")
            logger.info(f"  - 是否已关注: {'是' if user.get('followed', False) else '否'}")
            logger.info(f"  - 头像: {user.get('image', 'N/A')}")
            logger.info("-" * 30)
    else:
        logger.warning("返回数据格式异常")
        if res_json:
            logger.warning(f"返回数据: {res_json}")
else:
    logger.error(f"搜索失败: {msg}")

logger.info("=" * 50)

# 测试批量搜索用户（获取指定数量的用户）
logger.info("开始测试批量搜索用户接口")
logger.info("=" * 50)

require_num = 20
logger.info(f"搜索关键词: {search_query}, 需要数量: {require_num}")

success, msg, user_list = data_spider.xhs_apis.search_some_user(search_query, require_num, cookies_str)

if success:
    logger.info(f"批量搜索成功！消息: {msg}")
    logger.info(f"共获取 {len(user_list)} 个用户")
    
    # 打印用户统计信息（使用正确的字段名）
    if user_list:
        logger.info("\n用户列表预览（前5个）:")
        for i, user in enumerate(user_list[:5], 1):
            user_id = user.get('id', 'N/A')
            user_name = user.get('name', 'N/A')
            user_fans = user.get('fans', 'N/A')
            user_notes = user.get('note_count', 'N/A')
            logger.info(f"{i}. {user_name} (ID: {user_id}, 粉丝: {user_fans}, 笔记: {user_notes})")
        
        # 统计信息
        logger.info("\n统计信息:")
        total_followed = sum(1 for user in user_list if user.get('followed', False))
        logger.info(f"  - 已关注用户数: {total_followed}")
        logger.info(f"  - 未关注用户数: {len(user_list) - total_followed}")
        
        # 粉丝数统计（尝试解析）
        try:
            fans_list = []
            for user in user_list:
                fans_str = user.get('fans', '0')
                if '万' in fans_str:
                    fans_num = float(fans_str.replace('万', '')) * 10000
                else:
                    fans_num = float(fans_str) if fans_str.replace('.', '').isdigit() else 0
                fans_list.append(fans_num)
            
            if fans_list:
                avg_fans = sum(fans_list) / len(fans_list)
                max_fans = max(fans_list)
                min_fans = min(fans_list)
                logger.info(f"  - 平均粉丝数: {avg_fans/10000:.2f}万")
                logger.info(f"  - 最多粉丝数: {max_fans/10000:.2f}万")
                logger.info(f"  - 最少粉丝数: {min_fans/10000:.2f}万")
        except Exception as e:
            logger.warning(f"粉丝数统计失败: {e}")
else:
    logger.error(f"批量搜索失败: {msg}")

logger.info("=" * 50)
logger.info("搜索用户接口测试完成")
logger.info("=" * 50)

    # # ========== 测试获取用户信息接口 ==========
    # logger.info("\n" + "=" * 50)
    # logger.info("开始测试获取用户信息接口")
    # logger.info("=" * 50)
    
    # # 测试1: 获取用户自己的信息1 (get_user_self_info)
    # logger.info("\n【测试1】获取用户自己的信息1 (get_user_self_info)")
    # logger.info("-" * 50)
    # success, msg, res_json = data_spider.xhs_apis.get_user_self_info(cookies_str)
    
    # if success:
    #     logger.info(f"✅ 请求成功！消息: {msg}")
    #     if res_json and 'data' in res_json:
    #         user_data = res_json['data']
    #         logger.info("\n📋 用户信息详情:")
    #         logger.info(f"  - 用户ID: {user_data.get('user_id', 'N/A')}")
    #         logger.info(f"  - 昵称: {user_data.get('nickname', 'N/A')}")
    #         logger.info(f"  - 简介: {user_data.get('desc', 'N/A')}")
    #         logger.info(f"  - 头像: {user_data.get('imageb', 'N/A')}")
    #         logger.info(f"  - 粉丝数: {user_data.get('follows', 'N/A')}")
    #         logger.info(f"  - 关注数: {user_data.get('followed', 'N/A')}")
    #         logger.info(f"  - 获赞数: {user_data.get('liked', 'N/A')}")
    #         logger.info(f"  - 笔记数: {user_data.get('notes', 'N/A')}")
    #         logger.info(f"  - 收藏数: {user_data.get('collected', 'N/A')}")
            
    #         # 打印完整 JSON（格式化）
    #         logger.info("\n📄 完整返回数据:")
    #         logger.info(json.dumps(res_json, ensure_ascii=False, indent=2))
    #     else:
    #         logger.warning("⚠️ 返回数据格式异常")
    #         logger.info(f"返回内容: {res_json}")
    # else:
    #     logger.error(f"❌ 请求失败: {msg}")
    #     if res_json:
    #         logger.info(f"返回内容: {res_json}")
    
    # # 测试2: 获取用户自己的信息2 (get_user_self_info2)
    # logger.info("\n" + "-" * 50)
    # logger.info("【测试2】获取用户自己的信息2 (get_user_self_info2)")
    # logger.info("-" * 50)
    # success, msg, res_json = data_spider.xhs_apis.get_user_self_info2(cookies_str)
    
    # if success:
    #     logger.info(f"✅ 请求成功！消息: {msg}")
    #     if res_json and 'data' in res_json:
    #         user_data = res_json['data']
    #         logger.info("\n📋 用户信息详情:")
    #         logger.info(f"  - 用户ID: {user_data.get('id', 'N/A')}")
    #         logger.info(f"  - 昵称: {user_data.get('nickname', 'N/A')}")
    #         logger.info(f"  - 简介: {user_data.get('desc', 'N/A')}")
    #         logger.info(f"  - 头像: {user_data.get('imageb', 'N/A')}")
    #         logger.info(f"  - 粉丝数: {user_data.get('follows', 'N/A')}")
    #         logger.info(f"  - 关注数: {user_data.get('followed', 'N/A')}")
    #         logger.info(f"  - 获赞数: {user_data.get('liked', 'N/A')}")
    #         logger.info(f"  - 笔记数: {user_data.get('notes', 'N/A')}")
            
    #         # 打印完整 JSON（格式化）
    #         logger.info("\n📄 完整返回数据:")
    #         logger.info(json.dumps(res_json, ensure_ascii=False, indent=2))
    #     else:
    #         logger.warning("⚠️ 返回数据格式异常")
    #         logger.info(f"返回内容: {res_json}")
    # else:
    #     logger.error(f"❌ 请求失败: {msg}")
    #     if res_json:
    #         logger.info(f"返回内容: {res_json}")
    
    # # 测试3: 获取指定用户的信息 (get_user_info)
    # # 先从搜索结果中获取一个 user_id，或者使用一个示例 user_id
    # logger.info("\n" + "-" * 50)
    # logger.info("【测试3】获取指定用户的信息 (get_user_info)")
    # logger.info("-" * 50)
    
    # # 先搜索用户获取一个 user_id
    # test_user_id = None
    # search_query_for_user = "美食"
    # logger.info(f"先搜索关键词 '{search_query_for_user}' 获取一个用户ID...")
    
    # success, msg, search_res = data_spider.xhs_apis.search_user(search_query_for_user, cookies_str, page=1)
    # if success and search_res and 'data' in search_res:
    #     users = search_res['data'].get('users', [])
    #     if users:
    #         test_user_id = users[0].get('user_id')
    #         logger.info(f"✅ 找到用户ID: {test_user_id}")
    #         logger.info(f"   用户昵称: {users[0].get('nickname', 'N/A')}")
    #     else:
    #         logger.warning("⚠️ 搜索结果中没有找到用户，将使用示例 user_id")
    #         test_user_id = "64c3f392000000002b009e45"  # 示例 user_id
    # else:
    #     logger.warning("⚠️ 搜索失败，将使用示例 user_id")
    #     test_user_id = "64c3f392000000002b009e45"  # 示例 user_id
    
    # if test_user_id:
    #     logger.info(f"\n使用用户ID: {test_user_id} 进行测试")
    #     success, msg, res_json = data_spider.xhs_apis.get_user_info(test_user_id, cookies_str)
        
    #     if success:
    #         logger.info(f"✅ 请求成功！消息: {msg}")
    #         if res_json and 'data' in res_json:
    #             user_data = res_json['data']
    #             logger.info("\n📋 用户信息详情:")
    #             logger.info(f"  - 用户ID: {user_data.get('user_id', 'N/A')}")
    #             logger.info(f"  - 昵称: {user_data.get('nickname', 'N/A')}")
    #             logger.info(f"  - 简介: {user_data.get('desc', 'N/A')}")
    #             logger.info(f"  - 头像: {user_data.get('imageb', 'N/A')}")
    #             logger.info(f"  - 粉丝数: {user_data.get('follows', 'N/A')}")
    #             logger.info(f"  - 关注数: {user_data.get('followed', 'N/A')}")
    #             logger.info(f"  - 获赞数: {user_data.get('liked', 'N/A')}")
    #             logger.info(f"  - 笔记数: {user_data.get('notes', 'N/A')}")
    #             logger.info(f"  - 收藏数: {user_data.get('collected', 'N/A')}")
                
    #             # 打印完整 JSON（格式化）
    #             logger.info("\n📄 完整返回数据:")
    #             logger.info(json.dumps(res_json, ensure_ascii=False, indent=2))
    #         else:
    #             logger.warning("⚠️ 返回数据格式异常")
    #             logger.info(f"返回内容: {res_json}")
    #     else:
    #         logger.error(f"❌ 请求失败: {msg}")
    #         if res_json:
    #             logger.info(f"返回内容: {res_json}")
    # else:
    #     logger.error("❌ 无法获取测试用的 user_id")
    
    # logger.info("\n" + "=" * 50)
    # logger.info("获取用户信息接口测试完成")
    # logger.info("=" * 50)

    # # ========== 测试获取用户收藏笔记列表和关注列表 ==========
    # logger.info("\n" + "=" * 50)
    # logger.info("开始测试获取用户收藏笔记列表和关注列表")
    # logger.info("=" * 50)
    
    # # 先获取当前用户的 user_id
    # test_user_id = None
    # logger.info("\n【步骤1】获取当前用户的 user_id...")
    # success, msg, self_info = data_spider.xhs_apis.get_user_self_info2(cookies_str)
    
    # if success and self_info and 'data' in self_info:
    #     test_user_id = self_info['data'].get('user_id')
    #     logger.info(f"✅ 获取到当前用户ID: {test_user_id}")
    # else:
    #     logger.warning("⚠️ 无法获取当前用户ID，将使用示例 user_id")
    #     # 如果无法获取，尝试从搜索结果获取
    #     search_query_for_user = "美食"
    #     success, msg, search_res = data_spider.xhs_apis.search_user(search_query_for_user, cookies_str, page=1)
    #     if success and search_res and 'data' in search_res:
    #         users = search_res['data'].get('users', [])
    #         if users:
    #             test_user_id = users[0].get('user_id')
    #             logger.info(f"✅ 从搜索结果获取到用户ID: {test_user_id}")
    #         else:
    #             test_user_id = "65a75fca000000000803082a"  # 示例 user_id
    #     else:
    #         test_user_id = "65a75fca000000000803082a"  # 示例 user_id
    
    # if test_user_id:
    #     # 测试1: 获取用户收藏笔记列表（单页）
    #     logger.info("\n" + "-" * 50)
    #     logger.info("【测试1】获取用户收藏笔记列表（单页）")
    #     logger.info("-" * 50)
    #     logger.info(f"用户ID: {test_user_id}")
        
    #     success, msg, res_json = data_spider.xhs_apis.get_user_collect_notes(test_user_id, cookies_str)
        
    #     if success:
    #         logger.info(f"✅ 请求成功！消息: {msg}")
    #         if res_json and 'data' in res_json:
    #             data = res_json['data']
    #             notes = data.get('notes', [])
    #             logger.info(f"📋 找到 {len(notes)} 条收藏笔记")
                
    #             # 打印前几条笔记信息
    #             for i, note in enumerate(notes[:3], 1):
    #                 logger.info(f"\n收藏笔记 {i}:")
    #                 logger.info(f"  - 笔记ID: {note.get('note_id', 'N/A')}")
    #                 logger.info(f"  - 标题: {note.get('title', 'N/A')}")
    #                 logger.info(f"  - 类型: {note.get('type', 'N/A')}")
    #                 logger.info(f"  - 点赞数: {note.get('liked_count', 'N/A')}")
    #                 logger.info(f"  - 收藏数: {note.get('collected_count', 'N/A')}")
    #                 logger.info(f"  - 评论数: {note.get('comments_count', 'N/A')}")
                
    #             logger.info(f"\n📄 完整返回数据（前1000字符）:")
    #             json_str = json.dumps(res_json, ensure_ascii=False, indent=2)
    #             logger.info(json_str[:1000] + ("..." if len(json_str) > 1000 else ""))
    #         else:
    #             logger.warning("⚠️ 返回数据格式异常")
    #             logger.info(f"返回内容: {res_json}")
    #     else:
    #         logger.error(f"❌ 请求失败: {msg}")
    #         if res_json:
    #             logger.info(f"返回内容: {res_json}")
        
    #     # 测试2: 获取用户所有收藏笔记
    #     logger.info("\n" + "-" * 50)
    #     logger.info("【测试2】获取用户所有收藏笔记")
    #     logger.info("-" * 50)
    #     logger.info(f"用户ID: {test_user_id}")
        
    #     success, msg, note_list = data_spider.xhs_apis.get_user_all_collect_notes(test_user_id, cookies_str)
        
    #     if success:
    #         logger.info(f"✅ 请求成功！消息: {msg}")
    #         logger.info(f"📋 共获取 {len(note_list)} 条收藏笔记")
            
    #         if note_list:
    #             logger.info("\n收藏笔记列表预览（前5条）:")
    #             for i, note in enumerate(note_list[:5], 1):
    #                 logger.info(f"{i}. {note.get('display_title', 'N/A')} (ID: {note.get('note_id', 'N/A')})")
    #     else:
    #         logger.error(f"❌ 请求失败: {msg}")
    
    # else:
    #     logger.error("❌ 无法获取测试用的 user_id")
    
    # logger.info("\n" + "=" * 50)
    # logger.info("获取用户收藏笔记列表和关注列表测试完成")
    # logger.info("=" * 50)

    # ========== 以下为原有测试代码（已注释） ==========
    # # 1 爬取列表的所有笔记信息 笔记链接 如下所示 注意此url会过期！
    # notes = [
    #     r'https://www.xiaohongshu.com/explore/683fe17f0000000023017c6a?xsec_token=ABBr_cMzallQeLyKSRdPk9fwzA0torkbT_ubuQP1ayvKA=&xsec_source=pc_user',
    # ]
    # data_spider.spider_some_note(notes, cookies_str, base_path, 'all', 'test')

    # # 2 爬取用户的所有笔记信息 用户链接 如下所示 注意此url会过期！
    # user_url = 'https://www.xiaohongshu.com/user/profile/64c3f392000000002b009e45?xsec_token=AB-GhAToFu07JwNk_AMICHnp7bSTjVz2beVIDBwSyPwvM=&xsec_source=pc_feed'
    # data_spider.spider_user_all_note(user_url, cookies_str, base_path, 'all')

    # # 3 搜索指定关键词的笔记
    # query = "榴莲"
    # query_num = 10
    # sort_type_choice = 0  # 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
    # note_type = 0 # 0 不限, 1 视频笔记, 2 普通笔记
    # note_time = 0  # 0 不限, 1 一天内, 2 一周内天, 3 半年内
    # note_range = 0  # 0 不限, 1 已看过, 2 未看过, 3 已关注
    # pos_distance = 0  # 0 不限, 1 同城, 2 附近 指定这个1或2必须要指定 geo
    # # geo = {
    # #     # 经纬度
    # #     "latitude": 39.9725,
    # #     "longitude": 116.4207
    # # }
    # data_spider.spider_some_search_note(query, query_num, cookies_str, base_path, 'all', sort_type_choice, note_type, note_time, note_range, pos_distance, geo=None)
