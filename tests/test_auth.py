# encoding: utf-8
"""
认证接口测试
"""
import unittest
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app


class AuthTestCase(unittest.TestCase):
    """认证接口测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.app = app.test_client()
        self.app.testing = True
        
        # 测试邮箱
        self.test_email = "test_user@example.com"
        self.test_password = "password123"
    
    def test_register(self):
        """测试用户注册接口"""
        # 测试请求
        response = self.app.post(
            '/api/auth/register',
            data=json.dumps({
                "email": self.test_email,
                "password": self.test_password
            }),
            content_type='application/json'
        )
        
        # 检查响应
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertEqual(data['msg'], '注册成功，验证码已发送至您的邮箱')
        self.assertEqual(data['data']['email'], self.test_email)
    
    def test_login_without_verification(self):
        """测试未验证邮箱的登录"""
        # 先注册用户
        self.test_register()
        
        # 尝试登录
        response = self.app.post(
            '/api/auth/login',
            data=json.dumps({
                "email": self.test_email,
                "password": self.test_password
            }),
            content_type='application/json'
        )
        
        # 检查响应
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['msg'], '邮箱未验证，请先验证邮箱')
    
    def test_invalid_login(self):
        """测试无效登录"""
        response = self.app.post(
            '/api/auth/login',
            data=json.dumps({
                "email": "non_existent@example.com",
                "password": "wrong_password"
            }),
            content_type='application/json'
        )
        
        # 检查响应
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
    
    def test_request_reset_password(self):
        """测试请求重置密码"""
        # 先注册用户
        self.test_register()
        
        # 请求重置密码
        response = self.app.post(
            '/api/auth/request-reset',
            data=json.dumps({
                "email": self.test_email
            }),
            content_type='application/json'
        )
        
        # 检查响应
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['msg'], '重置密码邮件已发送，请查收')


if __name__ == '__main__':
    unittest.main()
