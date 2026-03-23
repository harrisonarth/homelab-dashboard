import re
import socket
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator
from core.metrics import (
    get_all_metrics, get_cpu_metrics, get_memory_metrics,
    get_disk_metrics, get_network_metrics,
)
from app.hosts import load_hosts, add_host, remove_host, get_host
from app.aggregator import fetch_host_metrics, fetch_all_metrics


@asynccontextmanager
async def lifespan(app):
    # Ensure local host is always registered on startup
    if not any(h.get("address") == "localhost" for h in load_hosts()):
        add_host({
            "id": "local",
            "name": socket.gethostname(),
            "address": "localhost",
            "port": 8000,
            "token": "",
            "enabled": True,
        })
    yield


app = FastAPI(
    title="Homelab Dashboard",
    description="Real-time system health metrics for your homelab",
    version="1.0.0",
    lifespan=lifespan,
)

# Serve static files (JS, CSS) from the /static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates from the /templates directory
templates = Jinja2Templates(directory="templates")


class HostIn(BaseModel):
    id: str
    name: str
    address: str
    port: int = 8000
    token: str = ""
    enabled: bool = True

    @field_validator("id")
    @classmethod
    def id_must_be_url_safe(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("id must be URL-safe (letters, numbers, hyphens, underscores)")
        return v



@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard HTML page."""
    return templates.TemplateResponse(request, "index.html")


# When someone visits /api/metrics, return ALL metrics as JSON.
# This is the main endpoint — the frontend JavaScript calls this every few seconds
@app.get("/api/metrics")
async def metrics():
    """
    Return all system metrics as JSON.
    This is the endpoint the frontend polls every few seconds.
    """
    data = get_all_metrics()
    return JSONResponse(content=data)


@app.get("/api/cpu")
async def cpu():
    """Return CPU metrics only."""
    return JSONResponse(content=get_cpu_metrics())


@app.get("/api/memory")
async def memory():
    """Return memory metrics only."""
    return JSONResponse(content=get_memory_metrics())


@app.get("/api/disk")
async def disk():
    """Return disk metrics only."""
    return JSONResponse(content=get_disk_metrics())


@app.get("/api/network")
async def network():
    """Return network metrics only."""
    return JSONResponse(content=get_network_metrics())


# A simple health check endpoint.
# Monitoring tools and CI pipelines call this to confirm the server is alive.
@app.get("/health")
async def health():
    """Health check endpoint used by CI and monitoring."""
    return {"status": "ok"}


@app.get("/api/hosts")
def list_hosts():
    hosts = load_hosts()
    # Strip token values — only expose whether a token is set
    return [{**h, "token": bool(h.get("token"))} for h in hosts]


@app.post("/api/hosts", status_code=201)
def add_host_route(host: HostIn):
    # Save unconditionally — reachability is the aggregator's concern.
    # Pre-registering an offline host is valid (e.g. setting up agent later).
    try:
        add_host(host.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.delete("/api/hosts/{host_id}", status_code=204)
def delete_host_route(host_id: str):
    if not remove_host(host_id):
        raise HTTPException(status_code=404, detail="Host not found")


@app.get("/api/hosts/{host_id}/metrics")
async def host_metrics(host_id: str):
    host = get_host(host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    async with httpx.AsyncClient(timeout=5.0) as client:
        return await fetch_host_metrics(host, client)


@app.get("/api/all-metrics")
async def all_metrics():
    results = await fetch_all_metrics()
    return {r["host_id"]: r for r in results}
