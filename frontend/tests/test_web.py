import json
from unittest.mock import patch

import pytest

from web.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _login_session(client):
    """Устанавливает сессию авторизованного пользователя."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "testuser"
        sess["gender"] = "male"


def test_index_redirects_without_login(client):
    resp = client.get("/")
    assert resp.status_code == 302


@patch("web.app.get_articles")
def test_index_page(mock_articles, client):
    _login_session(client)
    mock_articles.return_value = [
        {"id": 1, "title": "Тест", "summary": "Описание", "author": "Автор", "created_at": "2025-01-01"},
    ]
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Форум МТУСИ".encode() in resp.data


@patch("web.app.analyze_text")
def test_check_valid(mock_analyze, client):
    _login_session(client)
    mock_analyze.return_value = {
        "label": "toxic",
        "score": 0.95,
        "toxicity_percent": 95.0,
    }
    resp = client.post(
        "/check",
        data=json.dumps({"text": "test text"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["label"] == "toxic"
    assert data["score"] == 0.95
    mock_analyze.assert_called_once_with("test text", user_id=1)


def test_check_requires_auth(client):
    resp = client.post(
        "/check",
        data=json.dumps({"text": "test"}),
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_check_empty(client):
    _login_session(client)
    resp = client.post(
        "/check",
        data=json.dumps({"text": "   "}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_check_no_body(client):
    _login_session(client)
    resp = client.post("/check", content_type="application/json")
    assert resp.status_code == 400


@patch("web.app.get_stats")
def test_stats_page(mock_stats, client):
    _login_session(client)
    mock_stats.return_value = {
        "total_checks": 42,
        "toxic_count": 10,
        "neutral_count": 32,
        "toxic_percent": 23.8,
        "avg_toxic_score": 0.91,
        "recent": [],
        "by_gender": [
            {"gender": "male", "total": 30, "toxic_count": 8, "toxic_percent": 26.7},
            {"gender": "female", "total": 12, "toxic_count": 2, "toxic_percent": 16.7},
        ],
    }
    resp = client.get("/stats")
    assert resp.status_code == 200


@patch("web.app.login_user")
def test_login_success(mock_login, client):
    mock_login.return_value = {"id": 1, "username": "user1", "gender": "male"}
    resp = client.post(
        "/login",
        data=json.dumps({"username": "user1", "password": "pass"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


@patch("web.app.login_user")
def test_login_fail(mock_login, client):
    mock_login.return_value = {"error": "Неверное имя пользователя или пароль"}
    resp = client.post(
        "/login",
        data=json.dumps({"username": "user1", "password": "wrong"}),
        content_type="application/json",
    )
    assert resp.status_code == 401


@patch("web.app.register_user")
def test_register_success(mock_register, client):
    mock_register.return_value = {"id": 1, "username": "newuser", "gender": "female"}
    resp = client.post(
        "/register",
        data=json.dumps({"username": "newuser", "password": "pass", "gender": "female"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


@patch("web.app.get_comments")
@patch("web.app.get_article")
def test_article_page(mock_article, mock_comments, client):
    _login_session(client)
    mock_article.return_value = {
        "id": 1, "title": "Тест", "summary": "Описание", "author": "Автор", "created_at": "2025-01-01",
    }
    mock_comments.return_value = []
    resp = client.get("/article/1")
    assert resp.status_code == 200


@patch("web.app.get_article")
def test_article_not_found(mock_article, client):
    _login_session(client)
    mock_article.return_value = None
    resp = client.get("/article/999")
    assert resp.status_code == 302


@patch("web.app.post_comment")
def test_comment_success(mock_post, client):
    _login_session(client)
    mock_post.return_value = {
        "id": 1, "article_id": 1, "user_id": 1,
        "username": "testuser", "text": "Хороший текст", "created_at": "2025-01-01",
    }
    resp = client.post(
        "/article/1/comment",
        data=json.dumps({"text": "Хороший текст"}),
        content_type="application/json",
    )
    assert resp.status_code == 200


@patch("web.app.post_comment")
def test_comment_blocked(mock_post, client):
    _login_session(client)
    mock_post.return_value = {"blocked": True, "error": "Токсичный контент"}
    resp = client.post(
        "/article/1/comment",
        data=json.dumps({"text": "плохой текст"}),
        content_type="application/json",
    )
    assert resp.status_code == 403


def test_comment_requires_auth(client):
    resp = client.post(
        "/article/1/comment",
        data=json.dumps({"text": "текст"}),
        content_type="application/json",
    )
    assert resp.status_code == 401


@patch("web.app.check_api_health")
def test_health_ok(mock_health, client):
    mock_health.return_value = True
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


@patch("web.app.check_api_health")
def test_health_unavailable(mock_health, client):
    mock_health.return_value = False
    resp = client.get("/api/health")
    assert resp.status_code == 503
    assert resp.get_json()["status"] == "unavailable"
