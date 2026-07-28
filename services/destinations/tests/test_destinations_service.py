"""Service-level tests for Destinations microservice."""
import os
import sys

import pytest

SYS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYS_ROOT)

from app import app  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["service"] == "destinations"


def test_list_local(client):
    res = client.get("/destinations?source=local")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)


def test_search_query(client):
    res = client.get("/destinations?source=local&q=a")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
