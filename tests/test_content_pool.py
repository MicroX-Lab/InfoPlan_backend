# encoding: utf-8
"""Phase 2 内容池模块测试"""
import json
import pytest
from app import create_app
from app.extensions import db


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
    """注册并登录，返回 JWT token"""
    client.post("/api/auth/register", json={
        "username": "testuser", "password": "test123456"
    })
    resp = client.post("/api/auth/login", json={
        "username": "testuser", "password": "test123456"
    })
    data = resp.get_json()
    return data["data"]["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


class TestBloggerCRUD:
    """博主 CRUD 测试"""

    def test_add_blogger(self, client, auth_token):
        resp = client.post("/api/bloggers", json={
            "xhs_user_id": "abc123",
            "nickname": "测试博主",
            "description": "测试描述",
        }, headers=auth_header(auth_token))
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["xhs_user_id"] == "abc123"

    def test_add_duplicate_blogger(self, client, auth_token):
        headers = auth_header(auth_token)
        client.post("/api/bloggers", json={
            "xhs_user_id": "abc123", "nickname": "博主1"
        }, headers=headers)
        resp = client.post("/api/bloggers", json={
            "xhs_user_id": "abc123", "nickname": "博主1"
        }, headers=headers)
        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "该博主已在内容池中"

    def test_list_bloggers(self, client, auth_token):
        headers = auth_header(auth_token)
        client.post("/api/bloggers", json={
            "xhs_user_id": "user1", "nickname": "博主1"
        }, headers=headers)
        client.post("/api/bloggers", json={
            "xhs_user_id": "user2", "nickname": "博主2"
        }, headers=headers)
        resp = client.get("/api/bloggers", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) == 2

    def test_delete_blogger(self, client, auth_token):
        headers = auth_header(auth_token)
        resp = client.post("/api/bloggers", json={
            "xhs_user_id": "user_del", "nickname": "待删博主"
        }, headers=headers)
        blogger_id = resp.get_json()["data"]["id"]
        resp = client.delete(f"/api/bloggers/{blogger_id}", headers=headers)
        assert resp.status_code == 200

        # 验证已删除
        resp = client.get("/api/bloggers", headers=headers)
        assert len(resp.get_json()["data"]) == 0

    def test_delete_nonexistent_blogger(self, client, auth_token):
        resp = client.delete("/api/bloggers/9999", headers=auth_header(auth_token))
        assert resp.status_code == 404


class TestTagCRUD:
    """标签 CRUD 测试"""

    def test_create_tag(self, client, auth_token):
        resp = client.post("/api/tags", json={"name": "美食"},
                           headers=auth_header(auth_token))
        assert resp.status_code == 201
        assert resp.get_json()["data"]["name"] == "美食"

    def test_create_duplicate_tag(self, client, auth_token):
        headers = auth_header(auth_token)
        client.post("/api/tags", json={"name": "美食"}, headers=headers)
        resp = client.post("/api/tags", json={"name": "美食"}, headers=headers)
        assert resp.status_code == 400

    def test_list_tags(self, client, auth_token):
        headers = auth_header(auth_token)
        client.post("/api/tags", json={"name": "美食"}, headers=headers)
        client.post("/api/tags", json={"name": "旅行"}, headers=headers)
        resp = client.get("/api/tags", headers=headers)
        assert len(resp.get_json()["data"]) == 2

    def test_delete_tag(self, client, auth_token):
        headers = auth_header(auth_token)
        resp = client.post("/api/tags", json={"name": "待删"},
                           headers=headers)
        tag_id = resp.get_json()["data"]["id"]
        resp = client.delete(f"/api/tags/{tag_id}", headers=headers)
        assert resp.status_code == 200


class TestBloggerTagging:
    """博主打标签测试"""

    def test_add_tags_to_blogger(self, client, auth_token):
        headers = auth_header(auth_token)
        resp = client.post("/api/bloggers", json={
            "xhs_user_id": "tag_test", "nickname": "标签测试"
        }, headers=headers)
        blogger_id = resp.get_json()["data"]["id"]

        resp = client.post(f"/api/bloggers/{blogger_id}/tags", json={
            "tags": ["美食", "旅行", "生活"]
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data["tags"]) == 3

    def test_filter_bloggers_by_tag(self, client, auth_token):
        headers = auth_header(auth_token)
        # 添加两个博主
        resp1 = client.post("/api/bloggers", json={
            "xhs_user_id": "food_blogger", "nickname": "美食博主"
        }, headers=headers)
        resp2 = client.post("/api/bloggers", json={
            "xhs_user_id": "travel_blogger", "nickname": "旅行博主"
        }, headers=headers)
        id1 = resp1.get_json()["data"]["id"]
        id2 = resp2.get_json()["data"]["id"]

        # 给博主打不同标签
        client.post(f"/api/bloggers/{id1}/tags", json={"tags": ["美食"]},
                    headers=headers)
        client.post(f"/api/bloggers/{id2}/tags", json={"tags": ["旅行"]},
                    headers=headers)

        # 按标签筛选
        resp = client.get("/api/bloggers?tag=美食", headers=headers)
        data = resp.get_json()["data"]
        assert len(data) == 1
        assert data[0]["nickname"] == "美食博主"

    def test_add_tags_to_nonexistent_blogger(self, client, auth_token):
        resp = client.post("/api/bloggers/9999/tags", json={"tags": ["test"]},
                           headers=auth_header(auth_token))
        assert resp.status_code == 404


class TestInputValidation:
    """输入验证测试"""

    def test_add_blogger_missing_xhs_user_id(self, client, auth_token):
        resp = client.post("/api/bloggers", json={"nickname": "test"},
                           headers=auth_header(auth_token))
        assert resp.status_code == 400

    def test_create_tag_empty_name(self, client, auth_token):
        resp = client.post("/api/tags", json={"name": "  "},
                           headers=auth_header(auth_token))
        assert resp.status_code == 400

    def test_unauthorized_access(self, client):
        resp = client.get("/api/bloggers")
        assert resp.status_code == 401
