import os
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class InstanceOverlayManager:
    """
    Generates instance-scoped env and compose overlays.
    Handles deterministic port allocation.
    """
    PORT_OFFSETS = {
        "PAL": 3,
        "ConPort": 4,
        "Serena": 6,
        "Dope-Context": 10,
        "Dope-Memory": 20,
        "LiteLLM": 1000 # 4000 relative to 3000? No, let's keep it consistent.
    }

    def __init__(self, project_root: Path, instance_id: str):
        self.project_root = project_root
        self.instance_id = instance_id
        self.instance_dir = self.project_root / ".dopemux" / "instances" / instance_id
        self.base_port = self._calculate_base_port()
        self.port_map = self._generate_port_map()

    def _calculate_base_port(self) -> int:
        """
        Deterministic base port based on instance_id.
        A -> 3000, B -> 3100, C -> 3200, etc.
        """
        if not self.instance_id or len(self.instance_id) == 0:
            return 3000
        
        # Simple mapping for common letters, otherwise use hash-based offset
        first_char = self.instance_id[0].upper()
        if 'A' <= first_char <= 'Z':
            offset = ord(first_char) - ord('A')
            return 3000 + (offset * 100)
        
        # Fallback to hash-based for non-alpha instance IDs
        import hashlib
        h = hashlib.md5(self.instance_id.encode()).hexdigest()
        offset = int(h[:2], 16) % 30 # Up to 3000 + 30*100 = 6000
        return 3000 + (offset * 100)

    def _generate_port_map(self) -> Dict[str, int]:
        ports = {}
        for name, offset in self.PORT_OFFSETS.items():
            ports[name] = self.base_port + offset
        
        # Special case for LiteLLM - default is usually 4000
        # If base is 3000, LiteLLM is 4000.
        # If base is 3100, LiteLLM is 4100.
        ports["LiteLLM"] = self.base_port + 1000
        return ports

    def materialize(self) -> Dict[str, Any]:
        """Generates the overlay files in .dopemux/instances/<id>/"""
        self.instance_dir.mkdir(parents=True, exist_ok=True)
        
        env_path = self.write_mcp_env()
        compose_path = self.write_compose_override()
        
        # Save port map for reports
        with open(self.instance_dir / "PORT_MAP.json", "w") as f:
            json.dump(self.port_map, f, indent=2)

        return {
            "instance_dir": str(self.instance_dir),
            "env_path": str(env_path),
            "compose_path": str(compose_path),
            "port_map": self.port_map,
            "base_port": self.base_port,
            "compose_project_name": self.get_compose_project_name()
        }

    def get_compose_project_name(self) -> str:
        # Use folder name as project_id
        project_id = self.project_root.name
        return f"dopemux_{project_id}_{self.instance_id}"

    def write_mcp_env(self) -> Path:
        env_path = self.instance_dir / "mcp.env"
        lines = [
            f"# Generated for instance: {self.instance_id}",
            f"COMPOSE_PROJECT_NAME={self.get_compose_project_name()}",
            f"DOPEMUX_INSTANCE_ID={self.instance_id}",
            f"DOPEMUX_WORKSPACE_ID={self.instance_id}", # Legacy compatibility
            f"DOPEMUX_CONPORT_PORT={self.port_map['ConPort']}",
            f"DOPEMUX_PAL_PORT={self.port_map['PAL']}",
            f"DOPEMUX_SERENA_PORT={self.port_map['Serena']}",
            f"DOPEMUX_CONTEXT_PORT={self.port_map['Dope-Context']}",
            f"DOPEMUX_MEMORY_PORT={self.port_map['Dope-Memory']}",
            f"DOPEMUX_LITELLM_PORT={self.port_map['LiteLLM']}",
        ]
        
        with open(env_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        return env_path

    def write_compose_override(self) -> Path:
        compose_path = self.instance_dir / "mcp.compose.override.yml"
        
        # We generate a simple override that maps ports based on our allocator
        content = f"""version: '3.8'
services:
  conport:
    ports:
      - "{self.port_map['ConPort']}:3004"
  pal:
    ports:
      - "{self.port_map['PAL']}:3003"
  serena:
    ports:
      - "{self.port_map['Serena']}:3006"
  dope-context:
    ports:
      - "{self.port_map['Dope-Context']}:3010"
  dope-memory:
    ports:
      - "{self.port_map['Dope-Memory']}:3020"
  litellm:
    ports:
      - "{self.port_map['LiteLLM']}:4000"
"""
        with open(compose_path, "w") as f:
            f.write(content)
        return compose_path
