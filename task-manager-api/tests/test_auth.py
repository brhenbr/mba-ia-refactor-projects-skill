from database import db
from models.user import User


def test_protected_route_requires_token(client):
    resp = client.get("/tasks")
    assert resp.status_code == 401


def test_login_returns_real_jwt(client):
    resp = client.post("/login", json={"email": "user@test.com", "password": "userpass123"})
    assert resp.status_code == 200
    token = resp.get_json()["token"]
    assert token.count(".") == 2
    assert not token.startswith("fake-jwt-token-")


def test_login_wrong_password_fails(client):
    resp = client.post("/login", json={"email": "user@test.com", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_unknown_email_fails(client):
    resp = client.post("/login", json={"email": "nobody@test.com", "password": "whatever123"})
    assert resp.status_code == 401


def test_login_inactive_user_rejected(app, client):
    with app.app_context():
        inactive = User(name="Inactive", email="inactive@test.com", role="user", active=False)
        inactive.set_password("inactivepass1")
        db.session.add(inactive)
        db.session.commit()

    resp = client.post("/login", json={"email": "inactive@test.com", "password": "inactivepass1"})
    assert resp.status_code == 403


def test_register_rejects_role_field(client):
    """Registration schema has no `role` field at all (unknown fields are rejected by
    default), so a client can't even attempt to self-assign a role — every account
    created via POST /users is forced to role='user' at the service layer."""
    resp = client.post(
        "/users",
        json={"name": "New Admin", "email": "newadmin@test.com", "password": "newpass123", "role": "admin"},
    )
    assert resp.status_code == 400


def test_register_creates_plain_user_role(client):
    resp = client.post(
        "/users",
        json={"name": "New User", "email": "newuser@test.com", "password": "newpass123"},
    )
    assert resp.status_code == 201
    assert resp.get_json()["role"] == "user"


def test_password_never_returned_in_api(client, admin_headers, ids):
    resp = client.get(f"/users/{ids['admin']}", headers=admin_headers)
    body = resp.get_json()
    assert "password" not in body


def test_password_is_hashed_with_bcrypt(app):
    with app.app_context():
        user = User.query.filter_by(email="user@test.com").first()
        assert user.password != "userpass123"
        assert user.password.startswith("$2b$")
