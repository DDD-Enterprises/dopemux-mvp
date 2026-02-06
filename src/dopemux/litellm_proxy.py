"""LiteLLM proxy management helpers for Dopemux."""

from __future__ import annotations
import logging


import hashlib
import os
import secrets
import shutil
import signal
import socket
import subprocess
import time
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import litellm  # type: ignore
import yaml


logger = logging.getLogger(__name__)

class LiteLLMProxyError(RuntimeError):
    """Raised when the LiteLLM proxy cannot be prepared or launched."""

MASTER_KEY_PREFIX = "sk-master-dopemux-local"


def _sanitize_random_token(length: int = 24) -> str:
    """
    Generate a URL-safe random token trimmed to the requested length.

    LiteLLM virtual keys are opaque but must stay URL-safe and reasonably short.
    """
    token = secrets.token_urlsafe(length)
    # token_urlsafe can exceed requested length; trim while keeping alphanumerics/-/_
    return token.replace("-", "").replace("_", "")[:length]


def generate_litellm_master_key() -> str:
    """
    Create a LiteLLM-compatible virtual master key.

    LiteLLM requires virtual keys to start with ``sk-``. Prefix with a Dopemux-specific
    marker so users can recognise local keys when debugging.
    """
    random_part = _sanitize_random_token()
    return f"{MASTER_KEY_PREFIX}-{random_part}"


def ensure_master_key(candidate: Optional[str]) -> Tuple[str, bool]:
    """
    Validate or generate a LiteLLM master key.

    Returns:
        A tuple of (master_key, regenerated) where ``regenerated`` is True if the
        provided candidate was invalid and a new key had to be generated.
    """
    value = (candidate or "").strip()
    if value.startswith("sk-"):
        return value, False

    return generate_litellm_master_key(), True


