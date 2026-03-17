# InfoPlan - 致力于解决信息过载问题的智能学习规划系统

一个基于小红书数据爬取和AI大模型的智能学习规划生成系统，支持用户搜索、笔记获取和个性化学习路径规划，帮助用户快速找到有价值的学习资源并制定合理的学习计划。

## 📋 项目简介

在信息爆炸的时代，我们每天都面临着大量的信息，如何从这些信息中筛选出有价值的内容并形成系统的学习计划，是一个巨大的挑战。InfoPlan 项目旨在解决这个问题，通过以下方式帮助用户：

1. **智能数据爬取**：从小红书等平台获取高质量的学习资源和笔记
2. **个性化学习规划**：基于AI大模型生成符合用户需求的学习路径
3. **资源智能匹配**：自动匹配相关笔记到学习步骤，提供系统化的学习材料

本项目包含两个核心服务：

1. **爬虫服务（Spider Service）**：提供小红书用户、笔记等数据的爬取API
2. **模型服务（Model Service）**：基于AI大模型生成个性化学习规划

## ✨ 主要功能

### 爬虫服务功能

- 🔍 **用户搜索**：支持关键词搜索用户，支持分页和批量获取
- 📝 **笔记获取**：获取用户笔记、笔记详情、评论等
- 💾 **数据存储**：支持保存笔记数据到Excel、下载媒体文件
- 🌐 **API服务**：提供RESTful API接口，支持跨域访问
- 🔐 **用户认证**：支持邮箱注册、登录、验证和密码重置

### 模型服务功能

- 🤖 **智能规划**：基于用户目标和笔记内容生成学习步骤
- 📚 **内容匹配**：自动匹配相关笔记到学习步骤
- 🎯 **个性化推荐**：根据用户ID列表获取相关笔记并生成规划
- 📊 **学习进度追踪**：记录用户学习进度，提供个性化学习建议

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js (用于执行JS加密脚本)
- 小红书Cookie（需要登录获取）
- MariaDB数据库（用于用户认证）

### 安装依赖

#### 安装Python依赖

```bash
pip install -r requirements.txt
```

#### 安装Node.js依赖（如果需要）

```bash
npm install
```

### 配置环境变量

创建 `.env` 文件，包含以下内容：

```
# 小红书Cookie
COOKIES=your_xiaohongshu_cookies_here

# 邮件服务配置（用于用户认证）
MAIL_PASSWORD=your_email_password_here

# JWT密钥（用于用户认证）
JWT_SECRET=your-jwt-secret-key-here
```

### 数据库配置

本项目使用MariaDB数据库存储用户信息，配置如下：

- **主机**：8.155.168.11
- **端口**：3306
- **用户名**：root
- **密码**：MicroXLab
- **数据库**：infoplan

### 启动爬虫服务

#### 启动API服务（默认端口5001）

```bash
python api_server.py
```

服务启动后，访问 `http://localhost:5001/health` 检查服务状态。

### 启动模型服务

#### 设置环境变量

```bash
# Windows
set SPIDER_API_URL=http://localhost:5001
set MODEL_PATH=/path/to/your/model
set MODEL_SERVICE_PORT=5002

# Linux/Mac
SPIDER_API_URL=http://localhost:5001 MODEL_PATH=/path/to/your/model MODEL_SERVICE_PORT=5002 python model_service_server.py
```

#### 启动模型服务

```bash
cd XHS_Learing_Agent
python model_service_server.py
```

## 📖 API文档

### 认证服务API（端口5001）

#### 1. 用户注册

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应示例：**

```json
{
  "success": true,
  "msg": "注册成功，验证码已发送至您的邮箱",
  "data": {
    "email": "user@example.com",
    "verification_expiry": "2023-12-01T12:00:00"
  }
}
```

#### 2. 邮箱验证

```http
POST /api/auth/verify-email
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

#### 3. 用户登录

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应示例：**

```json
{
  "success": true,
  "msg": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com"
    }
  }
}
```

#### 4. 请求重置密码

```http
POST /api/auth/request-reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### 5. 重置密码

```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "token": "reset_token",
  "new_password": "new_password123"
}
```

### 爬虫服务API（端口5001）

#### 1. 搜索用户

```http
POST /api/search/user
Content-Type: application/json

{
  "query": "美食",
  "page": 1,
  "proxies": {}  // 可选
}
```

**响应示例：**

```json
{
  "success": true,
  "msg": "成功",
  "data": {
    "users": [...],
    "has_more": true
  }
}
```

#### 2. 批量搜索用户

```http
POST /api/search/user/batch
Content-Type: application/json

{
  "query": "美食",
  "require_num": 15
}
```

#### 3. 获取用户笔记

```http
POST /api/users/notes
Content-Type: application/json

{
  "user_ids": ["user_id1", "user_id2"],
  "max_users": 5,
  "notes_per_user": 5
}
```

#### 4. 获取单个用户笔记

```http
GET /api/user/notes/{user_id}?limit=20
```

#### 5. 健康检查

```http
GET /health
```

### 模型服务API（端口5002）

#### 生成学习规划

```http
POST /api/learning/plan
Content-Type: application/json
{
  "goal": "我想学习AI agent的简单开发",
  "user_ids": ["user_id1", "user_id2"],
  "max_users": 5,
  "notes_per_user": 5,
  "debug": false
}
```

