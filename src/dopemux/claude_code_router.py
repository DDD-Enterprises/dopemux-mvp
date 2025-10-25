"""Claude Code Router orchestration for Dopemux multi-instance environments."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


class ClaudeCodeRouterError(RuntimeError):
    """Raised when the Claude Code Router cannot be prepared or launched."""


@dataclass
class ClaudeCodeRouterInfo:
    """Details about a Claude Code Router process."""

    host: str
    port: int
    config_path: Path
    home_path: Path
    log_path: Path
    api_key: str
    already_running: bool

    @property
    def base_url(self) -> str:
        """HTTP base URL for the router."""
        return f"http://{self.host}:{self.port}"


class ClaudeCodeRouterManager:
    """Manage a Claude Code Router instance per Dopemux workspace instance."""

    MAIN_PORT_BASE = 3000
    ROUTER_PORT_BASE = 3456

    def __init__(self, project_root: Path, instance_id: str, port_base: int) -> None:
        self.project_root = project_root.resolve()
        self.instance_id = instance_id
        self.port_base = port_base

        offset = max(self.port_base - self.MAIN_PORT_BASE, 0)
        self.host = "127.0.0.1"
        self.port = self.ROUTER_PORT_BASE + offset

        self.base_dir = self.project_root / ".dopemux" / "claude-code-router"
        self.instance_home = self.base_dir / instance_id
        self.router_home = self.instance_home / ".claude-code-router"

        self.config_path = self.router_home / "config.json"
        self.api_key_path = self.router_home / "api.key"
        self.pid_path = self.router_home / ".claude-code-router.pid"
        self.log_path = self.instance_home / "claude-code-router.log"

        self._api_key: Optional[str] = None
        self._process_env_overrides: Dict[str, str] = {}
        self._provider_key_env_var: Optional[str] = None

    def prepare_config(
        self,
        provider_url: str,
        provider_models: Sequence[str],
        *,
        provider_name: str = "litellm",
        provider_key: Optional[str] = None,
        provider_key_env_var: Optional[str] = None,
        router_overrides: Optional[Dict[str, str]] = None,
    ) -> Path:
        """Create or update the router configuration for this instance."""
        if not provider_models:
            raise ClaudeCodeRouterError("At least one upstream model must be provided")

        self._ensure_directories()
        api_key = self._ensure_api_key()

        config = self._load_config()

        config["PORT"] = self.port
        config["HOST"] = self.host
        config.setdefault("LOG", True)
        config.setdefault("LOG_LEVEL", "info")
        config["NON_INTERACTIVE_MODE"] = True
        config.setdefault("API_TIMEOUT_MS", 600_000)
        config["APIKEY"] = api_key

        provider_entry = self._build_provider_entry(
            config=config,
            provider_name=provider_name,
            provider_url=provider_url,
            provider_models=provider_models,
            provider_key=provider_key,
            provider_key_env_var=provider_key_env_var,
        )
        config["Providers"] = self._merge_providers(
            config.get("Providers", []), provider_entry, provider_name
        )

        router_config = config.get("Router", {})
        router_config.setdefault("longContextThreshold", 60_000)

        overrides = router_overrides or {}
        
        # Set up intelligent model routing based on Anthropic models
        # Primary: Use Claude models with proper fallbacks through LiteLLM
        router_config["default"] = overrides.get(
            "default", "litellm,anthropic-claude-3-5-sonnet-20241022"
        )
        router_config["background"] = overrides.get(
            "background", "litellm,anthropic-claude-3-haiku-20240307"
        )
        router_config["think"] = overrides.get(
            "think", "litellm,anthropic-claude-3-opus-20240229"
        )
        router_config.setdefault("longContext", router_config["default"])
        
        # Web search uses faster models
        if "webSearch" in overrides:
            router_config["webSearch"] = overrides["webSearch"]
        else:
            router_config["webSearch"] = "litellm,anthropic-claude-3-haiku-20240307"

        config["Router"] = router_config

        self._write_config(config)

        self._process_env_overrides = {
            "HOME": str(self.instance_home),
            "SERVICE_PORT": str(self.port),
            "CCR_INSTANCE_ID": self.instance_id,
        }
        self._provider_key_env_var = provider_key_env_var
        
        # Ensure provider keys are available to the router process
        if provider_key_env_var and provider_key is not None:
            self._process_env_overrides[provider_key_env_var] = provider_key
        elif provider_key and not provider_key_env_var:
            self._process_env_overrides.setdefault("CCR_UPSTREAM_API_KEY", provider_key)
        
        # Pass through all required API keys for LiteLLM fallbacks
        if os.environ.get("ANTHROPIC_API_KEY"):
            self._process_env_overrides["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
        if os.environ.get("XAI_API_KEY"):
            self._process_env_overrides["XAI_API_KEY"] = os.environ["XAI_API_KEY"]
        if os.environ.get("OPENAI_API_KEY"):
            self._process_env_overrides["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
        if os.environ.get("OPENROUTER_API_KEY"):
            self._process_env_overrides["OPENROUTER_API_KEY"] = os.environ["OPENROUTER_API_KEY"]

        self._api_key = api_key
        return self.config_path

    def ensure_started(
        self,
        provider_url: str,
        provider_models: Sequence[str],
        *,
        provider_name: str = "litellm",
        provider_key: Optional[str] = None,
        provider_key_env_var: Optional[str] = None,
        router_overrides: Optional[Dict[str, str]] = None,
        startup_timeout: float = 20.0,
    ) -> ClaudeCodeRouterInfo:
        """Ensure the router process is running with the desired configuration."""
        self.prepare_config(
            provider_url=provider_url,
            provider_models=provider_models,
            provider_name=provider_name,
            provider_key=provider_key,
            provider_key_env_var=provider_key_env_var,
            router_overrides=router_overrides,
        )

        already_running = self._is_running()
        if already_running:
            return self._build_info(already_running=True)

        executable = shutil.which("ccr")
        if not executable:
            raise ClaudeCodeRouterError(
                "ccr executable not found. Install with `npm install -g @musistudio/claude-code-router`."
            )

        env = self._build_process_env()
        self._launch_router_process(executable, env)

        if not self._wait_until_ready(startup_timeout):
            raise ClaudeCodeRouterError(
                f"Claude Code Router did not become ready on {self.host}:{self.port}"
            )

        return self._build_info(already_running=False)

    def build_client_env(self, info: ClaudeCodeRouterInfo) -> Dict[str, str]:
        """Environment variables for clients that should use the router."""
        return {
            "ANTHROPIC_BASE_URL": info.base_url,
            "ANTHROPIC_API_KEY": info.api_key,
            "CLAUDE_CODE_ROUTER_PORT": str(info.port),
            "CLAUDE_CODE_ROUTER_HOME": str(info.home_path),
            "CLAUDE_CODE_ROUTER_CONFIG": str(info.config_path),
            "CLAUDE_CODE_ROUTER_LOG": str(info.log_path),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_directories(self) -> None:
        self.instance_home.mkdir(parents=True, exist_ok=True)
        self.router_home.mkdir(parents=True, exist_ok=True)
        (self.router_home / "logs").mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, object]:
        if not self.config_path.exists():
            return {}
        try:
            return json.loads(self.config_path.read_text())
        except json.JSONDecodeError:
            backup_path = self.config_path.with_suffix(".corrupt")
            self.config_path.replace(backup_path)
            raise ClaudeCodeRouterError(
                f"Existing router config was invalid JSON. Moved to {backup_path}."
            )

    def _write_config(self, config: Dict[str, object]) -> None:
        content = json.dumps(config, indent=2, sort_keys=False)
        self.config_path.write_text(f"{content}\n")

    def _ensure_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        if self.api_key_path.exists():
            self._api_key = self.api_key_path.read_text().strip()
            return self._api_key
        api_key = secrets.token_urlsafe(32)
        self.api_key_path.write_text(api_key)
        self._api_key = api_key
        return api_key

    @staticmethod
    def _merge_providers(
        providers: Iterable[Dict[str, object]],
        new_provider: Dict[str, object],
        provider_name: str,
    ) -> List[Dict[str, object]]:
        merged: List[Dict[str, object]] = []
        for provider in providers:
            if str(provider.get("name", "")).lower() == provider_name.lower():
                continue
            merged.append(provider)
        merged.append(new_provider)
        return merged

    def _build_provider_entry(
        self,
        *,
        config: Dict[str, object],
        provider_name: str,
        provider_url: str,
        provider_models: Sequence[str],
        provider_key: Optional[str],
        provider_key_env_var: Optional[str],
    ) -> Dict[str, object]:
        entry: Dict[str, object] = {
            "name": provider_name,
            "api_base_url": provider_url,
            "models": list(provider_models),
        }
        if provider_key_env_var:
            entry["api_key"] = f"${provider_key_env_var}"
        elif provider_key is not None:
            entry["api_key"] = provider_key
        else:
            entry["api_key"] = ""

        existing = [p for p in config.get("Providers", []) if p.get("name") == provider_name]
        if existing:
            # Preserve transformer configuration if user already added one
            transformer = existing[-1].get("transformer")
            if transformer:
                entry["transformer"] = transformer

        return entry

    def _is_running(self) -> bool:
        pid = self._read_pid()
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            try:
                self.pid_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    def _read_pid(self) -> Optional[int]:
        if not self.pid_path.exists():
            return None
        try:
            return int(self.pid_path.read_text().strip())
        except ValueError:
            try:
                self.pid_path.unlink()
            except OSError:
                pass
            return None

    def _build_process_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env.update(self._process_env_overrides)
        if self._provider_key_env_var and self._provider_key_env_var not in env:
            raise ClaudeCodeRouterError(
                f"Upstream credential {self._provider_key_env_var} missing from environment"
            )
        return env

    def _launch_router_process(self, executable: str, env: Dict[str, str]) -> None:
        log_file = self.log_path.open("a")
        subprocess.Popen(  # noqa: S603, S607 - managed parameters
            [executable, "start"],
            cwd=str(self.project_root),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )

    def _wait_until_ready(self, timeout: float) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._is_running() and self._is_port_in_use():
                return True
            time.sleep(0.3)
        return False

    def _is_port_in_use(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((self.host, self.port))
                return True
            except OSError:
                return False

    def _build_info(self, *, already_running: bool) -> ClaudeCodeRouterInfo:
        if not self._api_key:
            raise ClaudeCodeRouterError("Router API key not initialized")
        return ClaudeCodeRouterInfo(
            host=self.host,
            port=self.port,
            config_path=self.config_path,
            home_path=self.instance_home,
            log_path=self.log_path,
            api_key=self._api_key,
            already_running=already_running,
        )


__all__ = [
    "ClaudeCodeRouterError",
    "ClaudeCodeRouterInfo",
    "ClaudeCodeRouterManager",
]
