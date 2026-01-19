# encoding: utf-8
"""
邮件发送测试脚本
"""
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from auth.email import init_mail, send_verification_email


# 创建Flask应用实例
app = Flask(__name__)

# 初始化邮件服务
init_mail(app)

# 测试邮件发送
def test_email_send():
    print("=== 邮件发送测试 ===")
    
    # 测试邮箱
    test_email = "1165699654@qq.com"
    test_code = "123456"
    
    # 发送测试邮件
    print(f"发送测试邮件到: {test_email}")
    print(f"验证码: {test_code}")
    
    # 使用非测试模式发送实际邮件
    success = send_verification_email(test_email, test_code, is_test=False)
    
    if success:
        print("✅ 邮件发送成功！")
    else:
        print("❌ 邮件发送失败！")
    
    print("=== 测试完成 ===")


if __name__ == "__main__":
    with app.app_context():
        test_email_send()
