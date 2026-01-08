# xhs_utils/note_fetcher.py

from typing import List, Dict
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.data_util import handle_note_info


class NoteFetcher:
    """笔记获取工具类"""
    
    def __init__(self, cookies_str: str):
        """
        初始化笔记获取器
        :param cookies_str: Cookie字符串
        """
        self.cookies_str = cookies_str
        self.xhs_apis = XHS_Apis()
    
    def get_users_latest_notes(
        self, 
        user_ids: List[str], 
        max_users: int = 5, 
        notes_per_user: int = 5
    ) -> List[Dict]:
        """
        获取多个用户的最新笔记
        :param user_ids: 用户ID列表
        :param max_users: 最多处理几个用户（默认5个）
        :param notes_per_user: 每个用户获取几条笔记（默认5条）
        :return: 笔记列表
        """
        all_notes = []
        processed_users = 0
        
        for user_id in user_ids:
            if processed_users >= max_users:
                break
            
            try:
                logger.info(f"正在获取用户 {user_id} 的最新 {notes_per_user} 条笔记...")
                
                # 构建用户URL
                user_url = self._build_user_url(user_id)
                
                # 获取用户所有笔记
                success, msg, notes = self.xhs_apis.get_user_all_notes(
                    user_url, self.cookies_str
                )
                
                if success and notes:
                    # 取最新的notes_per_user条
                    latest_notes = notes[:notes_per_user]
                    
                    # 获取每条笔记的详细信息
                    for note_data in latest_notes:
                        note_id = note_data.get('note_id', '')
                        xsec_token = note_data.get('xsec_token', '')
                        
                        # 构建笔记URL
                        note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_user"
                        
                        # 获取笔记详细信息
                        note_detail = self._get_note_detail(note_url)
                        if note_detail:
                            note_detail['user_id'] = user_id
                            all_notes.append(note_detail)
                    
                    logger.info(f"✅ 用户 {user_id} 获取到 {len(latest_notes)} 条笔记")
                    processed_users += 1
                else:
                    logger.warning(f"⚠️ 获取用户 {user_id} 的笔记失败: {msg}")
                    
            except Exception as e:
                logger.error(f"❌ 处理用户 {user_id} 时出错: {e}")
                continue
        
        logger.info(f"📝 共获取到 {len(all_notes)} 条笔记（来自 {processed_users} 个用户）")
        return all_notes
    
    def _build_user_url(self, user_id: str) -> str:
        """构建用户URL"""
        # 如果已经是完整URL，直接返回
        if user_id.startswith('http'):
            return user_id
        
        # 否则构建URL（需要xsec_token，这里先简化）
        return f"https://www.xiaohongshu.com/user/profile/{user_id}"
    
    def _get_note_detail(self, note_url: str) -> Optional[Dict]:
        """获取笔记详细信息"""
        try:
            success, msg, note_info = self.xhs_apis.get_note_info(
                note_url, self.cookies_str
            )
            
            if success and note_info:
                items = note_info.get('data', {}).get('items', [])
                if items:
                    note_data = items[0]
                    note_data['url'] = note_url
                    handled_note = handle_note_info(note_data)
                    return handled_note
        except Exception as e:
            logger.error(f"获取笔记详情失败 {note_url}: {e}")
        
        return None