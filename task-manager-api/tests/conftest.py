import pytest

from app import create_app
from database import db
from models.category import Category
from models.user import User


@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        admin = User(name="Admin Test", email="admin@test.com", role="admin")
        admin.set_password("adminpass123")

        user = User(name="User Test", email="user@test.com", role="user")
        user.set_password("userpass123")

        other_user = User(name="Other User", email="other@test.com", role="user")
        other_user.set_password("otherpass123")

        category = Category(name="Backend", description="Backend tasks", color="#3498db")

        db.session.add_all([admin, user, other_user, category])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, email, password):
    resp = client.post("/login", json={"email": email, "password": password})
    return resp.get_json()["token"]


@pytest.fixture
def admin_token(client):
    return _login(client, "admin@test.com", "adminpass123")


@pytest.fixture
def user_token(client):
    return _login(client, "user@test.com", "userpass123")


@pytest.fixture
def other_user_token(client):
    return _login(client, "other@test.com", "otherpass123")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def other_user_headers(other_user_token):
    return {"Authorization": f"Bearer {other_user_token}"}


@pytest.fixture
def ids(app):
    with app.app_context():
        return {
            "admin": User.query.filter_by(email="admin@test.com").first().id,
            "user": User.query.filter_by(email="user@test.com").first().id,
            "other_user": User.query.filter_by(email="other@test.com").first().id,
            "category": Category.query.filter_by(name="Backend").first().id,
        }
