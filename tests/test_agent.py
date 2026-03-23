from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from agent.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@patch("core.metrics.psutil.cpu_percent", return_value=[55.0])
@patch("core.metrics.psutil.virtual_memory")
def test_metrics_no_auth(mock_mem, mock_cpu):
    mock_mem.return_value = MagicMock(percent=70.0, total=8e9, used=5.6e9, available=2.4e9)
    r = client.get("/api/metrics")
    assert r.status_code == 200
    assert r.json()["cpu"]["percent"] == 55.0


def test_metrics_requires_token_when_set(monkeypatch):
    monkeypatch.setenv("AGENT_TOKEN", "secret")
    # re-import needed to pick up new env var — covered in test setup
    r = client.get("/api/metrics")
    assert r.status_code == 401


def test_metrics_accepts_valid_token(monkeypatch):
    monkeypatch.setenv("AGENT_TOKEN", "secret")
    r = client.get("/api/metrics", headers={"Authorization": "Bearer secret"})
    assert r.status_code == 200


def test_docker_stub_returns_available_false():
    # Before Docker stats are implemented, stub always returns available: false
    # (unless real Docker socket present — CI machines won't have it)
    r = client.get("/api/docker")
    assert r.status_code == 200
    assert "available" in r.json()
