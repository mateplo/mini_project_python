"""Background health checks for the monitored servers."""

import asyncio
import logging

import httpx

from .models import Server

logger = logging.getLogger(__name__)


async def poll_server(server_id: int, url: str, store: dict[int, Server]) -> None:
    """Hit {url}/health and set the server status to UP / DEGRADED / DOWN."""
    server = store.get(server_id)
    if server is None:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{url}/health")
        server.status = "UP" if resp.status_code == 200 else "DEGRADED"
    except httpx.HTTPError:
        server.status = "DOWN"
    logger.info("Polled %s (%s) -> %s", server_id, url, server.status)


async def run_poll_loop(store: dict[int, Server], interval: int = 10) -> None:
    """Poll every server concurrently, then wait `interval` seconds, forever."""
    while True:
        await asyncio.gather(
            *(poll_server(sid, s.base_url(), store) for sid, s in list(store.items()))
        )
        await asyncio.sleep(interval)
