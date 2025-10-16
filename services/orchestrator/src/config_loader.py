"""
Configuration Loader - Production CLI Configuration System
Loads and validates agent configuration with ADHD-optimized error handling

Features:
- Auto-detection of CLI paths (PATH + common locations)
- Environment variable resolution with ${VAR} syntax
- Clear, actionable validation errors
- Zero-config defaults
- Layered configuration (project > user > defaults)
"""

import yaml
import os
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


class ConfigError(Exception):
    """Configuration validation error with ADHD-friendly messaging."""
    pass


@dataclass
class AgentConfig:
    """Validated agent configuration."""
    name: str
    agent_type: str  # 'cli' or 'mcp'
    command: Optional[str] = None
    args: Optional[List[str]] = None
    default_model: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    auto_restart: bool = True
    max_restarts: int = 3

    # MCP-specific
    zen_model: Optional[str] = None
    capabilities: Optional[List[str]] = None


class ConfigLoader:
    """
    Load and validate Dopemux agent configuration.

    Priority order:
    1. Explicit path (if provided)
    2. ./config/agents.yaml (project-specific)
    3. ~/.config/dopemux/agents.yaml (user default)
    4. Built-in defaults (zero-config fallback)
    """

    COMMON_PATHS = {
        'claude': [
            '~/.local/bin/claude',
            '/usr/local/bin/claude',
            '/opt/homebrew/bin/claude',
        ],
        'gemini': [
            '~/.local/bin/gemini',
            '/usr/local/bin/gemini',
            '/opt/homebrew/bin/gemini',
        ],
        'codex': [
            '~/.nvm/versions/node/v22.18.0/bin/codex',
            '/usr/local/bin/codex',
        ],
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.

        Args:
            config_path: Optional explicit path to config file
        """
        self.config_path = config_path
        self.config: Optional[Dict[str, Any]] = None
        self.agents: Dict[str, AgentConfig] = {}

    def load(self) -> Dict[str, AgentConfig]:
        """
        Load and validate configuration.

        Returns:
            Dictionary of agent name -> AgentConfig

        Raises:
            ConfigError: If configuration is invalid
        """
        # Find config file
        config_file = self._find_config_file()

        if config_file:
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
            print(f"✅ Loaded config from: {config_file}")
        else:
            # Use built-in defaults
            self.config = self._get_default_config()
            print("ℹ️  Using built-in defaults (no config file found)")

        # Resolve environment variables
        self.config = self._resolve_env_vars(self.config)

        # Validate configuration
        self._validate_config()

        # Build agent configs
        self._build_agent_configs()

        return self.agents

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in priority order."""
        search_paths = [
            self.config_path,
            Path("./config/agents.yaml"),
            Path("./agents.yaml"),
            Path.home() / ".config/dopemux/agents.yaml",
        ]

        for path in search_paths:
            if path and Path(path).exists():
                return Path(path)

        return None

    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve ${VAR} and ${VAR:default} in configuration.

        Examples:
            ${ANTHROPIC_API_KEY} -> value from environment
            ${CLAUDE_MODEL:claude-sonnet-4.5} -> value or default
        """
        def replace_env_var(match):
            var_part = match.group(1)
            if ':' in var_part:
                var_name, default = var_part.split(':', 1)
            else:
                var_name, default = var_part, ''
            return os.getenv(var_name, default)

        config_str = yaml.dump(config)
        resolved_str = re.sub(r'\$\{([^}]+)\}', replace_env_var, config_str)
        return yaml.safe_load(resolved_str)

    def _validate_config(self):
        """
        Validate configuration with ADHD-friendly error messages.

        Raises:
            ConfigError: If configuration has critical errors
        """
        errors = []
        warnings = []

        if 'agents' not in self.config:
            errors.append("❌ Missing 'agents' section in config")
            raise ConfigError("\n".join(errors))

        for agent_name, agent_config in self.config['agents'].items():
            agent_type = agent_config.get('type', 'cli')  # Default to CLI

            if agent_type == 'mcp':
                # MCP provider validation
                if not agent_config.get('zen_model'):
                    errors.append(f"❌ {agent_name}: MCP agents require 'zen_model'")
                continue

            # CLI provider validation
            if not agent_config.get('command'):
                errors.append(f"❌ {agent_name}: CLI agents require 'command'")
                continue

            # Check if CLI exists
            cli_path = self._find_cli_path(agent_config['command'])
            if not cli_path:
                errors.append(f"❌ {agent_name}: CLI '{agent_config['command']}' not found")
                errors.append(f"   💡 Try: which {agent_config['command']}")
                errors.append(f"   💡 Or install: pip install {agent_config['command']}-cli")
            else:
                print(f"✅ {agent_name}: Found at {cli_path}")

            # Check required environment variables
            for env_key, env_value in agent_config.get('env', {}).items():
                # Check if it was a required variable that didn't get resolved
                if env_value == '' and env_key in ['ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']:
                    # Only warn, not error (could be optional)
                    warnings.append(f"⚠️  {agent_name}: {env_key} not set (may be optional)")

        if errors:
            print("\n🚨 Configuration Errors:\n")
            print("\n".join(errors))
            print("\n💡 Fix the errors above and try again\n")
            raise ConfigError(f"{len(errors)} configuration error(s)")

        if warnings:
            print("\n⚠️  Configuration Warnings:\n")
            print("\n".join(warnings))
            print()

    def _find_cli_path(self, command: str) -> Optional[str]:
        """
        Find CLI executable with multi-strategy resolution.

        Strategy 1: Check PATH (works 80% of time)
        Strategy 2: Check common install locations
        Strategy 3: Return None if not found

        Args:
            command: CLI command name (e.g., 'claude', 'gemini')

        Returns:
            Absolute path to CLI or None if not found
        """
        # Strategy 1: PATH resolution (most common)
        if cli_path := shutil.which(command):
            return cli_path

        # Strategy 2: Common install locations
        for location in self.COMMON_PATHS.get(command, []):
            path = Path(location).expanduser()
            if path.exists() and os.access(path, os.X_OK):
                return str(path)

        return None

    def _build_agent_configs(self):
        """Build validated AgentConfig objects from raw config."""
        for agent_name, agent_data in self.config['agents'].items():
            agent_type = agent_data.get('type', 'cli')

            if agent_type == 'mcp':
                # MCP provider
                self.agents[agent_name] = AgentConfig(
                    name=agent_name,
                    agent_type='mcp',
                    zen_model=agent_data.get('zen_model'),
                    capabilities=agent_data.get('capabilities', []),
                )
            else:
                # CLI provider
                command = agent_data['command']
                cli_path = self._find_cli_path(command)

                self.agents[agent_name] = AgentConfig(
                    name=agent_name,
                    agent_type='cli',
                    command=cli_path or command,  # Use resolved path or original
                    args=agent_data.get('args', []),
                    default_model=agent_data.get('default_model'),
                    env=agent_data.get('env', {}),
                    auto_restart=agent_data.get('auto_restart', True),
                    max_restarts=agent_data.get('max_restarts', 3),
                )

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Built-in zero-config defaults.

        Provides sensible defaults for common AI CLIs that work out-of-box.
        """
        return {
            'agents': {
                'claude': {
                    'command': 'claude',
                    'args': ['chat'],
                    'default_model': 'claude-sonnet-4.5',
                    'auto_restart': True,
                },
                'gemini': {
                    'command': 'gemini',
                    'default_model': 'gemini-2.5-pro',
                    'auto_restart': True,
                },
            },
            'task_routing': {
                'research': 'gemini',
                'code': 'claude',
                'review': 'claude',
            },
            'advanced': {
                'max_concurrent_agents': 3,
                'auto_save_interval': 30,
                'health_check_interval': 60,
            }
        }

    def get_task_routing(self) -> Dict[str, str]:
        """Get task-based routing configuration."""
        return self.config.get('task_routing', {})

    def get_advanced_settings(self) -> Dict[str, Any]:
        """Get advanced configuration settings."""
        return self.config.get('advanced', {})

    def reload(self) -> Dict[str, AgentConfig]:
        """
        Reload configuration (for manual reload command).

        Returns:
            Updated agent configurations
        """
        print("🔄 Reloading configuration...")
        return self.load()


# Convenience function for simple usage
def load_agent_config(config_path: Optional[str] = None) -> Dict[str, AgentConfig]:
    """
    Load agent configuration with single function call.

    Args:
        config_path: Optional explicit path to config file

    Returns:
        Dictionary of agent name -> AgentConfig

    Example:
        >>> agents = load_agent_config()
        >>> claude_config = agents['claude']
        >>> print(claude_config.command)
        '/usr/local/bin/claude'
    """
    loader = ConfigLoader(config_path)
    return loader.load()


if __name__ == "__main__":
    """Test configuration loader."""
    print("🧪 Testing Configuration Loader")
    print("=" * 60)

    try:
        agents = load_agent_config()

        print(f"\n✅ Loaded {len(agents)} agents:")
        for name, config in agents.items():
            print(f"\n  {name}:")
            print(f"    Type: {config.agent_type}")
            if config.agent_type == 'cli':
                print(f"    Command: {config.command}")
                print(f"    Args: {config.args}")
                print(f"    Model: {config.default_model}")
            else:
                print(f"    Zen Model: {config.zen_model}")
                print(f"    Capabilities: {config.capabilities}")

        print("\n✅ Configuration loader test passed!")

    except ConfigError as e:
        print(f"\n❌ Configuration error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