DEFAULT_LITELLM_CONFIG = """model_list:
  - model_name: grok-4-fast
    litellm_params:
      model: xai/grok-4-fast
      api_key: os.environ/XAI_API_KEY
      max_tokens: 131072

  - model_name: xai-grok-code-fast-1
    litellm_params:
      model: xai/grok-code-fast-1
      api_key: os.environ/XAI_API_KEY
      max_tokens: 131072

  - model_name: openrouter-gpt-5
    litellm_params:
      model: openrouter/openai/gpt-5
      api_key: os.environ/OPENROUTER_API_KEY
      api_base: https://openrouter.ai/api/v1
      max_tokens: 32768
      extra_headers:
        HTTP-Referer: https://dopemux.local
        X-Title: Dopemux LiteLLM Proxy

  - model_name: openrouter-gpt-5-codex
    litellm_params:
      model: openrouter/openai/gpt-5-codex
      api_key: os.environ/OPENROUTER_API_KEY
      api_base: https://openrouter.ai/api/v1
      max_tokens: 32768
      extra_headers:
        HTTP-Referer: https://dopemux.local
        X-Title: Dopemux LiteLLM Proxy

litellm_settings:
  timeout: 90
  max_retries: 2
  drop_params: true
  model_alias_map:
    grok-4: grok-4-fast
    grok: grok-4-fast
    grok-code: xai-grok-code-fast-1
    claude-sonnet: xai-grok-code-fast-1
    claude-sonnet-4-5-20250929: xai-grok-code-fast-1
    claude-sonnet-4.5: xai-grok-code-fast-1
    claude-haiku: xai-grok-code-fast-1
    claude-opus: openrouter-gpt-5-codex
    claude-opus-4-1-20250805: openrouter-gpt-5-codex
    claude-opus-4-20250514: openrouter-gpt-5-codex
    claude-4: openrouter-gpt-5-codex
    claude-4-sonnet: xai-grok-code-fast-1
    claude-4-opus: openrouter-gpt-5-codex
    claude-3.7: xai-grok-code-fast-1
    claude-3-7-sonnet-20250219: xai-grok-code-fast-1
    claude-3.5: xai-grok-code-fast-1
    claude-3-5-sonnet-20240620: xai-grok-code-fast-1
    anthropic/claude-3-5-sonnet-latest: xai-grok-code-fast-1
    xai/grok-code-fast-1: xai-grok-code-fast-1
    gpt-5: openrouter-gpt-5
    codex: openrouter-gpt-5-codex
  fallbacks:
    grok-4-fast:
      - openrouter-gpt-5
      - openrouter-gpt-5-codex
    xai-grok-code-fast-1:
      - grok-4-fast
      - openrouter-gpt-5-codex
    openrouter-gpt-5:
      - grok-4-fast
      - openrouter-gpt-5-codex
    openrouter-gpt-5-codex:
      - openrouter-gpt-5
      - grok-4-fast
  default_fallbacks:
    - grok-4-fast
    - openrouter-gpt-5
    - openrouter-gpt-5-codex

general_settings:
  master_key: YOUR_MASTER_KEY
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
    db_status: Optional[str] = None
    db_enabled: bool = False
    db_url: Optional[str] = None

    @property
    def base_url(self) -> str:
        """Return the HTTP base URL for the proxy."""
        return f"http://{self.host}:{self.port}"


def sync_litellm_database(instance_dir: Path, db_url: str) -> tuple[str, bool]:
    """
    Ensure the LiteLLM Prisma schema is applied for metrics/logging support.

    Args:
        instance_dir: Directory for the LiteLLM instance (used for sentinel/log files)
        db_url: Connection string to the LiteLLM Postgres database

    Returns:
        Status message for logging

    Raises:
        LiteLLMProxyError: If synchronization fails or prerequisites are missing
    """
    sentinel_path = instance_dir / "prisma.ready"
    hash_key = hashlib.sha256(db_url.encode("utf-8")).hexdigest()[:16]

    if sentinel_path.exists():
        try:
            if sentinel_path.read_text().strip() == hash_key:
                return "LiteLLM database schema already synchronized", True
        except OSError as exc:
            logger.debug("Failed reading LiteLLM Prisma sentinel %s: %s", sentinel_path, exc)

    prisma_cli = shutil.which("prisma")
    if prisma_cli is None:
        return (
            "⚠️  LiteLLM metrics disabled (Prisma CLI not installed - install with `pip install prisma`)",
            False,
        )

    schema_dir = Path(litellm.__file__).resolve().parent / "proxy"
    log_path = instance_dir / "prisma.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("DATABASE_URL", db_url)
    env.setdefault("PRISMA_QUERY_ENGINE_TYPE", "binary")

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"\n[{datetime.utcnow().isoformat()}Z] prisma db push\n")
        log_file.flush()
        try:
            subprocess.run(
                [prisma_cli, "db", "push", "--accept-data-loss"],
                cwd=str(schema_dir),
                env=env,
                check=True,
                stdout=log_file,
                stderr=log_file,
                timeout=180,
            )
        except subprocess.TimeoutExpired as exc:
            raise LiteLLMProxyError(
                f"Timed out syncing LiteLLM database; see {log_path} for details."
            ) from exc
        except subprocess.CalledProcessError as exc:
            error_text = ""
            try:
                error_text = log_path.read_text(encoding="utf-8")[-2000:]
            except Exception as e:
                logger.debug("Failed reading Prisma log tail %s: %s", log_path, e)
            lowered = error_text.lower()
            if ("can't reach database server" in lowered) or ("p1001" in lowered):
                return (
                    "⚠️  LiteLLM database unreachable - continuing without metrics",
                    False,
                )
            raise LiteLLMProxyError(
                f"Failed to sync LiteLLM database; see {log_path} for details."
            ) from exc

    sentinel_path.write_text(hash_key, encoding="utf-8")
    return "LiteLLM database schema synchronized", True


class LiteLLMProxyManager:
    """Prepare and launch LiteLLM proxy instances per Dopemux worktree."""

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT_BASE = 4000
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

        db_url = self._resolve_db_url()
        effective_db_url = None
        if db_url:
            status, enabled = self._sync_database(db_url)
            proxy_info.db_status = status
            proxy_info.db_enabled = enabled
            if enabled:
                proxy_info.db_url = db_url
                effective_db_url = db_url
        else:
            proxy_info.db_status = "LiteLLM metrics disabled"

        if self._is_port_in_use():
            if self._check_proxy_health():
                proxy_info.already_running = True
                return proxy_info
            # Port in use but unhealthy - wait for it to clear or terminate it
            time.sleep(2)
            if not self._is_port_in_use():
                # Port cleared, continue to start new instance
                pass
            elif self._check_proxy_health():
                # Now healthy after brief wait
                proxy_info.already_running = True
                return proxy_info
            else:
                # Still unhealthy - try to cleanup
                self._cleanup_stale_instance()
                if self._is_port_in_use():
                    raise LiteLLMProxyError(
                        f"Port {self.port} is occupied by an unhealthy process"
                    )

        attempts = 0
        max_attempts = 2
        while True:
            proxy_env = os.environ.copy()
            proxy_env["LITELLM_MASTER_KEY"] = master_key
            if effective_db_url:
                proxy_env.setdefault("DATABASE_URL", effective_db_url)
                proxy_env.pop("LITELLM_DISABLE_DB", None)
                proxy_env.pop("LITELLM_DISABLE_SPEND_LOGGING", None)
            else:
                # Avoid Prisma requirement locally when no DB configured
                proxy_env.setdefault("LITELLM_DISABLE_DB", "true")
                proxy_env.setdefault("LITELLM_DISABLE_SPEND_LOGGING", "true")

            try:
                process = self._launch_proxy_process(proxy_env, config_path, log_path)
            except FileNotFoundError as exc:  # pragma: no cover - depends on system setup
                raise LiteLLMProxyError(
                    "litellm executable not found. Install LiteLLM (pip install litellm)"
                ) from exc
            except OSError as exc:  # pragma: no cover - defensive
                raise LiteLLMProxyError(f"Failed to launch LiteLLM proxy: {exc}") from exc

            if process.poll() is not None:
                log_excerpt = self._read_tail(log_path)
                reason = self._should_disable_db_due_to_launch(log_excerpt)
                if effective_db_url and reason:
                    attempts += 1
                    proxy_info.db_enabled = False
                    proxy_info.db_url = None
                    proxy_info.db_status = reason
                    effective_db_url = None
                    for var in ("DOPEMUX_LITELLM_DB_URL", "LITELLM_DATABASE_URL", "DATABASE_URL"):
                        os.environ.pop(var, None)
                    if attempts < max_attempts:
                        continue
                raise LiteLLMProxyError("LiteLLM proxy terminated immediately after launch")

            if not self._wait_until_ready():
                process.terminate()
                log_excerpt = self._read_tail(log_path)
                reason = self._should_disable_db_due_to_launch(log_excerpt)
                if effective_db_url and reason and attempts < max_attempts:
                    attempts += 1
                    proxy_info.db_enabled = False
                    proxy_info.db_url = None
                    proxy_info.db_status = reason
                    effective_db_url = None
                    for var in ("DOPEMUX_LITELLM_DB_URL", "LITELLM_DATABASE_URL", "DATABASE_URL"):
                        os.environ.pop(var, None)
                    continue
                raise LiteLLMProxyError(
                    f"LiteLLM proxy did not become ready on {self.host}:{self.port}"
                )
            break

        self._write_state(process.pid)

        return proxy_info

    def build_client_env(self, proxy_info: LiteLLMProxyInfo) -> Dict[str, str]:
        """Return environment variable updates for clients using the proxy."""
        updates: Dict[str, str] = {
            # Set OpenAI-compatible environment for Claude Code
            "OPENAI_API_BASE": proxy_info.base_url,
            "OPENAI_BASE_URL": proxy_info.base_url,
            "OPENAI_API_KEY": proxy_info.master_key,
            # Also set Anthropic-compatible environment
            "ANTHROPIC_API_BASE": proxy_info.base_url,
            "ANTHROPIC_BASE_URL": proxy_info.base_url,
            "ANTHROPIC_API_KEY": proxy_info.master_key,
            # Dopemux hints
            "DOPEMUX_CLAUDE_VIA_LITELLM": "1",
            "DOPEMUX_LITELLM_MASTER_KEY": proxy_info.master_key,
            "DOPEMUX_LITELLM_PORT": str(proxy_info.port),
            "DOPEMUX_LITELLM_HOST": proxy_info.host,
            "LITELLM_PROXY_URL": proxy_info.base_url,
            "LITELLM_MASTER_KEY": proxy_info.master_key,
        }

        if proxy_info.db_enabled and proxy_info.db_url:
            updates["DOPEMUX_LITELLM_DB_URL"] = proxy_info.db_url
            updates.setdefault("LITELLM_DATABASE_URL", proxy_info.db_url)
            updates.setdefault("DATABASE_URL", proxy_info.db_url)

        # Preserve original provider keys separately so LiteLLM can access them if needed
        provider_key_envs = {
            "ANTHROPIC_API_KEY": "DOPEMUX_PROVIDER_ANTHROPIC_API_KEY",
            "XAI_API_KEY": "DOPEMUX_PROVIDER_XAI_API_KEY",
            "OPENAI_API_KEY": "DOPEMUX_PROVIDER_OPENAI_API_KEY",
        }
        for env_name, dopemux_key in provider_key_envs.items():
            value = os.environ.get(env_name)
            if value:
                updates[dopemux_key] = value

        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        if openrouter_key:
            updates["OPENROUTER_API_KEY"] = openrouter_key
            updates["DOPEMUX_PROVIDER_OPENROUTER_API_KEY"] = openrouter_key

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

        # Use the default config from the dopemux installation
        default_config = Path(__file__).parent.parent.parent / "litellm.config.yaml"
        if default_config.exists():
            return default_config

        return None

    def _ensure_master_key(self) -> str:
        key_path = self.instance_dir / "master.key"
        if key_path.exists():
            existing = key_path.read_text().strip()
            master_key, regenerated = ensure_master_key(existing)
            if regenerated:
                key_path.write_text(master_key)
            return master_key

        master_key, _ = ensure_master_key(None)
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

        # IMPORTANT: Do not set a database_url for local CLI proxy.
        # Presence of this field triggers Prisma initialization which fails
        # on local installs without generated binaries. We disable DB usage
        # via env + removing the config key entirely. Advanced users can set
        # DOPEMUX_LITELLM_DB_URL to opt back in.
        override_db = os.environ.get("DOPEMUX_LITELLM_DB_URL", "").strip()
        if override_db:
            general_settings["database_url"] = override_db
        else:
            # Remove any existing DB configuration to avoid Prisma entirely
            if "database_url" in general_settings:
                general_settings.pop("database_url", None)

        config_path = self.instance_dir / "litellm.config.yaml"
        config_path.write_text(
            yaml.safe_dump(config_data, sort_keys=False, default_flow_style=False)
        )

        return config_path

    def _resolve_db_url(self) -> Optional[str]:
        for key in ("DOPEMUX_LITELLM_DB_URL", "LITELLM_DATABASE_URL", "DATABASE_URL"):
            value = os.environ.get(key, "").strip()
            if value:
                return value
        return None

    def _sync_database(self, db_url: str) -> str:
        return sync_litellm_database(self.instance_dir, db_url)

    def _is_port_in_use(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((self.host, self.port))
                return True
            except (ConnectionRefusedError, OSError):
                return False

    def _check_proxy_health(self) -> bool:
        """Check if the proxy at the configured port is healthy and responding."""
        try:
            import urllib.request
            import urllib.error
            url = f"http://{self.host}:{self.port}/health"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2.0) as response:
                return response.status == 200
        except Exception as e:
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

    def _wait_until_ready(self, timeout: float = 30.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._is_port_in_use():
                return True
            time.sleep(0.3)
        return False

    def _write_state(self, pid: int) -> None:
        state_path = self.instance_dir / "litellm.state"
        state_path.write_text(str(pid))

    def _cleanup_stale_instance(self) -> None:
        """Try to cleanup a stale litellm instance on this port."""
        state_path = self.instance_dir / "litellm.state"
        if not state_path.exists():
            return
        
        try:
            pid = int(state_path.read_text().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                # Check if process is still alive
                os.kill(pid, 0)
                # Still alive, force kill
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            except ProcessLookupError:
                # Process already dead
                logger.debug("LiteLLM stale process %s already terminated", pid)
        except (ValueError, OSError) as exc:
            logger.debug("Failed cleaning stale LiteLLM process state: %s", exc)
        
        # Remove stale state file
        state_path.unlink(missing_ok=True)

    @staticmethod
    def _read_tail(path: Path, length: int = 2000) -> str:
        try:
            text = path.read_text(encoding="utf-8")
            return text[-length:]
        except Exception:
            return ""
    @staticmethod
    def _should_disable_db_due_to_launch(log_excerpt: str) -> Optional[str]:
        lowered = log_excerpt.lower()
        if "unable to find prisma binaries" in lowered or (
            "prisma generate" in lowered and "unable" in lowered
        ):
            return "⚠️  LiteLLM metrics disabled (Prisma client unavailable)"
        if (
            "all connection attempts failed" in lowered
            or "connection refused" in lowered
            or "p1001" in lowered
            or "can't reach database server" in lowered
        ):
            return "⚠️  LiteLLM metrics disabled (database unreachable)"
        return None
