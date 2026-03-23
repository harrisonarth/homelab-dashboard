import os
from fastapi import FastAPI, HTTPException, Request
from core.metrics import (
    get_all_metrics, get_cpu_metrics, get_memory_metrics,
    get_disk_metrics, get_network_metrics,
)

app = FastAPI(title="homelab-agent")


def check_auth(request: Request):
    """Optional bearer token auth. Reads token at call time so env changes are picked up."""
    token = os.getenv("AGENT_TOKEN", "")
    if not token:
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/metrics")
def metrics(request: Request):
    check_auth(request)
    return get_all_metrics()


@app.get("/api/cpu")
def cpu(request: Request):
    check_auth(request)
    return get_cpu_metrics()


@app.get("/api/memory")
def memory(request: Request):
    check_auth(request)
    return get_memory_metrics()


@app.get("/api/disk")
def disk(request: Request):
    check_auth(request)
    return get_disk_metrics()


@app.get("/api/network")
def network(request: Request):
    check_auth(request)
    return get_network_metrics()


try:
    import docker as docker_sdk
    docker_sdk.from_env().ping()
    DOCKER_AVAILABLE = True
except Exception:
    DOCKER_AVAILABLE = False


@app.get("/api/docker")
def docker_stats(request: Request):
    check_auth(request)
    if not DOCKER_AVAILABLE:
        return {"available": False, "containers": []}
    # Full implementation comes in a later phase
    return {"available": True, "containers": []}
