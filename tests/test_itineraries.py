"""Tests for itineraries (auth required)."""


def _register_and_login(client, username="traveler", password="secret"):
    client.post("/register", json={
        "username": username,
        "password": password,
        "preferences": ["adventure"],
    })
    res = client.post("/login", json={"username": username, "password": password})
    return res.get_json()["token"]


def test_itineraries_requires_auth(client):
    res = client.get("/itineraries")
    assert res.status_code == 401


def test_create_and_list_itinerary(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/itineraries", json={
        "title": "Cameroon Trip",
        "destinations": ["Kribi", "Limbe"],
        "start_date": "2026-08-01",
        "end_date": "2026-08-10",
    }, headers=headers)
    assert res.status_code == 201
    created = res.get_json()
    assert created["title"] == "Cameroon Trip"

    res = client.get("/itineraries", headers=headers)
    assert res.status_code == 200
    trips = res.get_json()
    assert len(trips) >= 1
    assert trips[0]["title"] == "Cameroon Trip"


def test_create_itinerary_missing_title(client):
    token = _register_and_login(client, username="other")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/itineraries", json={"destinations": ["Paris"]}, headers=headers)
    assert res.status_code == 400
