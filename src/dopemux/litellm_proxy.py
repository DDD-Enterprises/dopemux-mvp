"""LiteLLM proxy management helpers for Dopemux."""

from __future__ import annotations

import os
import secrets
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml


class LiteLLMProxyError(RuntimeError):
    """Raised when the LiteLLM proxy cannot be prepared or launched."""


DEFAULT_LITELLM_CONFIG = """model_list:
  - model_name: openai-gpt-5
    litellm_params:
      model: openai/gpt-5
      api_key: os.environ/OPENAI_API_KEY
      api_base: https://api.openai.com
      temperature: 0.0
      max_tokens: 8192

  - model_name: openai-gpt-5-mini
    litellm_params:
      model: openai/gpt-5-mini
      api_key: os.environ/OPENAI_API_KEY
      api_base: https://api.openai.com
      temperature: 0.0
      max_tokens: 4096

  - model_name: xai-grok-4
    litellm_params:
      model: xai/grok-4
      api_key: os.environ/XAI_API_KEY
      api_base: https://api.x.ai/v1
      temperature: 0.0
      max_tokens: 4096

  - model_name: xai-grok-code-fast-1
    litellm_params:
      model: xai/grok-code-fast-1
      api_key: os.environ/XAI_API_KEY
      api_base: https://api.x.ai/v1
      temperature: 0.0
      max_tokens: 4096

litellm_settings:
  timeout: 60
  max_retries: 2
  fallbacks:
    - openai-gpt-5: ["openai-gpt-5-mini", "xai-grok-4", "xai-grok-code-fast-1"]
    - openai-gpt-5-mini: ["xai-grok-4", "xai-grok-code-fast-1"]
  default_fallbacks: ["xai-grok-4", "xai-grok-code-fast-1"]

router_settings:
  routing_strategy: "simple-shuffle"
  enable_pre_call_checks: true
  allowed_fails: 3
  cooldown_time: 30
  retry_policy:
    AuthenticationErrorRetries: 1
    TimeoutErrorRetries: 1
    RateLimitErrorRetries: 1
    InternalServerErrorRetries: 1
  content_policy_fallbacks:
    openai-gpt-5: ["xai-grok-4"]
    openai-gpt-5-mini: ["xai-grok-4"]

general_settings:
  master_key: "YOUR_MASTER_KEY"
  database_url: "sqlite:///litellm.db"
"""


@dataclass
class LiteLLMProxyInfo:
    """Holds details about a started LiteLLM proxy instance."""

    host: str
    port: int
    config_path: Path
    master_key: str
    log_path: Path
    already_running: bool

    @property
    def base_url(self) -> str:
        """Return the HTTP base URL for the proxy."""
        return f"http://{self.host}:{self.port}"


