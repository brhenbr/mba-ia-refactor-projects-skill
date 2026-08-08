def test_protected_route_requires_token(client):
    resp = client.post("/pedidos", json={"itens": []})
    assert resp.status_code == 401


def test_login_returns_token(client):
    resp = client.post("/login", json={"email": "cliente@teste.com", "senha": "senhacliente123"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()["dados"]


def test_login_wrong_password_fails(client):
    resp = client.post("/login", json={"email": "cliente@teste.com", "senha": "errada12345"})
    assert resp.status_code == 401


def test_user_cannot_access_another_users_orders(client, cliente_headers, ids):
    resp = client.get(f"/pedidos/usuario/{ids['outro_cliente']}", headers=cliente_headers)
    assert resp.status_code == 403


def test_user_can_access_own_orders(client, cliente_headers, ids):
    resp = client.get(f"/pedidos/usuario/{ids['cliente']}", headers=cliente_headers)
    assert resp.status_code == 200


def test_admin_can_access_any_users_orders(client, admin_headers, ids):
    resp = client.get(f"/pedidos/usuario/{ids['cliente']}", headers=admin_headers)
    assert resp.status_code == 200


def test_non_admin_cannot_create_product(client, cliente_headers):
    resp = client.post("/produtos", json={"nome": "X", "preco": 1, "estoque": 1}, headers=cliente_headers)
    assert resp.status_code == 403


def test_admin_can_create_product(client, admin_headers):
    resp = client.post(
        "/produtos",
        json={"nome": "Produto Novo", "preco": 10, "estoque": 5, "categoria": "geral"},
        headers=admin_headers,
    )
    assert resp.status_code == 201


def test_non_admin_cannot_list_all_orders(client, cliente_headers):
    resp = client.get("/pedidos", headers=cliente_headers)
    assert resp.status_code == 403


def test_order_is_created_for_authenticated_user_not_request_body(client, cliente_headers, ids):
    """Garante que o usuario_id do pedido vem do JWT, não de um campo do body.
    O schema nem aceita um campo usuario_id no payload (unknown fields são rejeitados)."""
    resp = client.post(
        "/pedidos",
        json={"itens": [{"produto_id": ids["produto"], "quantidade": 1}]},
        headers=cliente_headers,
    )
    assert resp.status_code == 201
    assert resp.get_json()["dados"]["usuario_id"] == ids["cliente"]


def test_order_payload_rejects_unknown_fields(client, cliente_headers, ids):
    resp = client.post(
        "/pedidos",
        json={"itens": [{"produto_id": ids["produto"], "quantidade": 1}], "usuario_id": 999999},
        headers=cliente_headers,
    )
    assert resp.status_code == 400
