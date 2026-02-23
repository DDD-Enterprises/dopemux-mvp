#!/usr/bin/env python3
"""
Dopemux Routing Configuration

Handles alias resolution for routing requests to appropriate services.
Aliases can reference either slot names or model IDs directly.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import sys
import importlib

# Import standard library logging to avoid conflict with dopemux.logging
import logging as std_logging
logger = std_logging.getLogger(__name__)


class RoutingValidationError(ValueError):
    """Raised when routing configuration is invalid."""
    pass


class RoutingConfig:
    """Routing configuration with alias resolution."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.slots = self.config.get("slots", {})
        self.models = self.config.get("models", {})
        self.aliases = self.config.get("aliases", {})
        
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "RoutingConfig":
        """Load routing configuration from file or use defaults."""
        config = {}
        
        # Try to load from default location if no path specified
        if config_path is None:
            default_path = Path("~/.dopemux/routing_config.yaml").expanduser()
            if default_path.exists():
                try:
                    with open(default_path, 'r') as f:
                        config = yaml.safe_load(f) or {}
                except Exception as e:
                    logger.warning(f"Failed to load routing config from {default_path}: {e}")
        elif Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load routing config from {config_path}: {e}")
        
        return cls(config)
    
    def validate(self) -> None:
        """Validate that all aliases point to valid slots or models."""
        errors = []
        
        for alias_name, alias_target in self.aliases.items():
            # Check if alias points to a slot
            if alias_target in self.slots:
                logger.debug(f"Alias {alias_name} -> slot {alias_target}")
                continue
            
            # Check if alias points to a model directly
            if alias_target in self.models:
                logger.debug(f"Alias {alias_name} -> model {alias_target}")
                continue
            
            # Neither slot nor model - this is an error
            errors.append(f"Alias '{alias_name}' points to '{alias_target}' which is neither a slot nor a model")
        
        if errors:
            raise RoutingValidationError("\n".join(errors))
        
        logger.info(f"Routing configuration validated: {len(self.aliases)} aliases, "
                   f"{len(self.slots)} slots, {len(self.models)} models")
    
    def resolve_alias(self, alias_name: str) -> str:
        """
        Resolve an alias to its final target (model ID).
        
        Args:
            alias_name: Name of the alias to resolve
            
        Returns:
            Final model ID that the alias points to
            
        Raises:
            KeyError: If alias doesn't exist
            RoutingValidationError: If alias points to invalid target
        """
        if alias_name not in self.aliases:
            raise KeyError(f"Alias '{alias_name}' not found")
        
        alias_target = self.aliases[alias_name]
        
        # If alias points to a slot, resolve to the model ID
        if alias_target in self.slots:
            model_id = self.slots[alias_target]
            logger.debug(f"Resolved alias {alias_name} -> slot {alias_target} -> model {model_id}")
            return model_id
        
        # If alias points directly to a model, use it
        if alias_target in self.models:
            logger.debug(f"Resolved alias {alias_name} -> model {alias_target}")
            return alias_target
        
        # This should have been caught by validate(), but just in case...
        raise RoutingValidationError(f"Alias '{alias_name}' points to '{alias_target}' which is neither a slot nor a model")
    
    def get_mode(self) -> str:
        """Get the current routing mode."""
        return self.config.get("mode", "default")


if __name__ == "__main__":
    # Simple test
    config = {
        "mode": "test",
        "slots": {
            "fast": "gpt-4-turbo",
            "smart": "claude-3-opus"
        },
        "models": {
            "gpt-4-turbo": {"provider": "openai"},
            "claude-3-opus": {"provider": "anthropic"}
        },
        "aliases": {
            "/model/fast": "fast",           # alias -> slot
            "/model/smart": "smart",         # alias -> slot  
            "/model/direct": "gpt-4-turbo"  # alias -> model directly
        }
    }
    
    rc = RoutingConfig(config)
    try:
        rc.validate()
        print("✅ Routing configuration validated successfully")
        print(f"Mode: {rc.get_mode()}")
        print(f"Alias /model/fast resolves to: {rc.resolve_alias('/model/fast')}")
        print(f"Alias /model/smart resolves to: {rc.resolve_alias('/model/smart')}")
        print(f"Alias /model/direct resolves to: {rc.resolve_alias('/model/direct')}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        exit(1)
