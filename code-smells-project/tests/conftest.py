import pytest

from app import create_app
from database import db
from models.produto import Produto
from models.usuario import Usuario


@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        admin = Usuario(nome="Admin Teste", email="admin@teste.com", tipo="admin")
        admin.set_senha("senhaadmin123")

        cliente = Usuario(nome="Cliente Teste", email="cliente@teste.com", tipo="cliente")
        cliente.set_senha("senhacliente123")

        outro_cliente = Usuario(nome="Outro Cliente", email="outro@teste.com", tipo="cliente")
        outro_cliente.set_senha("senhaoutro123")

        produto = Produto(nome="Produto Teste", descricao="desc", preco=100.0, estoque=10, categoria="geral")

        db.session.add_all([admin, cliente, outro_cliente, produto])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, email, senha):
    resp = client.post("/login", json={"email": email, "senha": senha})
    return resp.get_json()["dados"]["access_token"]


@pytest.fixture
def admin_token(client):
    return _login(client, "admin@teste.com", "senhaadmin123")


@pytest.fixture
def cliente_token(client):
    return _login(client, "cliente@teste.com", "senhacliente123")


@pytest.fixture
def outro_cliente_token(client):
    return _login(client, "outro@teste.com", "senhaoutro123")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def cliente_headers(cliente_token):
    return {"Authorization": f"Bearer {cliente_token}"}


@pytest.fixture
def outro_cliente_headers(outro_cliente_token):
    return {"Authorization": f"Bearer {outro_cliente_token}"}


@pytest.fixture
def ids(app):
    with app.app_context():
        return {
            "admin": Usuario.query.filter_by(email="admin@teste.com").first().id,
            "cliente": Usuario.query.filter_by(email="cliente@teste.com").first().id,
            "outro_cliente": Usuario.query.filter_by(email="outro@teste.com").first().id,
            "produto": Produto.query.filter_by(nome="Produto Teste").first().id,
        }
