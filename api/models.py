"""Data models: the Server dataclass and the Pydantic schemas."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class Server:
    """A monitored server, kept in the in-memory store."""

    id: int
    name: str
    host: str
    port: int
    status: str = "unknown"  # unknown | UP | DEGRADED | DOWN

    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    """Payload sent by the client to register a server."""

    name: str = Field(..., min_length=1)
    host: str
    port: int = Field(8080, ge=1, le=65535)


class ServerOut(ServerIn):
    """Server returned by the API (adds the id and current status)."""

    id: int
    status: str = "unknown"
