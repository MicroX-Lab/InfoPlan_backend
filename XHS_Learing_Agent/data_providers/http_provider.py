from typing import List, Optional
from loguru import logger
import requests
from model_service.interfaces import DataProvider, NoteInfo


class HTTPDataProvider(DataProvider):
    """通过HTTP API获取数据的提供者（用于跨服务器调用）"""
    
    def __init__(self, spider_api_url: str, timeout: int = 30):
        """
        初始化HTTP数据提供者
        :param spider_api_url: 爬虫服务的API地址，例如: "http://192.168.1.100:5001"
        :param timeout: 请求超时时间（秒）
        """
        self.spider_api_url = spider_api_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"✅ 初始化HTTP数据提供者，爬虫服务地址: {self.spider_api_url}")
    
    def _check_health(self) -> bool:
        """检查爬虫服务是否可用"""
        try:
            response = requests.get(
                f"{self.spider_api_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"爬虫服务健康检查失败: {e}")
            return False
    
    def get_user_notes(self, user_ids: List[str], max_notes_per_user: int = 20) -> List[NoteInfo]:
        """
        通过HTTP API获取指定用户的笔记列表
        :param user_ids: 用户ID列表
        :param max_notes_per_user: 每个用户最多获取的笔记数
        :return: 笔记列表
        """
        # 检查服务健康状态
        if not self._check_health():
            logger.error("爬虫服务不可用")
            return []
        
        try:
            # 调用爬虫API
            url = f"{self.spider_api_url}/api/users/notes"
            payload = {
                "user_ids": user_ids[:5],  # 限制最多5个用户
                "max_users": 5,
                "notes_per_user": max_notes_per_user
            }
            
            logger.info(f"正在从爬虫服务获取笔记: {len(user_ids)}个用户")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    notes_data = result.get('data', {}).get('notes', [])
                    
                    # 转换为NoteInfo对象
                    notes = []
                    for note_data in notes_data:
                        try:
                            note = NoteInfo(
                                note_id=note_data.get('note_id', ''),
                                title=note_data.get('title', ''),
                                desc=note_data.get('desc', ''),
                                type=note_data.get('type', 'normal'),
                                liked_count=note_data.get('liked_count', 0),
                                collected_count=note_data.get('collected_count', 0),
                                comment_count=note_data.get('comment_count', 0),
                                user_id=note_data.get('user_id', ''),
                                nickname=note_data.get('nickname', ''),
                                tags=note_data.get('tags', [])
                            )
                            notes.append(note)
                        except Exception as e:
                            logger.warning(f"转换笔记数据失败: {e}")
                            continue
                    
                    logger.info(f"✅ 从爬虫服务获取到 {len(notes)} 条笔记")
                    return notes
                else:
                    logger.error(f"爬虫服务返回错误: {result.get('msg')}")
                    return []
            else:
                logger.error(f"爬虫服务请求失败: HTTP {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error("请求爬虫服务超时")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"请求爬虫服务失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取用户笔记时出错: {e}", exc_info=True)
            return []
    
    def get_note_detail(self, note_id: str) -> Optional[NoteInfo]:
        """
        获取笔记详细信息（通过HTTP API）
        注意：如果爬虫服务没有提供此接口，可以返回None
        """
        # 如果爬虫服务没有提供获取单个笔记详情的接口，返回None
        logger.warning("HTTP数据提供者暂不支持获取单个笔记详情")
        return None