**响应示例：**

```json
{
  "success": true,
  "msg": "学习规划生成成功",
  "data": {
    "goal": "我想学习AI agent的简单开发",
    "steps": [
      {
        "step_number": 1,
        "description": "了解AI Agent基础概念",
        "recommended_notes": [...]
      }
    ],
    "statistics": {
      "total_users": 5,
      "total_notes": 25,
      "total_steps": 5
    }
  }
}
```

## 🔧 使用示例

### Python代码示例

#### 搜索用户

```python
import requests

response = requests.post('http://localhost:5001/api/search/user', json={
    'query': '美食',
    'page': 1
})
users = response.json()
print(users)
```

#### 获取用户笔记

```python
import requests

response = requests.post('http://localhost:5001/api/users/notes', json={
    'user_ids': ['user_id1', 'user_id2'],
    'max_users': 5,
    'notes_per_user': 5
})
notes = response.json()
print(notes)
```

#### 生成学习规划

```python
import requests

response = requests.post('http://localhost:5002/api/learning/plan', json={
    'goal': '我想学习Python爬虫',
    'user_ids': ['user_id1', 'user_id2'],
    'max_users': 5,
    'notes_per_user': 5
})
plan = response.json()
print(plan)
```

#### 用户注册

```python
import requests

response = requests.post('http://localhost:5001/api/auth/register', json={
    'email': 'user@example.com',
    'password': 'password123'
})
print(response.json())
```

#### 用户登录

```python
import requests

response = requests.post('http://localhost:5001/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})
print(response.json())
```

### 爬虫服务配置

在 `api_server.py` 中配置：

- **端口**：默认5001
- **Cookie**：通过环境变量 `COOKIES` 设置
- **邮件服务**：通过环境变量 `MAIL_PASSWORD` 设置
- **JWT密钥**：通过环境变量 `JWT_SECRET` 设置

### 模型服务配置

在 `XHS_Learing_Agent/config.py` 中配置：

- `MODEL_PATH`: 模型文件路径
- `SPIDER_API_URL`: 爬虫服务地址
- `MODEL_SERVICE_PORT`: 模型服务端口

## 🔒 注意事项

1. **Cookie安全**：请妥善保管Cookie，不要提交到代码仓库
2. **请求频率**：请合理控制请求频率，避免被封禁
3. **数据使用**：请遵守小红书的使用条款，仅用于学习研究
4. **模型路径**：确保模型文件路径正确，模型服务才能正常启动
5. **邮件配置**：确保邮件服务配置正确，否则用户认证功能无法使用
6. **数据库配置**：确保数据库配置正确，否则用户认证功能无法使用

## 🛠️ 开发指南

### 项目结构

```
InfoPlan_backend/
├── apis/                  # API接口实现
│   ├── auth_apis.py       # 认证相关API
│   └── xhs_pc_apis.py     # 小红书爬虫API
├── auth/                  # 认证相关功能
│   ├── email.py           # 邮件发送功能
│   └── utils.py           # 认证工具函数
├── db_config.py           # 数据库配置
├── db_connection.py       # 数据库连接
├── models/                # 数据模型
│   └── user.py            # 用户模型
├── tests/                 # 测试脚本
├── xhs_utils/             # 小红书工具函数
├── api_server.py          # API服务启动文件
├── requirements.txt       # Python依赖
└── README.md              # 项目说明
```

### 添加新的API接口

1. 在 `apis/` 目录中添加新的API实现文件或在现有文件中添加新方法
2. 在 `api_server.py` 中添加对应的路由
3. 更新API文档

### 扩展数据提供者

1. 实现 `data_providers/interfaces.py` 中的接口
2. 在 `model_service` 中使用新的数据提供者

### 数据库迁移

当修改数据模型时，需要执行数据库迁移：

```bash
# 生成迁移脚本
python -m alembic revision --autogenerate -m "description"

# 执行迁移
python -m alembic upgrade head
```

## 📄 许可证

本项目采用 MIT 许可证，仅供学习研究使用，请勿用于商业用途。

## 🤝 贡献

欢迎提交Issue和Pull Request！我们非常欢迎社区贡献，包括但不限于：

- 修复bug
- 添加新功能
- 改进文档
- 优化性能

## 📮 联系方式

如有问题，请通过以下方式联系我们：

- **GitHub Issue**：在项目仓库中提交Issue
- **邮箱**：nono@ycy.fan
- **微信**：请在Issue中留下您的联系方式

## 📊 项目状态

- **开发状态**：活跃开发中
- **测试状态**：基本功能测试通过
- **部署状态**：可本地部署

---

**⚠️ 免责声明**：本项目仅用于技术学习和研究，使用者需自行承担使用风险，并遵守相关法律法规和平台规则。

**📝 更新日志**：

- 2024-01-19：完善用户认证功能，添加邮件发送和密码重置功能
- 2024-01-18：添加模型服务，支持生成个性化学习规划
- 2024-01-17：添加爬虫服务，支持小红书用户和笔记爬取
- 2024-01-16：项目初始化，搭建基本框架

---

**🌟 感谢**：

- 小红书平台提供的丰富学习资源
- 所有为项目做出贡献的开发者
- 所有使用和支持本项目的用户

---

**InfoPlan** - 让学习更智能，让信息更有价值！
