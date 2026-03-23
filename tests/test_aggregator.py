import pytest
import respx
import httpx
import app.aggregator as aggregator_mod
from app.aggregator import fetch_host_metrics


@pytest.fixture(autouse=True)
def clear_cache():
    aggregator_mod._cache.clear()

@pytest.mark.asyncio
@respx.mock
async def test_fetch_host_metrics_success():
    host = {"id": "pi4", "name": "Pi4", "address": "192.168.1.10",
            "port": 8000, "token": ""}
    respx.get("http://192.168.1.10:8000/api/metrics").mock(
        return_value=httpx.Response(200, json={"cpu": {}, "memory": {}})
    )
    async with httpx.AsyncClient() as client:
        result = await fetch_host_metrics(host, client)
    assert result["error"] is None
    assert result["metrics"] is not None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_host_metrics_timeout():
    host = {"id": "pi4", "name": "Pi4", "address": "192.168.1.10",
            "port": 8000, "token": ""}
    respx.get("http://192.168.1.10:8000/api/metrics").mock(
        side_effect=httpx.TimeoutException("timeout")
    )
    async with httpx.AsyncClient() as client:
        result = await fetch_host_metrics(host, client)
    assert "timeout" in result["error"].lower()
    assert result["metrics"] is None