"""Route tests using FastAPI's TestClient."""

from fastapi.testclient import TestClient

from api.auth import API_KEY
from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "cpu_percent" in r.json()


def test_post_server_without_key():
    r = client.post(
        "/servers", json={"name": "web", "host": "localhost", "port": 8080}
    )
    assert r.status_code == 403


def test_post_server_with_key_then_listed():
    r = client.post(
        "/servers",
        json={"name": "web", "host": "localhost", "port": 8080},
        headers={"X-API-Key": API_KEY},
    )
    assert r.status_code == 201
    server_id = r.json()["id"]
    assert r.json()["status"] == "unknown"

    listed = client.get("/servers")
    assert listed.status_code == 200
    assert any(s["id"] == server_id for s in listed.json())


def test_get_nonexistent_server():
    r = client.get("/servers/99999")
    assert r.status_code == 404


def test_delete_server():
    created = client.post(
        "/servers",
        json={"name": "tmp", "host": "localhost", "port": 9000},
        headers={"X-API-Key": API_KEY},
    )
    server_id = created.json()["id"]

    r = client.delete(f"/servers/{server_id}", headers={"X-API-Key": API_KEY})
    assert r.status_code == 204

    assert client.get(f"/servers/{server_id}").status_code == 404
    assert client.delete(
        f"/servers/{server_id}", headers={"X-API-Key": API_KEY}
    ).status_code == 404


def test_list_servers_status_filter():
    r = client.get("/servers", params={"status": "UP"})
    assert r.status_code == 200
    assert all(s["status"] == "UP" for s in r.json())


def test_check_unknown_server():
    r = client.post("/servers/99999/check")
    assert r.status_code == 404
