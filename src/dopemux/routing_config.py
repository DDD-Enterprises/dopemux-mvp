"""Global routing configuration management for Dopemux."""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
import shutil
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)

LOCAL_PROVIDER_NAMES = {"ollama", "lmstudio"}
LOCAL_PROVIDER_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}


class RoutingConfigError(RuntimeError):
    """Raised when routing configuration is invalid or cannot be loaded."""


def _provider_hostname(provider: Dict[str, Any]) -> Optional[str]:
    base_url = str(provider.get("base_url") or "").strip()
    if not base_url:
        return None
    parsed = urlparse(base_url)
    hostname = parsed.hostname
    if hostname is None and "://" not in base_url:
        hostname = urlparse(f"http://{base_url}").hostname
    return hostname.lower() if hostname else None


def _provider_allows_inline_auth(provider: Dict[str, Any]) -> bool:
    name = str(provider.get("name") or "").strip().lower()
    if name in LOCAL_PROVIDER_NAMES:
        return True
    hostname = _provider_hostname(provider)
    return bool(hostname and hostname in LOCAL_PROVIDER_HOSTNAMES)


class RoutingConfig:
    """Manage the global routing configuration for Dopemux."""

    DEFAULT_CONFIG_PATH = Path.home() / ".dopemux" / "routing.yaml"
    TEMPLATE_PATH = (
        Path(__file__).parent.parent.parent / "templates" / "routing.yaml"
    )

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize routing config manager.

        Args:
            config_path: Path to routing.yaml. Defaults to ~/.dopemux/routing.yaml
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> Dict[str, Any]:
        """Load and validate the routing configuration.

        Returns:
            The parsed configuration dictionary

        Raises:
            RoutingConfigError: If config cannot be loaded or is invalid
        """
        if not self.config_path.exists():
            if self.TEMPLATE_PATH.exists():
                # Initialize from template
                self._copy_template()
            else:
                raise RoutingConfigError(
                    f"Routing config not found at {self.config_path} "
                    "and no template available"
                )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
            self._loaded = True
            self.validate()
            return self.config
        except yaml.YAMLError as e:
            raise RoutingConfigError(f"Invalid YAML in routing config: {e}") from e
        except Exception as e:
            raise RoutingConfigError(f"Failed to load routing config: {e}") from e

    def _copy_template(self) -> None:
        """Copy template to default location if it doesn't exist."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.TEMPLATE_PATH, "r", encoding="utf-8") as src:
                content = src.read()
            with open(self.config_path, "w", encoding="utf-8") as dst:
                dst.write(content)
            logger.info(
                f"Initialized routing config from template at {self.config_path}"
            )
        except Exception as e:
            raise RoutingConfigError(f"Failed to copy template: {e}") from e

    def load_template(self) -> Dict[str, Any]:
        """Load the repo-owned routing template."""
        if not self.TEMPLATE_PATH.exists():
            raise RoutingConfigError(
                f"Routing template not found at {self.TEMPLATE_PATH}"
            )

        try:
            with open(self.TEMPLATE_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise RoutingConfigError(f"Invalid YAML in routing template: {e}") from e
        except Exception as e:
            raise RoutingConfigError(f"Failed to load routing template: {e}") from e

    def audit_alias_contract(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compare current alias mappings against the repo-owned template."""
        current = config if config is not None else self.load()
        template = self.load_template()

        template_aliases = template.get("aliases", {})
        current_aliases = current.get("aliases", {})

        if not isinstance(template_aliases, dict):
            raise RoutingConfigError("Template aliases must be a dictionary")
        if not isinstance(current_aliases, dict):
            raise RoutingConfigError("Config aliases must be a dictionary")

        missing = {
            alias: target
            for alias, target in template_aliases.items()
            if alias not in current_aliases
        }
        mismatched = {
            alias: {"expected": target, "actual": current_aliases[alias]}
            for alias, target in template_aliases.items()
            if alias in current_aliases and current_aliases[alias] != target
        }

        return {
            "config_path": str(self.config_path),
            "template_path": str(self.TEMPLATE_PATH),
            "template_aliases": template_aliases,
            "missing_aliases": missing,
            "mismatched_aliases": mismatched,
            "stale": bool(missing or mismatched),
        }

    def repair_alias_contract(self) -> Dict[str, Any]:
        """Repair repo-owned alias drift without overwriting unrelated config."""
        current = self.load()
        audit = self.audit_alias_contract(current)
        if not audit["stale"]:
            return {
                "changed": False,
                "backup_path": None,
                "audit": audit,
            }

        merged_aliases = dict(current.get("aliases", {}))
        merged_aliases.update(audit["template_aliases"])

        backup_path = self.config_path.with_name(
            f"{self.config_path.name}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        shutil.copy2(self.config_path, backup_path)

        self._write_alias_block(merged_aliases)
        self._loaded = False
        repaired = self.load()

        return {
            "changed": True,
            "backup_path": str(backup_path),
            "audit": self.audit_alias_contract(repaired),
        }

    def _write_alias_block(self, aliases: Dict[str, str]) -> None:
        """Rewrite only the top-level aliases block in routing.yaml."""
        text = self.config_path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)

        start = None
        end = len(lines)
        for index, line in enumerate(lines):
            if line.strip() == "aliases:" and line[: len(line) - len(line.lstrip())] == "":
                start = index
                break

        if start is None:
            raise RoutingConfigError("routing.yaml missing top-level aliases section")

        for index in range(start + 1, len(lines)):
            stripped = lines[index].strip()
            if not stripped:
                continue
            if lines[index][: len(lines[index]) - len(lines[index].lstrip())] == "":
                end = index
                break

        alias_lines = ["aliases:\n"]
        for alias, target in aliases.items():
            alias_lines.append(f"  {alias}: {target}\n")

        updated = "".join(lines[:start] + alias_lines + lines[end:])
        self.config_path.write_text(updated, encoding="utf-8")

    def validate(self) -> None:
        """Validate the loaded configuration.

        Checks:
        - Required top-level keys exist
        - Mode is valid
        - All model references are valid
        - All provider references are valid
        - Fallback chains are valid

        Raises:
            RoutingConfigError: If validation fails
        """
        if not self._loaded:
            raise RoutingConfigError("Config not loaded - call load() first")

        # Check version
        if self.config.get("version") != 1:
            raise RoutingConfigError(
                f"Unsupported config version: {self.config.get('version')}"
            )

        required_sections = [
            "mode", "ports", "providers", "models", "slots", "fallbacks",
            "default_fallbacks", "aliases"
        ]
        for section in required_sections:
            if section not in self.config:
                raise RoutingConfigError(f"Missing required section: {section}")

        # Validate mode
        valid_modes = ["subscription", "api"]
        if self.config["mode"] not in valid_modes:
            raise RoutingConfigError(
                f"Invalid mode: {self.config['mode']}. Must be one of: {valid_modes}"
            )

        # Validate ports
        ports = self.config.get("ports", {})
        if "litellm" not in ports or "ccr" not in ports:
            raise RoutingConfigError("Ports section must contain 'litellm' and 'ccr'")

        # Validate providers
        providers = self.config.get("providers", [])
        if not isinstance(providers, list) or len(providers) == 0:
            raise RoutingConfigError("Providers must be a non-empty list")

        provider_names = {}
        for provider in providers:
            if "name" not in provider:
                raise RoutingConfigError("Provider missing 'name' field")
            auth_mode = str(provider.get("auth_mode") or "env").lower()
            if auth_mode not in {"env", "none", "ignored"}:
                raise RoutingConfigError(
                    f"Provider {provider['name']} has unsupported auth_mode: {auth_mode}"
                )
            if auth_mode in {"none", "ignored"} and not _provider_allows_inline_auth(
                provider
            ):
                raise RoutingConfigError(
                    f"Provider {provider['name']} has auth_mode {auth_mode} but is not a local provider"
                )
            if auth_mode == "env" and "api_key_env" not in provider:
                raise RoutingConfigError(
                    f"Provider {provider['name']} missing 'api_key_env' field"
                )
            provider_names[provider["name"]] = provider

        # Validate models
        models = self.config.get("models", [])
        if not isinstance(models, list) or len(models) == 0:
            raise RoutingConfigError("Models must be a non-empty list")

        model_names = {}
        for model in models:
            if "name" not in model:
                raise RoutingConfigError("Model missing 'name' field")
            if "provider" not in model:
                raise RoutingConfigError(
                    f"Model {model['name']} missing 'provider' field"
                )
            if "model_id" not in model and "litellm_model" not in model:
                raise RoutingConfigError(
                    f"Model {model['name']} missing 'model_id' field"
                )

            # Check provider exists
            if model["provider"] not in provider_names:
                raise RoutingConfigError(
                    f"Model {model['name']} references unknown provider: "
                    f"{model['provider']}"
                )

            model_names[model["name"]] = model

        # Validate slots
        slots = self.config.get("slots", {})
        if not isinstance(slots, dict) or len(slots) == 0:
            raise RoutingConfigError("Slots must be a non-empty dictionary")

        for slot_name, model_name in slots.items():
            if model_name not in model_names:
                raise RoutingConfigError(
                    f"Slot {slot_name} references unknown model: {model_name}"
                )

        # Validate fallbacks
        fallbacks = self.config.get("fallbacks", {})
        if not isinstance(fallbacks, dict):
            raise RoutingConfigError("Fallbacks must be a dictionary")

        for model_name, fallback_list in fallbacks.items():
            if model_name not in model_names:
                raise RoutingConfigError(
                    f"Fallbacks contain unknown model: {model_name}"
                )
            if not isinstance(fallback_list, list):
                raise RoutingConfigError(
                    f"Fallbacks for {model_name} must be a list"
                )
            for fb_model in fallback_list:
                if fb_model not in model_names:
                    raise RoutingConfigError(
                        f"Fallbacks for {model_name} references unknown model: "
                        f"{fb_model}"
                    )

        # Validate default_fallbacks
        default_fb = self.config.get("default_fallbacks", [])
        if not isinstance(default_fb, list):
            raise RoutingConfigError("default_fallbacks must be a list")
        for model_name in default_fb:
            if model_name not in model_names:
                raise RoutingConfigError(
                    f"default_fallbacks contains unknown model: {model_name}"
                )

        # Validate aliases
        aliases = self.config.get("aliases", {})
        if not isinstance(aliases, dict):
            raise RoutingConfigError("Aliases must be a dictionary")

        for alias, target in aliases.items():
            if target not in slots:
                msg = f"Alias {alias} references unknown slot: {target}"
                raise RoutingConfigError(msg)

        try:
            from dopemux.freeflow import validate_freeflow_config

            validate_freeflow_config(self.config)
        except ValueError as exc:
            raise RoutingConfigError(str(exc)) from exc

    def generate_litellm_config(self, master_key: str) -> Dict[str, Any]:
        """Generate LiteLLM configuration from routing config.

        Args:
            master_key: The master key to use for LiteLLM

        Returns:
            Dictionary containing LiteLLM configuration

        Note:
            This does NOT include API keys - those must be set via environment variables
            referenced in the config.
        """
        if not self._loaded:
            raise RoutingConfigError("Config not loaded - call load() first")

        from dopemux.freeflow import (
            generate_freeflow_litellm_config,
            strict_free_enabled,
        )

        if strict_free_enabled(self.config):
            return generate_freeflow_litellm_config(self.config, master_key)

        models = self.config.get("models", [])
        slots = self.config.get("slots", {})
        fallbacks = self.config.get("fallbacks", {})
        default_fb = self.config.get("default_fallbacks", [])
        aliases = self.config.get("aliases", {})

        # Build model_list
        model_list = []
        for model in models:
            provider = self._get_provider_by_name(model["provider"])
            auth_mode = str(provider.get("auth_mode") or "env").lower()

            litellm_params = {
                "model": model.get("model_id") or model.get("litellm_model"),
                "max_tokens": model.get("max_tokens", 131072),
            }
            if auth_mode in {"none", "ignored"}:
                if not _provider_allows_inline_auth(provider):
                    raise RoutingConfigError(
                        f"Provider {provider['name']} has auth_mode {auth_mode} but is not a local provider"
                    )
                # Inline placeholder keys are reserved for local providers only.
                litellm_params["api_key"] = str(provider.get("api_key") or "local")
            else:
                # Hosted providers stay env-driven so credentials are never embedded.
                litellm_params["api_key"] = f"os.environ/{provider['api_key_env']}"

            # Add provider-specific settings
            if "base_url" in provider:
                litellm_params["api_base"] = provider["base_url"]

            if "extra_headers" in provider:
                litellm_params["extra_headers"] = provider["extra_headers"]

            model_list.append({
                "model_name": model["name"],
                "litellm_params": litellm_params,
            })

        # Build model_alias_map from slots and aliases
        model_alias_map = {}

        # First, map all aliases to their slot targets
        for alias, slot_name in aliases.items():
            model_name = slots[slot_name]
            model_alias_map[alias] = model_name

        # Then, add direct slot mappings for convenience
        for slot_name, model_name in slots.items():
            model_alias_map[slot_name] = model_name

        # Build fallbacks structure
        fallback_dict = {}
        for model_name, fb_list in fallbacks.items():
            fallback_dict[model_name] = fb_list

        config = {
            "model_list": model_list,
            "litellm_settings": {
                "timeout": 90,
                "max_retries": 2,
                "drop_params": True,
                "model_alias_map": model_alias_map,
                "fallbacks": fallback_dict,
                "default_fallbacks": default_fb,
            },
            "general_settings": {
                "master_key": master_key,
            },
        }

        return config

    def generate_ccr_config(
        self, litellm_url: str, litellm_key: str, ccr_api_key: str
    ) -> Dict[str, Any]:
        """Generate Claude Code Router configuration.

        Args:
            litellm_url: URL of the LiteLLM proxy (without /v1)
            litellm_key: Master key for LiteLLM
            ccr_api_key: API key for CCR itself

        Returns:
            Dictionary containing CCR configuration in CCR's expected format
        """
        models = self.config.get("models", [])
        slots = self.config.get("slots", {})

        default_model = slots.get("default", all_model_names[0] if all_model_names else "default")

        return {
            "LOG": True,
            "LOG_LEVEL": "info",
            "HOST": "127.0.0.1",
            "PORT": self.config["ports"]["ccr"],
            "API_TIMEOUT_MS": 600000,
            "Providers": [
                {
                    "name": "litellm",
                    "api_base_url": f"{litellm_url}/v1",
                    "api_key": litellm_key,
                    "models": all_model_names,
                }
            ],
            "Router": {
                "default": f"litellm,{default_model}",
            },
        }


    def _get_provider_by_name(self, name: str) -> Dict[str, Any]:
        """Get provider by name."""
        providers = self.config.get("providers", [])
        for provider in providers:
            if provider["name"] == name:
                return provider
        raise RoutingConfigError(f"Provider not found: {name}")

    @classmethod
    def load_default(cls) -> "RoutingConfig":
        """Load the default routing configuration."""
        config = cls()
        config.load()
        return config

    @classmethod
    def get_mode(cls) -> str:
        """Get the current routing mode."""
        config = cls()
        config.load()
        return config.config["mode"]

    @classmethod
    def is_api_mode(cls) -> bool:
        """Check if routing is in API mode (using LiteLLM proxy)."""
        return cls.get_mode() == "api"

    @classmethod
    def is_subscription_mode(cls) -> bool:
        """Check if routing is in subscription mode (direct to Anthropic)."""
        return cls.get_mode() == "subscription"

    def get_ports(self) -> Dict[str, int]:
        """Get the configured ports.

        Returns:
            Dictionary of port names and numbers
        """
        if not self._loaded:
            self.load()
        return self.config.get("ports", {})
