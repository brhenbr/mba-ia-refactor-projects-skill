def test_sql_injection_no_login_bypass(client):
    resp = client.post("/login", json={"email": "' OR '1'='1", "senha": "' OR '1'='1"})
    assert resp.status_code in (400, 401)


def test_sql_injection_in_search_returns_safe_results(client):
    resp = client.get("/produtos/busca", query_string={"q": "x' OR '1'='1"})
    assert resp.status_code == 200
    assert resp.get_json()["dados"] == []


def test_password_never_returned_in_api(client, admin_headers, ids):
    resp = client.get(f"/usuarios/{ids['admin']}", headers=admin_headers)
    body = resp.get_json()
    assert "senha" not in body["dados"]
    assert "senha_hash" not in body["dados"]


def test_password_is_hashed_in_database(app):
    from models.usuario import Usuario

    with app.app_context():
        usuario = Usuario.query.filter_by(email="cliente@teste.com").first()
        assert usuario.senha_hash != "senhacliente123"
        assert usuario.senha_hash.startswith("$2b$")


def test_health_does_not_leak_secrets(client):
    resp = client.get("/health")
    body = resp.get_json()
    assert "secret_key" not in body
    assert "debug" not in body


def test_admin_query_endpoint_removed(client):
    resp = client.post("/admin/query", json={"sql": "SELECT 1"})
    assert resp.status_code == 404


def test_reset_db_requires_admin(client, cliente_headers):
    resp = client.post("/admin/reset-db", headers=cliente_headers)
    assert resp.status_code == 403


def test_reset_db_requires_auth(client):
    resp = client.post("/admin/reset-db")
    assert resp.status_code == 401
