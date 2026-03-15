# encoding: utf-8
"""
小红书分享链接解析工具
支持从分享文本中提取笔记链接并解析出note_id和xsec_token
"""
import re
import urllib.parse
from typing import Tuple, Optional, Dict
from loguru import logger


class ShareLinkParser:
    """小红书分享链接解析器"""

    @staticmethod
    def extract_url_from_share_text(share_text: str) -> Optional[str]:
        """
        从分享文本中提取URL

        分享文本格式示例：
        10 【你和雪有一个共同点❄️ - 零小七 | 小红书 - 你的生活兴趣社区】 😆 MToXfDNgOqWn6u8 😆
        https://www.xiaohongshu.com/discovery/item/695f873a00000000210308ce?source=webshare...

        :param share_text: 分享文本
        :return: 提取的URL，如果没找到返回None
        """
        try:
            # 匹配小红书URL（支持多种路径格式）
            url_patterns = [
                r'https?://www\.xiaohongshu\.com/discovery/item/([a-zA-Z0-9]+)(\?[^\s]*)?',
                r'https?://www\.xiaohongshu\.com/explore/([a-zA-Z0-9]+)(\?[^\s]*)?',
                r'https?://xhslink\.com/[^\s]+',  # 短链接
            ]

            for pattern in url_patterns:
                match = re.search(pattern, share_text)
                if match:
                    url = match.group(0)
                    logger.info(f"✅ 从分享文本中提取到URL: {url}")
                    return url

            logger.warning("⚠️ 未在分享文本中找到小红书链接")
            return None

        except Exception as e:
            logger.error(f"❌ 提取URL失败: {e}")
            return None

    @staticmethod
    def parse_note_url(url: str) -> Dict[str, str]:
        """
        解析笔记URL，提取关键参数

        :param url: 笔记URL
        :return: 包含note_id, xsec_token, xsec_source等信息的字典
        """
        try:
            # 解析URL
            parsed_url = urllib.parse.urlparse(url)

            # 提取note_id（从路径中）
            # 支持两种路径格式：
            # - /discovery/item/{note_id}
            # - /explore/{note_id}
            path_parts = parsed_url.path.split('/')
            note_id = path_parts[-1] if path_parts else None

            if not note_id:
                logger.error("❌ 无法从URL中提取note_id")
                return {}

            # 解析查询参数
            query_params = urllib.parse.parse_qs(parsed_url.query)

            # 提取参数（parse_qs返回的是列表，需要取第一个元素）
            xsec_token = query_params.get('xsec_token', [''])[0]
            xsec_source = query_params.get('xsec_source', ['pc_share'])[0]
            source = query_params.get('source', [''])[0]

            # 构建标准的explore格式URL（用于get_note_info），对xsec_token做URL编码以保留特殊字符
            if xsec_token:
                encoded_token = urllib.parse.quote(xsec_token, safe='')
                explore_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={encoded_token}&xsec_source={xsec_source}"
            else:
                explore_url = f"https://www.xiaohongshu.com/explore/{note_id}"

            result = {
                'note_id': note_id,
                'xsec_token': xsec_token,
                'xsec_source': xsec_source,
                'source': source,
                'original_url': url,
                'explore_url': explore_url
            }

            logger.info(f"✅ 解析URL成功:")
            logger.info(f"   Note ID: {note_id}")
            logger.info(f"   xsec_token: {xsec_token[:20]}..." if xsec_token else "   xsec_token: (空)")
            logger.info(f"   xsec_source: {xsec_source}")

            return result

        except Exception as e:
            logger.error(f"❌ 解析URL失败: {e}")
            return {}

    @staticmethod
    def parse_share_link(share_text: str) -> Dict[str, str]:
        """
        一站式解析分享链接

        :param share_text: 分享文本或直接URL
        :return: 包含笔记信息的字典
        """
        # 如果已经是URL格式，直接解析
        if share_text.strip().startswith('http'):
            return ShareLinkParser.parse_note_url(share_text.strip())

        # 否则先提取URL
        url = ShareLinkParser.extract_url_from_share_text(share_text)
        if url:
            return ShareLinkParser.parse_note_url(url)
        else:
            logger.error("❌ 无法从分享文本中提取URL")
            return {}

    @staticmethod
    def extract_title_from_share_text(share_text: str) -> Optional[str]:
        """
        从分享文本中提取标题

        示例: "10 【你和雪有一个共同点❄️ - 零小七 | 小红书...】"
        提取: "你和雪有一个共同点❄️"

        :param share_text: 分享文本
        :return: 提取的标题，如果没找到返回None
        """
        try:
            # 匹配【】中的内容
            match = re.search(r'【([^】]+?)(?:\s*-\s*[^】]*)?】', share_text)
            if match:
                title = match.group(1).strip()
                logger.info(f"✅ 提取到标题: {title}")
                return title
            return None
        except Exception as e:
            logger.error(f"❌ 提取标题失败: {e}")
            return None

    @staticmethod
    def extract_author_from_share_text(share_text: str) -> Optional[str]:
        """
        从分享文本中提取作者昵称

        示例: "【你和雪有一个共同点❄️ - 零小七 | 小红书...】"
        提取: "零小七"

        :param share_text: 分享文本
        :return: 提取的作者昵称，如果没找到返回None
        """
        try:
            # 匹配 "- 作者名" 模式
            match = re.search(r'-\s*([^|】]+?)\s*\|', share_text)
            if match:
                author = match.group(1).strip()
                logger.info(f"✅ 提取到作者: {author}")
                return author
            return None
        except Exception as e:
            logger.error(f"❌ 提取作者失败: {e}")
            return None


if __name__ == '__main__':
    # 测试代码
    parser = ShareLinkParser()

    # 测试1: 完整的分享文本
    share_text1 = """10 【你和雪有一个共同点❄️ - 零小七 | 小红书 - 你的生活兴趣社区】 😆 MToXfDNgOqWn6u8 😆 https://www.xiaohongshu.com/discovery/item/695f873a00000000210308ce?source=webshare&xhsshare=pc_web&xsec_token=ABdxNbkUmzWUODXZAnB8SQ5WxoG5BNnNoFy__fqkK76ro=&xsec_source=pc_share"""

    print("=" * 60)
    print("测试1: 解析完整分享文本")
    print("=" * 60)
    result1 = parser.parse_share_link(share_text1)
    print(f"结果: {result1}")

    title1 = parser.extract_title_from_share_text(share_text1)
    print(f"标题: {title1}")

    author1 = parser.extract_author_from_share_text(share_text1)
    print(f"作者: {author1}")

    # 测试2: 直接URL
    url2 = "https://www.xiaohongshu.com/explore/695f873a00000000210308ce?xsec_token=ABdxNbkUmzWUODXZAnB8SQ5WxoG5BNnNoFy__fqkK76ro=&xsec_source=pc_share"

    print("\n" + "=" * 60)
    print("测试2: 解析直接URL")
    print("=" * 60)
    result2 = parser.parse_share_link(url2)
    print(f"结果: {result2}")
