# encoding: utf-8
"""
认证服务API服务器
专注于邮箱登录注册功能
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from apis.auth_apis import (
    register_api, verify_email_api, login_api,
    request_reset_password_api, reset_password_api
)
from auth.email import init_mail

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化邮件服务
init_mail(app)

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
        "service": "Auth Service",
        "message": "认证服务运行正常"
    }), 200


if __name__ == '__main__':
    print('=' * 60)
    print('启动认证服务API服务器')
    print('=' * 60)
    print('认证相关接口:')
    print('用户注册: POST /api/auth/register')
    print('邮箱验证: POST /api/auth/verify-email')
    print('用户登录: POST /api/auth/login')
    print('请求重置密码: POST /api/auth/request-reset')
    print('重置密码: POST /api/auth/reset-password')
    print('健康检查接口: GET /health')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5002, debug=True)
