import asyncio
import time
import httpx
from app.hosts import load_hosts

TIMEOUT = 5.0   # per-host fetch timeout
CACHE_TTL = 4.0  # seconds — just under the 5s frontend poll interval

# host_id -> (monotonic timestamp, result dict)
_cache: dict[str, tuple[float, dict]] = {}


def _build_headers(token: str) -> dict:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


async def fetch_host_metrics(host: dict, client: httpx.AsyncClient) -> dict:
    """Fetch /api/metrics from a single host. Returns error dict on failure."""
    host_id = host["id"]
    now = time.monotonic()

    # Return cached result if still fresh
    if host_id in _cache:
        ts, cached = _cache[host_id]
        if now - ts < CACHE_TTL:
            return cached

    url = f"http://{host['address']}:{host['port']}/api/metrics"
    try:
        r = await client.get(url, headers=_build_headers(host.get("token", "")))
        r.raise_for_status()
        result = {
            "host_id": host_id,
            "host_name": host["name"],
            "metrics": r.json(),
            "error": None,
        }
    except httpx.TimeoutException:
        result = {"host_id": host_id, "host_name": host["name"],
                  "metrics": None, "error": "Connection timeout"}
    except Exception as e:
        result = {"host_id": host_id, "host_name": host["name"],
                  "metrics": None, "error": str(e)}

    _cache[host_id] = (time.monotonic(), result)
    return result


async def fetch_all_metrics() -> list[dict]:
    """Fetch metrics from all enabled hosts in parallel."""
    hosts = [h for h in load_hosts() if h.get("enabled", True)]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = [fetch_host_metrics(h, client) for h in hosts]
        return await asyncio.gather(*tasks)
