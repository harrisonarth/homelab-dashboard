from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_METRICS = {
    "system": {
        "hostname": "test-host",
        "boot_time": "2024-01-01 00:00:00",
        "uptime_seconds": 86400,
    },
    "cpu": {
        "percent": 25.0,
        "per_core": [20.0, 30.0],
        "core_count": 2,
        "physical_cores": 1,
        "load_avg": [0.5, 0.4, 0.3],
    },
    "memory": {
        "total": 8589934592,
        "used": 4294967296,
        "available": 4294967296,
        "percent": 50.0,
        "total_gb": 8.0,
        "used_gb": 4.0,
        "available_gb": 4.0,
        "swap_total": 0,
        "swap_used": 0,
        "swap_percent": 0.0,
    },
    "disk": {
        "partitions": [
            {
                "device": "/dev/sda1",
                "mountpoint": "/",
                "fstype": "ext4",
                "total": 107374182400,
                "used": 21474836480,
                "free": 85899345920,
                "percent": 20.0,
                "total_gb": 100.0,
                "used_gb": 20.0,
                "free_gb": 80.0,
            }
        ],
        "io": {},
    },
    "network": {
        "interfaces": [
            {
                "interface": "eth0",
                "bytes_sent": 1048576,
                "bytes_recv": 2097152,
                "packets_sent": 1000,
                "packets_recv": 2000,
                "sent_mb": 1.0,
                "recv_mb": 2.0,
            }
        ]
    },
    "timestamp": "2024-03-15 14:23:01",
}


# --- Health Endpoint ---

def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# --- Dashboard Page ---

def test_dashboard_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_dashboard_returns_html():
    response = client.get("/")
    assert "text/html" in response.headers["content-type"]


# --- /api/metrics ---

def test_metrics_endpoint_returns_200():
    with patch('app.main.get_all_metrics', return_value=MOCK_METRICS):
        response = client.get("/api/metrics")
    assert response.status_code == 200


def test_metrics_endpoint_returns_json():
    with patch('app.main.get_all_metrics', return_value=MOCK_METRICS):
        response = client.get("/api/metrics")
    assert response.headers["content-type"] == "application/json"


def test_metrics_contains_all_sections():
    with patch('app.main.get_all_metrics', return_value=MOCK_METRICS):
        response = client.get("/api/metrics")
    data = response.json()
    for key in ["system", "cpu", "memory", "disk", "network", "timestamp"]:
        assert key in data, f"Missing section: {key}"


# --- Individual API Endpoints ---

def test_cpu_endpoint_returns_200():
    response = client.get("/api/cpu")
    assert response.status_code == 200


def test_memory_endpoint_returns_200():
    response = client.get("/api/memory")
    assert response.status_code == 200


def test_disk_endpoint_returns_200():
    response = client.get("/api/disk")
    assert response.status_code == 200
