"""Tests for recommendations endpoint."""


def _token(client):
    client.post("/register", json={
        "username": "recuser",
        "password": "secret",
        "preferences": ["beach", "food"],
    })
    res = client.post("/login", json={"username": "recuser", "password": "secret"})
    return res.get_json()["token"]


def test_recommendations_requires_auth(client):
    res = client.get("/recommendations")
    assert res.status_code == 401


def test_recommendations_with_auth(client):
    token = _token(client)
    res = client.get("/recommendations", headers={
        "Authorization": f"Bearer {token}"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
