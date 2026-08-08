def test_listar_produtos_publico(client):
    resp = client.get("/produtos")
    assert resp.status_code == 200
    assert resp.get_json()["sucesso"] is True


def test_criar_produto_categoria_invalida(client, admin_headers):
    resp = client.post(
        "/produtos",
        json={"nome": "X", "preco": 1, "estoque": 1, "categoria": "categoria-inexistente"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_criar_produto_preco_negativo(client, admin_headers):
    resp = client.post(
        "/produtos",
        json={"nome": "X", "preco": -1, "estoque": 1},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_buscar_produto_inexistente(client):
    resp = client.get("/produtos/999999")
    assert resp.status_code == 404
