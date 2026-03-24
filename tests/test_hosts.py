import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def tmp_hosts_config(tmp_path, monkeypatch):
    """Point HOSTS_CONFIG at a temp file for each test — no shared state."""
    config = tmp_path / "hosts.yaml"
    monkeypatch.setenv("HOSTS_CONFIG", str(config))
    # Re-import hosts module so HOSTS_CONFIG path is picked up
    import app.hosts as hosts_mod
    from pathlib import Path
    hosts_mod.HOSTS_CONFIG = Path(str(config))
    yield config


@pytest.fixture()
def client(tmp_hosts_config):
    # Import app after the env var is set so startup sees the temp path
    from app.main import app
    return TestClient(app)


# --- GET /api/hosts ---

def test_list_hosts_empty(client):
    r = client.get("/api/hosts")
    assert r.status_code == 200
    # startup auto-registers local; filter it out to check no extras
    hosts = [h for h in r.json() if h["id"] != "local"]
    assert hosts == []


# --- POST /api/hosts ---

def test_add_host_returns_201(client):
    payload = {"id": "pi4", "name": "Raspberry Pi 4", "address": "192.168.1.10"}
    r = client.post("/api/hosts", json=payload)
    assert r.status_code == 201


def test_add_host_appears_in_list(client):
    payload = {"id": "pi4", "name": "Raspberry Pi 4", "address": "192.168.1.10"}
    client.post("/api/hosts", json=payload)
    hosts = client.get("/api/hosts").json()
    ids = [h["id"] for h in hosts]
    assert "pi4" in ids


def test_add_duplicate_host_returns_409(client):
    payload = {"id": "pi4", "name": "Raspberry Pi 4", "address": "192.168.1.10"}
    client.post("/api/hosts", json=payload)
    r = client.post("/api/hosts", json=payload)
    assert r.status_code == 409


def test_token_not_exposed_in_list(client):
    payload = {"id": "pi4", "name": "Pi", "address": "192.168.1.10", "token": "mysecret"}
    client.post("/api/hosts", json=payload)
    hosts = client.get("/api/hosts").json()
    pi4 = next(h for h in hosts if h["id"] == "pi4")
    assert pi4["token"] is True  # bool, not the secret string


# --- DELETE /api/hosts/{id} ---

def test_delete_host(client):
    client.post("/api/hosts", json={"id": "pi4", "name": "Pi", "address": "192.168.1.10"})
    r = client.delete("/api/hosts/pi4")
    assert r.status_code == 204


def test_delete_removes_host_from_list(client):
    client.post("/api/hosts", json={"id": "pi4", "name": "Pi", "address": "192.168.1.10"})
    client.delete("/api/hosts/pi4")
    ids = [h["id"] for h in client.get("/api/hosts").json()]
    assert "pi4" not in ids


def test_delete_nonexistent_returns_404(client):
    r = client.delete("/api/hosts/doesnotexist")
    assert r.status_code == 404
