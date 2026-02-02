"""Collectors for implementation-mode data sources."""

from __future__ import annotations

import asyncio
import json
import shutil
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .base_collector import BaseCollector
from ..config.settings import ServiceEndpoints


class ImplementationCollector(BaseCollector):
    """Aggregates operational data for the implementation dashboard."""

    def __init__(self, services: ServiceEndpoints):
        super().__init__(cache_ttl=5.0, timeout=2.5)
        self.services = services

    async def fetch(self) -> Dict[str, Any]:
        results = await asyncio.gather(
            self.fetch_adhd_engine(),
            self.fetch_serena_untracked(),
            self.fetch_activity_capture(),
            self.fetch_git_status(),
            self.fetch_docker_status(),
            self.fetch_mcp_health(),
            self.fetch_litellm_costs(),
            return_exceptions=True,
        )

        return {
            "adhd": self._safe_result(results[0]),
            "serena": self._safe_result(results[1]),
            "activity": self._safe_result(results[2]),
            "git": self._safe_result(results[3]),
            "docker": self._safe_result(results[4]),
            "mcp": self._safe_result(results[5]),
            "litellm": self._safe_result(results[6]),
        }

    @staticmethod
    def _safe_result(value: Any, fallback: Optional[Any] = None) -> Any:
        if isinstance(value, Exception):
            return fallback
        return value if value is not None else fallback

    async def fetch_adhd_engine(self) -> Dict[str, Any]:
        url = f"{self.services.adhd_engine_url.rstrip('/')}/status"
        payload = await self._http_json(url)
        if not payload:
            return {
                "energy": "N/A",
                "session_minutes": 0,
                "health": None,
                "focus": None,
            }
        return {
            "energy": payload.get("energy", "N/A"),
            "session_minutes": payload.get("session_minutes", 0),
            "health": payload.get("health_score"),
            "focus": payload.get("focus"),
        }

    async def fetch_serena_untracked(self) -> Dict[str, Any]:
        url = f"{self.services.serena_url.rstrip('/')}/detect-untracked"
        payload = await self._http_json(url)
        if not payload:
            return await self._detect_untracked_via_git()
        return {
            "file_count": payload.get("file_count", 0),
            "age_days": payload.get("age_days", 0),
            "confidence": payload.get("confidence", 0.0),
            "files": payload.get("files_list", []),
        }

    async def _detect_untracked_via_git(self) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        lines = [l for l in stdout.decode("utf-8", "ignore").splitlines() if l.strip()]
        untracked = [l[3:] for l in lines if l.startswith("?? ")]
        file_count = len(untracked)
        # Compute age_days as days since most recently modified untracked file
        now = time.time()
        ages = []
        for rel in untracked:
            try:
                mtime = os.path.getmtime(rel)
                ages.append((now - mtime) / 86400.0)
            except OSError:
                continue
        age_days = int(max(ages) if ages else 0)
        return {"file_count": file_count, "age_days": age_days, "confidence": 0.0, "files": untracked[:20]}

    async def fetch_activity_capture(self) -> Dict[str, Any]:
        url = f"{self.services.activity_capture_url.rstrip('/')}/recent"
        payload = await self._http_json(url)
        if not payload:
            return {"switches_15m": 0, "current_context": None}
        return {
            "switches_15m": payload.get("switches_15m", 0),
            "current_context": payload.get("current_context"),
        }

    async def fetch_git_status(self) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "status",
            "--porcelain",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", "ignore").strip()
        if not output:
            return {"uncommitted": 0}
        lines = [line for line in output.splitlines() if line.strip()]
        return {"uncommitted": len(lines), "paths": lines[:10]}

    async def fetch_docker_status(self) -> Dict[str, Any]:
        compose_bin = self.services.docker_compose_bin or "docker-compose"
        if not shutil.which(compose_bin):
            return {"available": False, "healthy": 0, "total": 0}
        proc = await asyncio.create_subprocess_exec(
            compose_bin,
            "ps",
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        text = stdout.decode("utf-8", "ignore").strip()
        if not text:
            return {"available": True, "healthy": 0, "total": 0}
        healthy = 0
        total = 0
        containers = []
        for line in text.splitlines():
            total += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            state = (entry.get("State") or "").lower()
            name = entry.get("Name") or entry.get("Service") or "unknown"
            image = entry.get("Image") or ""
            if state.startswith("up"):
                healthy += 1
            containers.append({"name": name, "state": state, "image": image})
        # Discover compose-defined services (aggregate all compose files)
        compose_services: Dict[str, Dict[str, Any]] = {}
        try:
            root = Path.cwd()
            for compose_file in root.glob("docker-compose*.yml"):
                try:
                    text_comp = compose_file.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                in_services = False
                for raw_line in text_comp.splitlines():
                    line = raw_line.rstrip()
                    if line.strip().startswith("services:"):
                        in_services = True
                        continue
                    if in_services:
                        # End of services section when a top-level key appears
                        if line and not line.startswith(" "):
                            in_services = False
                            continue
                        if not line.strip():
                            continue
                        # Match service lines like '  service-name:'
                        if ":" in line:
                            left = line.split(":", 1)[0]
                            name_candidate = left.strip()
                            # heuristic: skip keys that are not top-level service entries (e.g. image, build, depends_on)
                            if " " not in left and name_candidate and name_candidate.isascii() and name_candidate not in {"image","build","depends_on","volumes","networks","environment","restart","ports","healthcheck"}:
                                compose_services.setdefault(name_candidate, {})
        except Exception:
            pass
        # Map container states to compose services
        container_state_map = {c["name"]: c["state"] for c in containers}
        for svc in compose_services.keys():
            # try direct name and common prefix patterns
            state = None
            # direct match
            state = container_state_map.get(svc)
            if state is None:
                # look for container containing svc
                for cname, cstate in container_state_map.items():
                    if svc in cname:
                        state = cstate
                        break
            compose_services[svc]["state"] = state or "missing"
        return {"available": True, "healthy": healthy, "total": total, "containers": containers, "compose": compose_services}

    async def fetch_mcp_health(self) -> Dict[str, Any]:
        servers = {
            "zen": "http://localhost:3003",
            "conport": "http://localhost:3004",
            "serena": self.services.activity_capture_url.rstrip("/"),
            "context7": "http://localhost:3002",
            "gptr-mcp": "http://localhost:3009",
        }
        services: Dict[str, Dict[str, Any]] = {}
        for name, base in servers.items():
            url = base.rstrip("/") + "/health"
            start = time.time()
            payload = await self._http_json(url)
            latency = int((time.time() - start) * 1000)
            services[name] = {
                "healthy": bool(payload),
                "latency_ms": latency,
            }
        healthy_count = sum(1 for v in services.values() if v["healthy"])
        return {"summary": healthy_count, "services": services}

    async def fetch_litellm_costs(self) -> Dict[str, Any]:
        url = f"{self.services.litellm_url.rstrip('/')}/metrics"
        payload = await self._http_json(url)
        if not payload:
            return {"hourly_cost": None, "latency_ms": None}
        return {
            "hourly_cost": payload.get("cost_per_hour"),
            "latency_ms": payload.get("average_latency_ms"),
        }

