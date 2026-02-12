from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

class DockerConfig(BaseModel):
    service: str
    port: Optional[int] = None
    health_url: Optional[str] = None
    compose_file: str = "docker/mcp-servers/docker-compose.yml"

class LocalConfig(BaseModel):
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)

class MCPServerDefinition(BaseModel):
    name: str = "" # Populated after load
    transport: str  # http, http-sse, stdio
    docker: DockerConfig
    local: Optional[LocalConfig] = None

class MCPRegistry:
    def __init__(self, registry_path: Optional[str] = None):
        if registry_path:
            self.path = Path(registry_path)
        else:
            self.path = Path(__file__).parent / "registry.yaml"
        self.servers: Dict[str, MCPServerDefinition] = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
            
        with open(self.path, "r") as f:
            data = yaml.safe_load(f)
            
        if not data or "servers" not in data:
            return
            
        for name, config in data["servers"].items():
            server_def = MCPServerDefinition(**config)
            server_def.name = name
            self.servers[name] = server_def

    def get_server(self, name: str) -> Optional[MCPServerDefinition]:
        return self.servers.get(name)

    def list_servers(self) -> List[MCPServerDefinition]:
        return list(self.servers.values())