class LiteLLMProxyManager:
    """Prepare and launch LiteLLM proxy instances per Dopemux worktree."""

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT_BASE = 4100
    MAIN_PORT_BASE = 3000

    def __init__(self, project_root: Path, instance_id: str, port_base: int):
        self.project_root = project_root.resolve()
        self.instance_id = instance_id or "A"
        self.port_base = port_base
        host_override = os.environ.get("DOPEMUX_LITELLM_HOST", "")
        self.host = host_override or self.DEFAULT_HOST
        base_port_override = os.environ.get("DOPEMUX_LITELLM_PORT_BASE")
        base_port = self.DEFAULT_PORT_BASE
        if base_port_override and base_port_override.isdigit():
            base_port = int(base_port_override)
        offset = max(self.port_base - self.MAIN_PORT_BASE, 0)
        self.port = base_port + offset
        self.base_dir = self.project_root / ".dopemux" / "litellm"
        self.instance_dir = self.base_dir / self.instance_id

    def ensure_started(self) -> LiteLLMProxyInfo:
        """Ensure the LiteLLM proxy for this instance is running."""
        self.instance_dir.mkdir(parents=True, exist_ok=True)

        master_key = self._ensure_master_key()
        config_path = self._prepare_config(master_key)
        log_path = self.instance_dir / "litellm.log"

        proxy_info = LiteLLMProxyInfo(
            host=self.host,
            port=self.port,
            config_path=config_path,
            master_key=master_key,
            log_path=log_path,
            already_running=False,
        )

        if self._is_port_in_use():
            proxy_info.already_running = True
            return proxy_info

        proxy_env = os.environ.copy()
        proxy_env["LITELLM_MASTER_KEY"] = master_key

        try:
            process = self._launch_proxy_process(proxy_env, config_path, log_path)
        except FileNotFoundError as exc:  # pragma: no cover - depends on system setup
            raise LiteLLMProxyError(
                "litellm executable not found. Install LiteLLM (pip install litellm)"
            ) from exc
        except OSError as exc:  # pragma: no cover - defensive
            raise LiteLLMProxyError(f"Failed to launch LiteLLM proxy: {exc}") from exc

        if process.poll() is not None:
            raise LiteLLMProxyError("LiteLLM proxy terminated immediately after launch")

        if not self._wait_until_ready():
            process.terminate()
            raise LiteLLMProxyError(
                f"LiteLLM proxy did not become ready on {self.host}:{self.port}"
            )

        self._write_state(process.pid)

        return proxy_info

    def build_client_env(self, proxy_info: LiteLLMProxyInfo) -> Dict[str, str]:
        """Return environment variable updates for clients using the proxy."""
        updates: Dict[str, str] = {
            "OPENAI_API_BASE": proxy_info.base_url,
            "OPENAI_BASE_URL": proxy_info.base_url,
            "OPENAI_API_KEY": proxy_info.master_key,
            # Claude Code expects Anthropic-style env when routing via LiteLLM
            # Set both common variants to maximize compatibility
            "ANTHROPIC_API_BASE": proxy_info.base_url,
            "ANTHROPIC_BASE_URL": proxy_info.base_url,
            "ANTHROPIC_API_KEY": proxy_info.master_key,
            # Dopemux hint for launcher to keep API key (disable OAuth stripping)
            "DOPEMUX_CLAUDE_VIA_LITELLM": "1",
            "DOPEMUX_LITELLM_MASTER_KEY": proxy_info.master_key,
            "DOPEMUX_LITELLM_PORT": str(proxy_info.port),
            "DOPEMUX_LITELLM_HOST": proxy_info.host,
            "LITELLM_PROXY_URL": proxy_info.base_url,
        }

        current_openai_key = os.environ.get("OPENAI_API_KEY")
        if current_openai_key and current_openai_key != proxy_info.master_key:
            updates["DOPEMUX_PROVIDER_OPENAI_API_KEY"] = current_openai_key

        return updates

    def _resolve_config_template(self) -> Optional[Path]:
        override = os.environ.get("DOPEMUX_LITELLM_CONFIG")
        if override:
            candidate = Path(override).expanduser()
            if candidate.is_file():
                return candidate

        repo_candidate = self.project_root / "litellm.config.yaml"
        if repo_candidate.is_file():
            return repo_candidate

        return None

    def _ensure_master_key(self) -> str:
        key_path = self.instance_dir / "master.key"
        if key_path.exists():
            return key_path.read_text().strip()

        master_key = secrets.token_urlsafe(32)
        key_path.write_text(master_key)
        return master_key

    def _prepare_config(self, master_key: str) -> Path:
        template_path = self._resolve_config_template()
        if template_path and template_path.is_file():
            content = template_path.read_text()
        else:
            content = DEFAULT_LITELLM_CONFIG

        try:
            config_data = yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - defensive
            raise LiteLLMProxyError(f"Invalid LiteLLM configuration: {exc}") from exc

        general_settings = config_data.setdefault("general_settings", {})
        general_settings["master_key"] = master_key

        # Always use a per-instance SQLite DB unless explicitly overridden.
        # Using Postgres from the repo config would cause local CLI startup failures.
        override_db = os.environ.get("DOPEMUX_LITELLM_DB_URL", "").strip()
        if override_db:
            general_settings["database_url"] = override_db
        else:
            resolved_db = self.instance_dir / "litellm.db"
            general_settings["database_url"] = f"sqlite:///{resolved_db}"

        config_path = self.instance_dir / "litellm.config.yaml"
        config_path.write_text(
            yaml.safe_dump(config_data, sort_keys=False, default_flow_style=False)
        )

        return config_path

    def _is_port_in_use(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((self.host, self.port))
                return True
            except (ConnectionRefusedError, OSError):
                return False

    def _launch_proxy_process(
        self,
        env: Dict[str, str],
        config_path: Path,
        log_path: Path,
    ) -> subprocess.Popen:
        log_file = log_path.open("a")
        cmd = [
            "litellm",
            "--config",
            str(config_path),
            "--port",
            str(self.port),
            "--host",
            self.host,
        ]

        return subprocess.Popen(
            cmd,
            cwd=str(self.project_root),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    def _wait_until_ready(self, timeout: float = 10.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._is_port_in_use():
                return True
            time.sleep(0.3)
        return False

    def _write_state(self, pid: int) -> None:
        state_path = self.instance_dir / "litellm.state"
        state_path.write_text(str(pid))
