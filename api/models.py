"""Data models: the Server dataclass and the Pydantic schemas."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class Server:
    id: int
    name: str
    host: str
    port: int
    status: str = "unknown"

    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    name: str = Field(..., min_length=1)
    host: str
    port: int = Field(8080, ge=1, le=65535)


class ServerOut(ServerIn):
    id: int
    status: str = "unknown"
