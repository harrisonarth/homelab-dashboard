from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.metrics import (
    get_all_metrics, get_cpu_metrics, get_memory_metrics,
    get_disk_metrics, get_network_metrics,
)

app = FastAPI(
    title="Homelab Dashboard",
    description="Real-time system health metrics for your homelab",
    version="1.0.0",
)

# Serve static files (JS, CSS) from the /static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates from the /templates directory
templates = Jinja2Templates(directory="templates")


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
