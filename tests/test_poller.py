"""Tests for the models and the background poller."""

import asyncio

from api.models import Server
from api.poller import poll_server


def test_base_url():
    s = Server(id=1, name="web", host="10.0.0.1", port=8080)
    assert s.base_url() == "http://10.0.0.1:8080"


def test_poll_unknown_id_does_nothing():
    # No server with that id -> the call just returns, no error.
    asyncio.run(poll_server(99, "http://127.0.0.1:1", {}))


def test_poll_down_when_unreachable():
    s = Server(id=1, name="web", host="127.0.0.1", port=1)
    store = {1: s}
    # Port 1 refuses the connection -> status should become DOWN.
    asyncio.run(poll_server(1, s.base_url(), store))
    assert store[1].status == "DOWN"
