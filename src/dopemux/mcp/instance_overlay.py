"""Instance-scoped env/compose overlays with unified port allocation.

Historically used a letter/md5 base port map independent of ``mcp init``.
Packet 004 routes catalog-aligned ports through the lease allocator when a
catalog is available, keeping overlay generation consistent with init/repair.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

logger = logging.getLogger(__name__)


class InstanceOverlayManager:
    """
    Generates instance-scoped env and compose overlays.
    Port assignment prefers the lease allocator (Packet 004).
    """

    # Legacy offsets retained only as fallback when catalog/allocator unavailable
    PORT_OFFSETS = {
        "ConPort": 4,
        "Serena": 6,
        "Dope-Context": 10,
        "Dope-Memory": 20,
        "LiteLLM": 1000,
    }

    def __init__(
        self,
        project_root: Path,
        instance_id: str,
        *,
        catalog: Optional[Mapping[str, Any]] = None,
        worktree: Optional[str | Path] = None,
        persist_leases: bool = False,
    ):
        self.project_root = Path(project_root)
        self.instance_id = instance_id or ""
        self.instance_dir = self.project_root / ".dopemux" / "instances" / (instance_id or "A")
        self.catalog = catalog
        self.worktree = str(Path(worktree or project_root).resolve())
        self.persist_leases = persist_leases
        self.base_port = self._calculate_base_port()
        self.port_map = self._generate_port_map()
        self.env_ports: Dict[str, int] = {}
        self._allocator_used = False
        self._try_lease_allocator()

    def _calculate_base_port(self) -> int:
        if not self.instance_id:
            return 3000

        first_char = self.instance_id[0].upper()
        if "A" <= first_char <= "Z":
            offset = ord(first_char) - ord("A")
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

    def _try_lease_allocator(self) -> None:
        """Prefer lease allocator for catalog per-worktree services."""
        catalog = self.catalog
        if catalog is None:
            try:
                from dopemux.commands.mcp_commands import _load_catalog

                catalog = _load_catalog()
            except Exception:  # noqa: BLE001
                return
        try:
            from dopemux.mcp.port_allocator import allocate_ports_map

            names = list((catalog.get("defaults") or {}).get("per_worktree") or [])
            if not names:
                return
            ports = allocate_ports_map(
                self.worktree,
                names,
                catalog,
                project_root=str(self.project_root),
                persist=self.persist_leases,
                dry_run=not self.persist_leases,
                source="InstanceOverlayManager",
            )
            self.env_ports = dict(ports)
            # Map into legacy port_map keys used by compose overlay writers
            if "CONPORT_HTTP_PORT" in ports:
                self.port_map["ConPort"] = ports["CONPORT_HTTP_PORT"]
            if "DOPE_MEMORY_PORT" in ports:
                self.port_map["Dope-Memory"] = ports["DOPE_MEMORY_PORT"]
            self._allocator_used = True
            logger.info(
                "InstanceOverlayManager using lease allocator ports for %s",
                self.worktree,
            )
        except RuntimeError:
            # Allocation BLOCKED (collision / occupied fixed port / etc.) —
            # do not fall back to the unsafe legacy map; surface the failure.
            raise
        except Exception as exc:  # noqa: BLE001 — unexpected errors fall back
            logger.warning(
                "InstanceOverlayManager lease allocator unavailable (%s); using legacy map",
                exc,
            )

    def materialize(self) -> Dict[str, Any]:
        """Generates the overlay files in .dopemux/instances/<id>/"""
        self.instance_dir.mkdir(parents=True, exist_ok=True)

        env_path = self.write_mcp_env()
        compose_path = self.write_compose_override()

        with open(self.instance_dir / "PORT_MAP.json", "w") as f:
            json.dump(
                {
                    "port_map": self.port_map,
                    "env_ports": self.env_ports,
                    "allocator_used": self._allocator_used,
                    "base_port": self.base_port,
                },
                f,
                indent=2,
            )

        return {
            "instance_dir": str(self.instance_dir),
            "env_path": str(env_path),
            "compose_path": str(compose_path),
            "port_map": self.port_map,
            "env_ports": self.env_ports,
            "allocator_used": self._allocator_used,
            "base_port": self.base_port,
            "compose_project_name": self.get_compose_project_name(),
        }

    def get_compose_project_name(self) -> str:
        project_id = self.project_root.name
        name = f"dopemux_{project_id}_{self.instance_id}".lower()
        return re.sub(r"[^a-z0-9_-]", "_", name)

    def write_mcp_env(self) -> Path:
        env_path = self.instance_dir / "mcp.env"

        def get_p(name: str) -> int:
            return int(self.port_map.get(name, 0))

        # Prefer lease env_ports when present
        conport_http = self.env_ports.get("CONPORT_HTTP_PORT", get_p("ConPort"))
        conport_mcp = self.env_ports.get("CONPORT_MCP_PORT", get_p("ConPort") + 1)
        conport_info = self.env_ports.get("CONPORT_INFO_PORT", get_p("ConPort") + 1000)
        dope_memory = self.env_ports.get("DOPE_MEMORY_PORT", get_p("Dope-Memory"))

        lines = [
            f"# Generated for instance: {self.instance_id}",
            f"# allocator_used={self._allocator_used}",
            f"COMPOSE_PROJECT_NAME={self.get_compose_project_name()}",
            "COMPOSE_FILE=compose.yml",
            f"DOPEMUX_INSTANCE_ID={self.instance_id}",
            f"CONPORT_CONTAINER_NAME={'mcp-conport' if not self.instance_id or self.instance_id == 'A' else f'mcp-conport_{self.instance_id}'}",
            f"SERENA_CONTAINER_NAME={'dopemux-mcp-serena' if not self.instance_id or self.instance_id == 'A' else f'dopemux-mcp-serena_{self.instance_id}'}",
            f"CONPORT_HTTP_PORT={conport_http}",
            f"CONPORT_MCP_PORT={conport_mcp}",
            f"CONPORT_INFO_PORT={conport_info}",
            f"SERENA_PORT={get_p('Serena')}",
            f"SERENA_HTTP_PORT={get_p('Serena') + 1000}",
            f"DOPE_CONTEXT_PORT={get_p('Dope-Context')}",
            f"DOPE_MEMORY_PORT={dope_memory}",
            f"PAL_PORT={self.base_port + 3}",
            f"EXA_PORT={self.base_port + 11}",
            f"DESKTOP_COMMANDER_PORT={self.base_port + 12}",
            f"LEANTIME_BRIDGE_PORT={self.base_port + 15}",
            f"GPT_RESEARCHER_PORT={self.base_port + 9}",
            f"DOPEMUX_CONPORT_PORT={conport_http}",
            f"DOPEMUX_SERENA_PORT={get_p('Serena')}",
            f"DOPEMUX_CONTEXT_PORT={get_p('Dope-Context')}",
            f"DOPEMUX_MEMORY_PORT={dope_memory}",
            f"DOPEMUX_LITELLM_PORT={get_p('LiteLLM')}",
        ]
        if "TASK_ORCHESTRATOR_HTTP_PORT" in self.env_ports:
            lines.append(
                f"TASK_ORCHESTRATOR_HTTP_PORT={self.env_ports['TASK_ORCHESTRATOR_HTTP_PORT']}"
            )

        with open(env_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        return env_path

    def write_compose_override(self) -> Path:
        compose_path = self.instance_dir / "mcp.compose.override.yml"

        services = []
        if "ConPort" in self.port_map or "CONPORT_HTTP_PORT" in self.env_ports:
            http = self.env_ports.get("CONPORT_HTTP_PORT", self.port_map.get("ConPort", 0))
            mcp = self.env_ports.get("CONPORT_MCP_PORT", http + 1)
            info = self.env_ports.get("CONPORT_INFO_PORT", http + 1000)
            services.append(
                "  conport:\n"
                f"    container_name: {'mcp-conport' if not self.instance_id or self.instance_id == 'A' else f'mcp-conport_{self.instance_id}'}\n"
                "    ports:\n"
                f'      - "{http}:3004"\n'
                f'      - "{mcp}:3005"\n'
                f'      - "{info}:4004"'
            )
        if "Serena" in self.port_map:
            services.append(
                "  serena:\n"
                f"    container_name: {'dopemux-mcp-serena' if not self.instance_id or self.instance_id == 'A' else f'dopemux-mcp-serena_{self.instance_id}'}\n"
                "    ports:\n"
                f'      - "{self.port_map["Serena"]}:3006"\n'
                f'      - "{self.port_map["Serena"] + 1000}:4006"'
            )
        if "Dope-Context" in self.port_map:
            services.append(
                f"  dope-context:\n    ports:\n      - \"{self.port_map['Dope-Context']}:3010\""
            )
        mem = self.env_ports.get("DOPE_MEMORY_PORT", self.port_map.get("Dope-Memory"))
        if mem:
            services.append(f'  dope-memory:\n    ports:\n      - "{mem}:3020"')
        if "LiteLLM" in self.port_map:
            services.append(
                f"  litellm:\n    ports:\n      - \"{self.port_map['LiteLLM']}:4000\""
            )

        content = "services:\n" + "\n".join(services)

        with open(compose_path, "w") as f:
            f.write(content)
        return compose_path
