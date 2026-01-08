"""
爬虫服务API测试脚本
测试服务器A (8.155.168.11:5001) 的所有接口
"""

import requests
import json
import time
from typing import Dict, Any
from loguru import logger

# 配置
SPIDER_API_BASE_URL = "http://8.155.168.11:5001"
TIMEOUT = 30  # 请求超时时间（秒）

# 配置日志
logger.add("test_spider_api.log", rotation="10 MB", retention="7 days")


class SpiderAPITester:
    """爬虫服务API测试类"""
    
    def __init__(self, base_url: str = SPIDER_API_BASE_URL, timeout: int = TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_health_check(self) -> bool:
        """测试健康检查接口"""
        print("\n" + "=" * 60)
        print("测试1: 健康检查接口")
        print("=" * 60)
        
        try:
            url = f"{self.base_url}/health"
            print(f"请求URL: {url}")
            
            response = self.session.get(url, timeout=5)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                print("✅ 健康检查通过")
                return True
            else:
                print(f"❌ 健康检查失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            return False
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务器: {self.base_url}")
            return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def test_search_user(self, query: str = "美食", page: int = 1) -> Dict[str, Any]:
        """测试搜索用户接口"""
        print("\n" + "=" * 60)
        print("测试2: 搜索用户接口")
        print("=" * 60)
        
        try:
            url = f"{self.base_url}/api/search/user"
            payload = {
                "query": query,
                "page": page
            }
            
            print(f"请求URL: {url}")
            print(f"请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    users = result.get('data', {}).get('users', [])
                    print(f"\n✅ 搜索成功，找到 {len(users)} 个用户")
                    
                    # 显示前3个用户
                    if users:
                        print("\n前3个用户信息:")
                        for i, user in enumerate(users[:3], 1):
                            print(f"  {i}. {user.get('name', 'N/A')} (ID: {user.get('id', 'N/A')})")
                            print(f"     粉丝数: {user.get('fans', 'N/A')}")
                            print(f"     笔记数: {user.get('note_count', 'N/A')}")
                    
                    return result
                else:
                    print(f"❌ 搜索失败: {result.get('msg')}")
                    return result
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            logger.error(f"搜索用户接口测试失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def test_search_user_batch(self, query: str = "美食", require_num: int = 5) -> Dict[str, Any]:
        """测试批量搜索用户接口"""
        print("\n" + "=" * 60)
        print("测试3: 批量搜索用户接口")
        print("=" * 60)
        
        try:
            url = f"{self.base_url}/api/search/user/batch"
            payload = {
                "query": query,
                "require_num": require_num
            }
            
            print(f"请求URL: {url}")
            print(f"请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    users = result.get('data', {}).get('users', [])
                    print(f"\n✅ 批量搜索成功，找到 {len(users)} 个用户")
                    
                    # 显示用户列表
                    if users:
                        print("\n用户列表:")
                        for i, user in enumerate(users[:5], 1):
                            print(f"  {i}. {user.get('name', 'N/A')} (ID: {user.get('id', 'N/A')})")
                    
                    return result
                else:
                    print(f"❌ 批量搜索失败: {result.get('msg')}")
                    return result
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            logger.error(f"批量搜索用户接口测试失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def test_get_users_notes(
        self, 
        user_ids: list = None, 
        max_users: int = 2, 
        notes_per_user: int = 3
    ) -> Dict[str, Any]:
        """测试获取用户笔记接口"""
        print("\n" + "=" * 60)
        print("测试4: 获取用户笔记接口")
        print("=" * 60)
        
        # 如果没有提供user_ids，先搜索获取一些用户ID
        if not user_ids:
            print("未提供用户ID，先搜索获取用户...")
            search_result = self.test_search_user_batch(query="美食", require_num=max_users)
            
            if search_result.get('success'):
                users = search_result.get('data', {}).get('users', [])
                user_ids = [user.get('id') for user in users[:max_users] if user.get('id')]
                print(f"获取到 {len(user_ids)} 个用户ID: {user_ids}")
            else:
                print("❌ 无法获取用户ID，测试终止")
                return {"success": False, "error": "无法获取用户ID"}
        
        try:
            url = f"{self.base_url}/api/users/notes"
            payload = {
                "user_ids": user_ids[:max_users],
                "max_users": max_users,
                "notes_per_user": notes_per_user
            }
            
            print(f"请求URL: {url}")
            print(f"请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=self.timeout)
            elapsed_time = time.time() - start_time
            
            print(f"响应状态码: {response.status_code}")
            print(f"请求耗时: {elapsed_time:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    notes = result.get('data', {}).get('notes', [])
                    count = result.get('data', {}).get('count', 0)
                    users_processed = result.get('data', {}).get('users_processed', 0)
                    
                    print(f"\n✅ 获取笔记成功")
                    print(f"   处理用户数: {users_processed}")
                    print(f"   获取笔记数: {count}")
                    
                    # 显示前5条笔记
                    if notes:
                        print("\n前5条笔记信息:")
                        for i, note in enumerate(notes[:5], 1):
                            print(f"  {i}. {note.get('title', 'N/A')[:50]}")
                            print(f"     笔记ID: {note.get('note_id', 'N/A')}")
                            print(f"     用户ID: {note.get('user_id', 'N/A')}")
                            print(f"     点赞数: {note.get('liked_count', 0)}")
                            print(f"     标签: {', '.join(note.get('tags', []))[:50]}")
                            print()
                    
                    return result
                else:
                    print(f"❌ 获取笔记失败: {result.get('msg')}")
                    print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return result
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return {"success": False, "error": response.text}
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时（{self.timeout}秒）")
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            logger.error(f"获取用户笔记接口测试失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def test_get_user_notes_single(self, user_id: str = None, limit: int = 5) -> Dict[str, Any]:
        """测试获取单个用户笔记接口"""
        print("\n" + "=" * 60)
        print("测试5: 获取单个用户笔记接口")
        print("=" * 60)
        
        # 如果没有提供user_id，先搜索获取一个用户ID
        if not user_id:
            print("未提供用户ID，先搜索获取用户...")
            search_result = self.test_search_user(query="美食", page=1)
            
            if search_result.get('success'):
                users = search_result.get('data', {}).get('users', [])
                if users:
                    user_id = users[0].get('id')
                    print(f"使用用户ID: {user_id}")
                else:
                    print("❌ 无法获取用户ID，测试终止")
                    return {"success": False, "error": "无法获取用户ID"}
            else:
                print("❌ 搜索用户失败，测试终止")
                return {"success": False, "error": "搜索用户失败"}
        
        try:
            url = f"{self.base_url}/api/user/notes/{user_id}"
            params = {"limit": limit}
            
            print(f"请求URL: {url}")
            print(f"查询参数: {params}")
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    notes = result.get('data', {}).get('notes', [])
                    count = result.get('data', {}).get('count', 0)
                    
                    print(f"\n✅ 获取笔记成功")
                    print(f"   笔记数量: {count}")
                    
                    # 显示笔记列表
                    if notes:
                        print("\n笔记列表:")
                        for i, note in enumerate(notes[:5], 1):
                            print(f"  {i}. {note.get('title', 'N/A')[:50]}")
                            print(f"     笔记ID: {note.get('note_id', 'N/A')}")
                    
                    return result
                else:
                    print(f"❌ 获取笔记失败: {result.get('msg')}")
                    return result
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            logger.error(f"获取单个用户笔记接口测试失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("开始测试爬虫服务API")
        print(f"服务器地址: {self.base_url}")
        print("=" * 60)
        
        results = {}
        
        # 测试1: 健康检查
        results['health'] = self.test_health_check()
        
        if not results['health']:
            print("\n❌ 健康检查失败，服务器可能不可用，停止后续测试")
            return results
        
        # 测试2: 搜索用户
        results['search_user'] = self.test_search_user(query="美食", page=1)
        
        # 测试3: 批量搜索用户
        results['search_user_batch'] = self.test_search_user_batch(query="美食", require_num=5)
        
        # 测试4: 获取用户笔记（使用搜索到的用户ID）
        if results['search_user_batch'].get('success'):
            users = results['search_user_batch'].get('data', {}).get('users', [])
            user_ids = [user.get('id') for user in users[:2] if user.get('id')]
            if user_ids:
                results['get_users_notes'] = self.test_get_users_notes(
                    user_ids=user_ids,
                    max_users=2,
                    notes_per_user=3
                )
        
        # 测试5: 获取单个用户笔记
        if results['search_user'].get('success'):
            users = results['search_user'].get('data', {}).get('users', [])
            if users:
                user_id = users[0].get('id')
                results['get_user_notes_single'] = self.test_get_user_notes_single(
                    user_id=user_id,
                    limit=5
                )
        
        # 测试总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        passed = sum(1 for r in results.values() if isinstance(r, dict) and r.get('success'))
        total = len([r for r in results.values() if isinstance(r, dict)])
        
        print(f"总测试数: {total}")
        print(f"通过数: {passed}")
        print(f"失败数: {total - passed}")
        
        for test_name, result in results.items():
            if isinstance(result, dict):
                status = "✅" if result.get('success') else "❌"
                print(f"{status} {test_name}: {result.get('msg', 'N/A')}")
            else:
                status = "✅" if result else "❌"
                print(f"{status} {test_name}")
        
        return results


if __name__ == "__main__":
    # 创建测试实例
    tester = SpiderAPITester(base_url=SPIDER_API_BASE_URL)
    
    # 运行所有测试
    results = tester.run_all_tests()
    
    # 保存测试结果
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n测试结果已保存到 test_results.json")