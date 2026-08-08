import pytest


def test_health_does_not_leak_secrets(client):
    resp = client.get("/health")
    body = resp.get_json()
    assert "secret_key" not in body
    assert "debug" not in body


def test_debug_disabled_in_testing_config(app):
    assert app.config["DEBUG"] is False


def test_cors_is_not_wide_open_by_default(app):
    assert app.config["CORS_ORIGINS"] == []


def test_sql_meta_characters_in_search_do_not_error(client, user_headers):
    resp = client.get("/tasks/search", query_string={"q": "x' OR '1'='1"}, headers=user_headers)
    assert resp.status_code == 200
    assert resp.get_json() == []


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/tasks"),
        ("post", "/tasks"),
        ("get", "/tasks/search"),
        ("get", "/tasks/stats"),
        ("get", "/users"),
        ("get", "/categories"),
        ("get", "/reports/summary"),
    ],
)
def test_protected_routes_require_auth(client, method, path):
    resp = getattr(client, method)(path)
    assert resp.status_code == 401


def test_password_hash_never_serialized_in_login_response(client):
    resp = client.post("/login", json={"email": "user@test.com", "password": "userpass123"})
    body = resp.get_json()
    assert "password" not in body["user"]
