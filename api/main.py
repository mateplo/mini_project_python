"""FastAPI app: metrics, websocket and server CRUD.

Run: uvicorn api.main:app --reload --port 8000
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)

from .auth import verify_api_key
from .metrics import get_system_metrics
from .models import Server, ServerIn, ServerOut
from .poller import poll_server, run_poll_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# In-memory store. Keys are server ids, values the Server dataclasses.
_servers: dict[int, Server] = {}
_next_id: int = 1


def _to_out(server: Server) -> ServerOut:
    """Convert an internal Server into its API response model."""
    return ServerOut(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        status=server.status,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run the background poll loop while the app is alive, cancel it on shutdown."""
    task = asyncio.create_task(run_poll_loop(_servers))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="DevOps Monitor", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> dict:
    """Return a one-shot snapshot of the host metrics."""
    return get_system_metrics()


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket) -> None:
    """Stream the metrics as JSON, one frame per second, until the client leaves."""
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(get_system_metrics()))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Client closed the tab — nothing to clean up.
        pass


@app.post("/servers", response_model=ServerOut, status_code=201)
async def add_server(
    server: ServerIn,
    _: Annotated[str, Depends(verify_api_key)],
) -> ServerOut:
    """Register a new server (requires the API key)."""
    global _next_id
    new = Server(
        id=_next_id,
        name=server.name,
        host=server.host,
        port=server.port,
    )
    _servers[new.id] = new
    _next_id += 1
    return _to_out(new)


@app.get("/servers", response_model=list[ServerOut])
async def list_servers(status: str | None = None) -> list[ServerOut]:
    """List servers, optionally filtered by status (e.g. ?status=UP)."""
    servers = [_to_out(s) for s in _servers.values()]
    if status is not None:
        servers = [s for s in servers if s.status == status]
    return servers


@app.get("/servers/{server_id}", response_model=ServerOut)
async def get_server(server_id: int) -> ServerOut:
    """Return a single server, or 404 if it does not exist."""
    server = _servers.get(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return _to_out(server)


@app.delete("/servers/{server_id}", status_code=204)
async def delete_server(
    server_id: int,
    _: Annotated[str, Depends(verify_api_key)],
) -> None:
    """Delete a server (requires the API key), or 404 if unknown."""
    if server_id not in _servers:
        raise HTTPException(status_code=404, detail="Server not found")
    del _servers[server_id]


@app.post("/servers/{server_id}/check", status_code=202)
async def check_server(server_id: int, background_tasks: BackgroundTasks) -> dict:
    """Trigger a one-off health check for a server, run in the background."""
    server = _servers.get(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    background_tasks.add_task(poll_server, server_id, server.base_url(), _servers)
    return {"status": "check scheduled", "id": server_id}
