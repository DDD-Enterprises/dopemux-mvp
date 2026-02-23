"""Global routing configuration management for Dopemux."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class RoutingConfigError(RuntimeError):
    """Raised when routing configuration is invalid or cannot be loaded."""


class RoutingConfig:
    """Manage the global routing configuration for Dopemux."""

    DEFAULT_CONFIG_PATH = Path.home() / ".dopemux" / "routing.yaml"
    TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "routing.yaml"

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
                    f"Routing config not found at {self.config_path} and no template available"
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
            logger.info(f"Initialized routing config from template at {self.config_path}")
        except Exception as e:
            raise RoutingConfigError(f"Failed to copy template: {e}") from e

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
            raise RoutingConfigError(f"Unsupported config version: {self.config.get('version')}")

        # Check required sections
        required_sections = ["mode", "ports", "providers", "models", "slots", "fallbacks", "default_fallbacks", "aliases"]
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
            if "api_key_env" not in provider:
                raise RoutingConfigError(f"Provider {provider['name']} missing 'api_key_env' field")
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
                raise RoutingConfigError(f"Model {model['name']} missing 'provider' field")
            if "model_id" not in model:
                raise RoutingConfigError(f"Model {model['name']} missing 'model_id' field")
            
            # Check provider exists
            if model["provider"] not in provider_names:
                raise RoutingConfigError(
                    f"Model {model['name']} references unknown provider: {model['provider']}"
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
                        f"Fallbacks for {model_name} references unknown model: {fb_model}"
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
                raise RoutingConfigError(
                    f"Alias {alias} references unknown slot: {target}"
                )

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

        models = self.config.get("models", [])
        slots = self.config.get("slots", {})
        fallbacks = self.config.get("fallbacks", {})
        default_fb = self.config.get("default_fallbacks", [])
        aliases = self.config.get("aliases", {})

        # Build model_list
        model_list = []
        for model in models:
            provider = self._get_provider_by_name(model["provider"])
            
            litellm_params = {
                "model": model["model_id"],
                "api_key": f"os.environ/{provider['api_key_env']}",
                "max_tokens": model.get("max_tokens", 131072),
            }
            
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
            litellm_url: URL of the LiteLLM proxy
            litellm_key: Master key for LiteLLM
            ccr_api_key: API key for CCR itself
            
        Returns:
            Dictionary containing CCR configuration
            
        Note:
            This does NOT include upstream API keys - those are handled by environment variables.
        """
        if not self._loaded:
            raise RoutingConfigError("Config not loaded - call load() first")

        slots = self.config.get("slots", {})
        
        # CCR exposes slot names as model names
        ccr_models = list(slots.keys())
        
        return {
            "provider": "litellm",
            "upstream_url": litellm_url,
            "upstream_key_var": "DOPEMUX_LITELLM_MASTER_KEY",
            "models": ccr_models,
            "api_key": ccr_api_key,
            "listen_port": self.config["ports"]["ccr"],
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
