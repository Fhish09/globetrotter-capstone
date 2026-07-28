"""Service-level tests for Itineraries microservice."""
import os
import sys
import datetime

import jwt
import pytest

SYS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYS_ROOT)

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from app import app, db  # noqa: E402

SECRET = "test-secret"


def _token(username="traveler"):
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {"sub": username, "iat": now, "exp": now + datetime.timedelta(hours=1)},
        SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = SECRET
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200


def test_requires_auth(client):
    res = client.get("/itineraries")
    assert res.status_code == 401


def test_create_and_list(client):
    headers = {"Authorization": f"Bearer {_token()}"}
    res = client.post("/itineraries", json={
        "title": "Kribi Weekend",
        "destinations": ["Kribi"],
    }, headers=headers)
    assert res.status_code == 201

    res = client.get("/itineraries", headers=headers)
    assert res.status_code == 200
    assert len(res.get_json()) >= 1
