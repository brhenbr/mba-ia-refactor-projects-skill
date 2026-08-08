def test_list_categories_requires_auth(client):
    resp = client.get("/categories")
    assert resp.status_code == 401


def test_list_categories_allowed_for_any_authenticated_user(client, user_headers):
    resp = client.get("/categories", headers=user_headers)
    assert resp.status_code == 200


def test_create_category_requires_admin(client, user_headers):
    resp = client.post("/categories", json={"name": "Frontend"}, headers=user_headers)
    assert resp.status_code == 403


def test_admin_can_create_update_delete_category(client, admin_headers):
    create_resp = client.post("/categories", json={"name": "Frontend", "color": "#2ecc71"}, headers=admin_headers)
    assert create_resp.status_code == 201
    category_id = create_resp.get_json()["id"]

    update_resp = client.put(f"/categories/{category_id}", json={"name": "Frontend v2"}, headers=admin_headers)
    assert update_resp.status_code == 200
    assert update_resp.get_json()["name"] == "Frontend v2"

    delete_resp = client.delete(f"/categories/{category_id}", headers=admin_headers)
    assert delete_resp.status_code == 200


def test_create_category_invalid_color_returns_400(client, admin_headers):
    resp = client.post("/categories", json={"name": "Bad Color", "color": "not-a-color"}, headers=admin_headers)
    assert resp.status_code == 400
