"""Tests for destination search."""


def test_list_destinations(client):
    res = client.get("/destinations?source=local")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    # Seed data should have at least a few entries
    assert len(data) >= 1


def test_search_by_query(client):
    res = client.get("/destinations?source=local&q=paris")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    if data:
        assert any("paris" in d.get("name", "").lower() for d in data)


def test_filter_by_tag(client):
    res = client.get("/destinations?source=local&tag=beach")
    assert res.status_code == 200
    data = res.get_json()
    for dest in data:
        tags = [t.lower() for t in dest.get("tags", [])]
        assert "beach" in tags
