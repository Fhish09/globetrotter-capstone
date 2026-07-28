"""Service-level tests for Auth microservice (SQLite in-memory)."""
import os
import sys

import pytest

# Ensure service root is importable
SYS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYS_ROOT)

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import app, db  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["service"] == "auth"


def test_register_and_login(client):
    res = client.post("/register", json={
        "username": "alice",
        "password": "secret",
        "preferences": ["beach"],
    })
    assert res.status_code == 201

    res = client.post("/login", json={"username": "alice", "password": "secret"})
    assert res.status_code == 200
    assert "token" in res.get_json()


def test_register_duplicate(client):
    client.post("/register", json={"username": "bob", "password": "x"})
    res = client.post("/register", json={"username": "bob", "password": "y"})
    assert res.status_code == 409


def test_me_requires_auth(client):
    res = client.get("/me")
    assert res.status_code == 401
