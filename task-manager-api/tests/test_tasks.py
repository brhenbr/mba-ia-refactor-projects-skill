from datetime import datetime, timedelta


def _create_task(client, headers, **overrides):
    payload = {"title": "Write refactor plan", "priority": 2}
    payload.update(overrides)
    return client.post("/tasks", json=payload, headers=headers)


def test_create_task_assigns_to_self_by_default(client, user_headers, ids):
    resp = _create_task(client, user_headers)
    assert resp.status_code == 201
    assert resp.get_json()["user_id"] == ids["user"]


def test_user_cannot_read_another_users_task(client, user_headers, other_user_headers):
    created = _create_task(client, other_user_headers).get_json()

    resp = client.get(f"/tasks/{created['id']}", headers=user_headers)
    assert resp.status_code == 403


def test_user_task_list_excludes_others_tasks(client, user_headers, other_user_headers):
    _create_task(client, other_user_headers, title="Other user task")
    _create_task(client, user_headers, title="My task")

    resp = client.get("/tasks", headers=user_headers)
    titles = [t["title"] for t in resp.get_json()]
    assert "My task" in titles
    assert "Other user task" not in titles


def test_admin_sees_all_tasks(client, admin_headers, user_headers, other_user_headers):
    _create_task(client, user_headers, title="User task")
    _create_task(client, other_user_headers, title="Other task")

    resp = client.get("/tasks", headers=admin_headers)
    titles = [t["title"] for t in resp.get_json()]
    assert "User task" in titles
    assert "Other task" in titles


def test_admin_can_assign_task_to_other_user(client, admin_headers, ids):
    resp = _create_task(client, admin_headers, user_id=ids["user"])
    assert resp.status_code == 201
    assert resp.get_json()["user_id"] == ids["user"]


def test_non_admin_cannot_reassign_task(client, user_headers, other_user_headers, ids):
    created = _create_task(client, user_headers).get_json()

    resp = client.put(f"/tasks/{created['id']}", json={"user_id": ids["other_user"]}, headers=user_headers)
    assert resp.status_code == 403


def test_user_can_update_own_task(client, user_headers):
    created = _create_task(client, user_headers).get_json()

    resp = client.put(f"/tasks/{created['id']}", json={"status": "done"}, headers=user_headers)
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "done"


def test_user_can_delete_own_task(client, user_headers):
    created = _create_task(client, user_headers).get_json()

    resp = client.delete(f"/tasks/{created['id']}", headers=user_headers)
    assert resp.status_code == 200


def test_is_overdue_true_for_past_due_pending_task(client, user_headers):
    past_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
    created = _create_task(client, user_headers, due_date=past_date, status="pending").get_json()
    assert created["overdue"] is True


def test_is_overdue_false_for_done_task(client, user_headers):
    past_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
    created = _create_task(client, user_headers, due_date=past_date, status="done").get_json()
    assert created["overdue"] is False


def test_search_with_non_numeric_priority_returns_400_instead_of_crashing(client, user_headers):
    resp = client.get("/tasks/search", query_string={"priority": "abc"}, headers=user_headers)
    assert resp.status_code == 400


def test_search_with_non_numeric_user_id_returns_400(client, user_headers):
    resp = client.get("/tasks/search", query_string={"user_id": "abc"}, headers=user_headers)
    assert resp.status_code == 400


def test_search_scoped_to_own_tasks_for_regular_user(client, user_headers, other_user_headers):
    _create_task(client, other_user_headers, title="Findable other task")
    _create_task(client, user_headers, title="Findable my task")

    resp = client.get("/tasks/search", query_string={"q": "Findable"}, headers=user_headers)
    titles = [t["title"] for t in resp.get_json()]
    assert titles == ["Findable my task"]


def test_stats_scoped_to_own_tasks_for_regular_user(client, user_headers, other_user_headers):
    _create_task(client, other_user_headers)
    _create_task(client, user_headers)
    _create_task(client, user_headers, status="done")

    resp = client.get("/tasks/stats", headers=user_headers)
    stats = resp.get_json()
    assert stats["total"] == 2
    assert stats["done"] == 1


def test_create_task_invalid_title_returns_400(client, user_headers):
    resp = client.post("/tasks", json={"title": "ab"}, headers=user_headers)
    assert resp.status_code == 400


def test_create_task_invalid_priority_returns_400(client, user_headers):
    resp = client.post("/tasks", json={"title": "Valid title", "priority": 9}, headers=user_headers)
    assert resp.status_code == 400
