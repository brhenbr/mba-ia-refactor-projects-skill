from sqlalchemy import event

from database import db


def test_criar_pedido_sucesso(client, cliente_headers, ids):
    resp = client.post(
        "/pedidos",
        json={"itens": [{"produto_id": ids["produto"], "quantidade": 2}]},
        headers=cliente_headers,
    )
    assert resp.status_code == 201
    dados = resp.get_json()["dados"]
    assert dados["total"] == 200.0
    assert len(dados["itens"]) == 1


def test_criar_pedido_estoque_insuficiente(client, cliente_headers, ids):
    resp = client.post(
        "/pedidos",
        json={"itens": [{"produto_id": ids["produto"], "quantidade": 9999}]},
        headers=cliente_headers,
    )
    assert resp.status_code == 400


def test_criar_pedido_produto_inexistente(client, cliente_headers):
    resp = client.post(
        "/pedidos",
        json={"itens": [{"produto_id": 999999, "quantidade": 1}]},
        headers=cliente_headers,
    )
    assert resp.status_code == 400


def test_estoque_nao_e_debitado_se_algum_item_falhar(client, cliente_headers, ids):
    """Sem transação atômica, o item válido processado antes do inválido deixaria
    estoque debitado mesmo com o pedido inteiro falhando. Aqui isso não deve ocorrer."""
    client.post(
        "/pedidos",
        json={"itens": [
            {"produto_id": ids["produto"], "quantidade": 1},
            {"produto_id": 999999, "quantidade": 1},
        ]},
        headers=cliente_headers,
    )

    resp = client.get(f"/produtos/{ids['produto']}")
    assert resp.get_json()["dados"]["estoque"] == 10


def test_listar_pedidos_usuario_nao_gera_n_mais_1_queries(app, client, cliente_headers, ids):
    for _ in range(3):
        client.post(
            "/pedidos",
            json={"itens": [{"produto_id": ids["produto"], "quantidade": 1}]},
            headers=cliente_headers,
        )

    contador = {"n": 0}

    def _contar(*args, **kwargs):
        contador["n"] += 1

    with app.app_context():
        event.listen(db.engine, "before_cursor_execute", _contar)
        try:
            resp = client.get(f"/pedidos/usuario/{ids['cliente']}", headers=cliente_headers)
        finally:
            event.remove(db.engine, "before_cursor_execute", _contar)

    assert resp.status_code == 200
    assert len(resp.get_json()["dados"]) == 3
    # Eager loading: número de queries não deve crescer com o número de pedidos/itens
    assert contador["n"] <= 5
