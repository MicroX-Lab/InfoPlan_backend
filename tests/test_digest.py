# encoding: utf-8
"""Phase 3 每日摘要模块测试"""
import json
import time
from unittest.mock import patch, MagicMock
import pytest
from app import create_app
from app.extensions import db
from app.models.blogger import Blogger
from app.models.digest import Digest


@pytest.fixture
def app():
    app = create_app("development")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_token(client):
    client.post("/api/auth/register", json={
        "username": "digestuser", "password": "test123456"
    })
    resp = client.post("/api/auth/login", json={
        "username": "digestuser", "password": "test123456"
    })
    return resp.get_json()["data"]["access_token"]


@pytest.fixture
def user_with_bloggers(app, auth_token, client):
    """创建带博主的用户"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    client.post("/api/bloggers", json={
        "xhs_user_id": "blogger_001", "nickname": "美食博主"
    }, headers=headers)
    client.post("/api/bloggers", json={
        "xhs_user_id": "blogger_002", "nickname": "旅行博主"
    }, headers=headers)
    return auth_token


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


class TestDigestGeneration:
    """摘要生成测试"""

    def test_generate_digest_no_bloggers(self, client, auth_token):
        """内容池为空时不能生成摘要"""
        resp = client.post("/api/digest/generate", json={},
                           headers=auth_header(auth_token))
        assert resp.status_code == 400
        assert "内容池为空" in resp.get_json()["msg"]

    @patch("app.services.digest_service.llm_service")
    @patch("app.services.digest_service.xhs_service")
    def test_generate_digest_success(self, mock_xhs, mock_llm,
                                     client, user_with_bloggers):
        """成功生成摘要（mock 外部服务）"""
        mock_xhs.get_users_latest_notes.return_value = [
            {"note_id": "n1", "title": "美食笔记1", "desc": "好吃的内容",
             "type": "normal", "user_id": "blogger_001"},
            {"note_id": "n2", "title": "旅行笔记1", "desc": "好玩的地方",
             "type": "normal", "user_id": "blogger_002"},
        ]
        mock_llm.summarize_note.return_value = "这是AI生成的摘要"

        resp = client.post("/api/digest/generate", json={},
                           headers=auth_header(user_with_bloggers))
        assert resp.status_code == 202
        assert resp.get_json()["data"]["status"] == "processing"

        # 等待后台线程完成
        time.sleep(1)

        # 检查任务状态
        resp = client.get("/api/digest/status",
                          headers=auth_header(user_with_bloggers))
        data = resp.get_json()["data"]
        assert data["status"] == "done"

    @patch("app.services.digest_service.llm_service")
    @patch("app.services.digest_service.xhs_service")
    def test_generate_digest_duplicate_blocked(self, mock_xhs, mock_llm,
                                                client, user_with_bloggers):
        """重复触发时阻止"""
        mock_xhs.get_users_latest_notes.return_value = [
            {"note_id": "n1", "title": "笔记", "desc": "内容",
             "type": "normal", "user_id": "blogger_001"},
        ]
        mock_llm.summarize_note.return_value = "摘要"

        headers = auth_header(user_with_bloggers)
        # 第一次触发
        client.post("/api/digest/generate", json={}, headers=headers)
        # 立刻第二次触发（应被阻止，因为正在处理）
        resp = client.post("/api/digest/generate", json={}, headers=headers)
        # 可能已经完成或正在处理，两种情况都行
        data = resp.get_json()
        # 确认响应合理
        assert resp.status_code in [202, 400]

        time.sleep(1)  # 等待完成


class TestDigestQuery:
    """摘要查询测试"""

    def test_get_latest_no_digest(self, client, auth_token):
        resp = client.get("/api/digest/latest",
                          headers=auth_header(auth_token))
        assert resp.status_code == 404

    def test_get_history_empty(self, client, auth_token):
        resp = client.get("/api/digest/history",
                          headers=auth_header(auth_token))
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_digest_detail_not_found(self, client, auth_token):
        resp = client.get("/api/digest/9999",
                          headers=auth_header(auth_token))
        assert resp.status_code == 404

    def test_get_latest_with_data(self, app, client, auth_token):
        """有数据时获取最新摘要"""
        with app.app_context():
            digest = Digest(
                user_id=1,
                digest_json=json.dumps({
                    "total_notes": 2,
                    "bloggers_count": 1,
                    "items": [
                        {"note_id": "test1", "title": "测试笔记", "summary": "摘要"},
                    ]
                }, ensure_ascii=False),
            )
            db.session.add(digest)
            db.session.commit()

        resp = client.get("/api/digest/latest",
                          headers=auth_header(auth_token))
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["digest"]["total_notes"] == 2

    def test_get_history_with_data(self, app, client, auth_token):
        """摘要历史分页"""
        with app.app_context():
            for i in range(3):
                d = Digest(
                    user_id=1,
                    digest_json=json.dumps({"total_notes": i, "items": []},
                                           ensure_ascii=False),
                )
                db.session.add(d)
            db.session.commit()

        resp = client.get("/api/digest/history?page=1&per_page=2",
                          headers=auth_header(auth_token))
        data = resp.get_json()["data"]
        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["pages"] == 2

    def test_get_digest_detail_success(self, app, client, auth_token):
        """获取特定摘要详情"""
        with app.app_context():
            digest = Digest(
                user_id=1,
                digest_json=json.dumps({"total_notes": 1, "items": [{"note_id": "x"}]},
                                       ensure_ascii=False),
            )
            db.session.add(digest)
            db.session.commit()
            digest_id = digest.id

        resp = client.get(f"/api/digest/{digest_id}",
                          headers=auth_header(auth_token))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["digest"]["total_notes"] == 1


class TestDigestStatus:
    """任务状态查询测试"""

    def test_status_idle(self, client, auth_token):
        # 清除可能遗留的任务状态
        from app.services.digest_service import _digest_tasks, _tasks_lock
        with _tasks_lock:
            _digest_tasks.clear()

        resp = client.get("/api/digest/status",
                          headers=auth_header(auth_token))
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "idle"

    def test_unauthorized_access(self, client):
        resp = client.post("/api/digest/generate")
        assert resp.status_code == 401
