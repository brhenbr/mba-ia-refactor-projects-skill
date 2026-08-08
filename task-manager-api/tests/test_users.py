def test_register_requires_valid_email(client):
    resp = client.post("/users", json={"name": "X", "email": "not-an-email", "password": "validpass123"})
    assert resp.status_code == 400


def test_register_requires_min_password_length(client):
    resp = client.post("/users", json={"name": "X", "email": "short@test.com", "password": "short"})
    assert resp.status_code == 400


def test_register_duplicate_email_returns_409(client):
    client.post("/users", json={"name": "First", "email": "dup@test.com", "password": "validpass123"})
    resp = client.post("/users", json={"name": "Second", "email": "dup@test.com", "password": "validpass123"})
    assert resp.status_code == 409


def test_list_users_requires_admin(client, user_headers):
    resp = client.get("/users", headers=user_headers)
    assert resp.status_code == 403


def test_list_users_allowed_for_admin(client, admin_headers):
    resp = client.get("/users", headers=admin_headers)
    assert resp.status_code == 200


def test_get_own_profile_allowed(client, user_headers, ids):
    resp = client.get(f"/users/{ids['user']}", headers=user_headers)
    assert resp.status_code == 200


def test_get_other_profile_forbidden_for_non_admin(client, user_headers, ids):
    resp = client.get(f"/users/{ids['other_user']}", headers=user_headers)
    assert resp.status_code == 403


def test_get_other_profile_allowed_for_admin(client, admin_headers, ids):
    resp = client.get(f"/users/{ids['other_user']}", headers=admin_headers)
    assert resp.status_code == 200


def test_non_admin_cannot_change_own_role(client, user_headers, ids):
    resp = client.put(f"/users/{ids['user']}", json={"role": "admin"}, headers=user_headers)
    assert resp.status_code == 403


def test_non_admin_can_update_own_name(client, user_headers, ids):
    resp = client.put(f"/users/{ids['user']}", json={"name": "Updated Name"}, headers=user_headers)
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Updated Name"


def test_admin_can_change_role(client, admin_headers, ids):
    resp = client.put(f"/users/{ids['user']}", json={"role": "manager"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["role"] == "manager"


def test_delete_user_requires_admin(client, user_headers, ids):
    resp = client.delete(f"/users/{ids['other_user']}", headers=user_headers)
    assert resp.status_code == 403


def test_admin_can_delete_user(client, admin_headers, ids):
    resp = client.delete(f"/users/{ids['other_user']}", headers=admin_headers)
    assert resp.status_code == 200


def test_get_user_tasks_forbidden_for_other_user(client, user_headers, ids):
    resp = client.get(f"/users/{ids['other_user']}/tasks", headers=user_headers)
    assert resp.status_code == 403
