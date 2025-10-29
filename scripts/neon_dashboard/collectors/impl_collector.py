"""Collectors for implementation-mode data sources."""

from __future__ import annotations

import asyncio
import json
import shutil
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
            return {"file_count": 0, "age_days": 0, "confidence": 0.0, "files": []}
        return {
            "file_count": payload.get("file_count", 0),
            "age_days": payload.get("age_days", 0),
            "confidence": payload.get("confidence", 0.0),
            "files": payload.get("files_list", []),
        }

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
        for line in text.splitlines():
            total += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (entry.get("State") or "").lower().startswith("up"):
                healthy += 1
        return {"available": True, "healthy": healthy, "total": total}

    async def fetch_mcp_health(self) -> Dict[str, Any]:
        # Placeholder: eventually poll MCP supervisor
        return {"healthy": None}

    async def fetch_litellm_costs(self) -> Dict[str, Any]:
        url = f"{self.services.litellm_url.rstrip('/')}/metrics"
        payload = await self._http_json(url)
        if not payload:
            return {"hourly_cost": None, "latency_ms": None}
        return {
            "hourly_cost": payload.get("cost_per_hour"),
            "latency_ms": payload.get("average_latency_ms"),
        }

