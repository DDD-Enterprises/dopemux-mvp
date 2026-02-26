from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


DEFAULT_COMPOSE_FILE = "compose.yml"
MCPTransport = Literal["http", "http-sse", "stdio"]


class DockerConfig(BaseModel):
    """Docker runtime metadata for an MCP server."""

    model_config = ConfigDict(extra="forbid")

    service: str
    compose_file: str = DEFAULT_COMPOSE_FILE
    port: Optional[int] = None
    health_url: Optional[str] = None
    exec: List[str] = Field(default_factory=list)


class LocalConfig(BaseModel):
    """Local runtime metadata for an MCP server."""

    model_config = ConfigDict(extra="forbid")

    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)


class MCPServerDefinition(BaseModel):
    """Canonical MCP server definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = ""
    transport: MCPTransport
    docker: Optional[DockerConfig] = None
    local: Optional[LocalConfig] = None
    default_enabled: bool = True
    required_for_auto: bool = False

    @model_validator(mode="after")
    def validate_transport_requirements(self) -> "MCPServerDefinition":
        """Validate transport-specific requirements."""
        if self.transport in ("http", "http-sse"):
            if not self.docker:
                raise ValueError(f"{self.name or 'server'} requires docker config for HTTP transport")
            if self.docker.port is None:
                raise ValueError(f"{self.name or 'server'} requires docker.port for HTTP transport")
        if self.transport == "stdio" and not (self.local and self.local.command) and not (
            self.docker and self.docker.exec
        ):
            raise ValueError(
                f"{self.name or 'server'} requires local.command or docker.exec for stdio transport"
            )
        return self


class MCPRegistry:
    """Loads canonical MCP definitions from registry.yaml."""

    def __init__(self, registry_path: Optional[str] = None):
        self.path = Path(registry_path) if registry_path else Path(__file__).with_name("registry.yaml")
        self.servers: Dict[str, MCPServerDefinition] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"MCP registry not found: {self.path}")

        with self.path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        raw_servers = data.get("servers")
        if not isinstance(raw_servers, dict):
            raise ValueError(f"Invalid MCP registry format in {self.path}: missing 'servers' mapping")

        for name, config in raw_servers.items():
            if not isinstance(config, dict):
                raise ValueError(f"Invalid MCP registry entry for '{name}': expected mapping")
            server_def = MCPServerDefinition(name=name, **config)
            self.servers[name] = server_def

    def get_server(self, name: str) -> Optional[MCPServerDefinition]:
        return self.servers.get(name)

    def list_servers(self) -> List[MCPServerDefinition]:
        return [self.servers[name] for name in sorted(self.servers.keys())]

    def default_servers(self) -> List[MCPServerDefinition]:
        return [server for server in self.list_servers() if server.default_enabled]
