def _create_task(client, headers, **overrides):
    payload = {"title": "Report source task", "priority": 2}
    payload.update(overrides)
    return client.post("/tasks", json=payload, headers=headers)


def test_summary_requires_admin(client, user_headers):
    resp = client.get("/reports/summary", headers=user_headers)
    assert resp.status_code == 403


def test_summary_allowed_for_admin(client, admin_headers, user_headers):
    _create_task(client, user_headers, status="done")

    resp = client.get("/reports/summary", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["overview"]["total_tasks"] >= 1
    assert body["tasks_by_status"]["done"] >= 1


def test_user_report_owner_access(client, user_headers, ids):
    resp = client.get(f"/reports/user/{ids['user']}", headers=user_headers)
    assert resp.status_code == 200


def test_user_report_forbidden_for_other_user(client, user_headers, ids):
    resp = client.get(f"/reports/user/{ids['other_user']}", headers=user_headers)
    assert resp.status_code == 403


def test_admin_can_access_any_user_report(client, admin_headers, ids):
    resp = client.get(f"/reports/user/{ids['user']}", headers=admin_headers)
    assert resp.status_code == 200
