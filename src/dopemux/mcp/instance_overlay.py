import json
import logging
import re
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class InstanceOverlayManager:
    """
    Generates instance-scoped env and compose overlays.
    Handles deterministic port allocation.
    """
    PORT_OFFSETS = {
        "ConPort": 4,
        "Serena": 6,
        "Dope-Context": 10,
        "Dope-Memory": 20,
        "LiteLLM": 1000 
    }

    def __init__(self, project_root: Path, instance_id: str):
        self.project_root = project_root
        self.instance_id = instance_id
        self.instance_dir = self.project_root / ".dopemux" / "instances" / instance_id
        self.base_port = self._calculate_base_port()
        self.port_map = self._generate_port_map()

    def _calculate_base_port(self) -> int:
        if not self.instance_id:
            return 3000
        
        first_char = self.instance_id[0].upper()
        if 'A' <= first_char <= 'Z':
            offset = ord(first_char) - ord('A')
            return 3000 + (offset * 100)
        
        import hashlib
        h = hashlib.md5(self.instance_id.encode()).hexdigest()
        offset = int(h[:2], 16) % 30
        return 3000 + (offset * 100)

    def _generate_port_map(self) -> Dict[str, int]:
        ports = {}
        for name, offset in self.PORT_OFFSETS.items():
            ports[name] = self.base_port + offset
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
        project_id = self.project_root.name
        name = f"dopemux_{project_id}_{self.instance_id}".lower()
        # Sanitize for Docker Compose
        return re.sub(r'[^a-z0-9_-]', '_', name)

    def write_mcp_env(self) -> Path:
        env_path = self.instance_dir / "mcp.env"
        
        # Safely get ports
        def get_p(name): return self.port_map.get(name, 0)

        lines = [
            f"# Generated for instance: {self.instance_id}",
            f"COMPOSE_PROJECT_NAME={self.get_compose_project_name()}",
            "COMPOSE_FILE=compose.yml",
            f"DOPEMUX_INSTANCE_ID={self.instance_id}",
            f"CONPORT_CONTAINER_NAME={'mcp-conport' if not self.instance_id or self.instance_id == 'A' else f'mcp-conport_{self.instance_id}'}",
            f"SERENA_CONTAINER_NAME={'dopemux-mcp-serena' if not self.instance_id or self.instance_id == 'A' else f'dopemux-mcp-serena_{self.instance_id}'}",
            f"CONPORT_HTTP_PORT={get_p('ConPort')}",
            f"CONPORT_MCP_PORT={get_p('ConPort') + 1}",
            f"CONPORT_INFO_PORT={get_p('ConPort') + 1000}",
            f"SERENA_PORT={get_p('Serena')}",
            f"SERENA_HTTP_PORT={get_p('Serena') + 1000}",
            f"DOPE_CONTEXT_PORT={get_p('Dope-Context')}",
            f"DOPE_MEMORY_PORT={get_p('Dope-Memory')}",
            f"PAL_PORT={self.base_port + 3}",
            f"EXA_PORT={self.base_port + 11}",
            f"DESKTOP_COMMANDER_PORT={self.base_port + 12}",
            f"LEANTIME_BRIDGE_PORT={self.base_port + 15}",
            f"GPT_RESEARCHER_PORT={self.base_port + 9}",
            f"DOPEMUX_CONPORT_PORT={get_p('ConPort')}",
            f"DOPEMUX_SERENA_PORT={get_p('Serena')}",
            f"DOPEMUX_CONTEXT_PORT={get_p('Dope-Context')}",
            f"DOPEMUX_MEMORY_PORT={get_p('Dope-Memory')}",
            f"DOPEMUX_LITELLM_PORT={get_p('LiteLLM')}",
        ]
        
        with open(env_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        return env_path

    def write_compose_override(self) -> Path:
        compose_path = self.instance_dir / "mcp.compose.override.yml"
        
        # Helper to generate service override only if port exists
        services = []
        if "ConPort" in self.port_map:
            services.append(
                "  conport:\n"
                f"    container_name: {'mcp-conport' if not self.instance_id or self.instance_id == 'A' else f'mcp-conport_{self.instance_id}'}\n"
                "    ports:\n"
                f"      - \"{self.port_map['ConPort']}:3004\"\n"
                f"      - \"{self.port_map['ConPort'] + 1}:3005\"\n"
                f"      - \"{self.port_map['ConPort'] + 1000}:4004\""
            )
        if "Serena" in self.port_map:
            services.append(
                "  serena:\n"
                f"    container_name: {'dopemux-mcp-serena' if not self.instance_id or self.instance_id == 'A' else f'dopemux-mcp-serena_{self.instance_id}'}\n"
                "    ports:\n"
                f"      - \"{self.port_map['Serena']}:3006\"\n"
                f"      - \"{self.port_map['Serena'] + 1000}:4006\""
            )
        if "Dope-Context" in self.port_map:
            services.append(f"  dope-context:\n    ports:\n      - \"{self.port_map['Dope-Context']}:3010\"")
        if "Dope-Memory" in self.port_map:
            services.append(f"  dope-memory:\n    ports:\n      - \"{self.port_map['Dope-Memory']}:3020\"")
        if "LiteLLM" in self.port_map:
            services.append(f"  litellm:\n    ports:\n      - \"{self.port_map['LiteLLM']}:4000\"")

        content = "services:\n" + "\n".join(services)
        
        with open(compose_path, "w") as f:
            f.write(content)
        return compose_path
