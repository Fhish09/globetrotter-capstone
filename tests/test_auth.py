"""Tests for registration and login."""


def test_register_success(client):
    res = client.post("/register", json={
        "username": "alice",
        "password": "secret123",
        "preferences": ["beach", "food"],
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["username"] == "alice"


def test_register_duplicate(client):
    client.post("/register", json={"username": "bob", "password": "x"})
    res = client.post("/register", json={"username": "bob", "password": "y"})
    assert res.status_code == 409


def test_register_missing_fields(client):
    res = client.post("/register", json={"username": ""})
    assert res.status_code == 400


def test_login_success(client):
    client.post("/register", json={
        "username": "carol",
        "password": "pass123",
        "preferences": ["culture"],
    })
    res = client.post("/login", json={
        "username": "carol",
        "password": "pass123",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "token" in data


def test_login_invalid(client):
    res = client.post("/login", json={
        "username": "nobody",
        "password": "wrong",
    })
    assert res.status_code == 401
