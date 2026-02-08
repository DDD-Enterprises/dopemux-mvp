"""
Agent Config Factory - Bridge between config loader and agent spawner

Converts new ConfigLoader output to existing AgentConfig/AgentType format
for backwards compatibility with existing code.
"""

from typing import Dict

import logging

logger = logging.getLogger(__name__)

from .agent_spawner import AgentConfig, AgentType
from .config_loader import load_agent_config, AgentConfig as LoadedAgentConfig


class AgentConfigFactory:
    """
    Factory for creating AgentConfig instances from configuration file.

    Bridges the gap between new config system and existing spawner code.
    """

    # Map config agent names to AgentType enum
    AGENT_TYPE_MAP = {
        'claude': AgentType.CLAUDE,
        'gemini': AgentType.GEMINI,
        'grok': AgentType.GROK,
        'codex': AgentType.CODEX,
        'aider': AgentType.AIDER,
    }

    def __init__(self, config_path: str = None):
        """
        Initialize factory with configuration.

        Args:
            config_path: Optional path to config file
        """
        self.config_path = config_path
        self.loaded_configs: Dict[str, LoadedAgentConfig] = {}
        self.agent_configs: Dict[AgentType, AgentConfig] = {}

    def load(self) -> Dict[AgentType, AgentConfig]:
        """
        Load configuration and convert to AgentConfig instances.

        Returns:
            Dictionary of AgentType -> AgentConfig for spawner
        """
        # Load configs using config loader
        self.loaded_configs = load_agent_config(self.config_path)

        # Convert to spawner format
        for name, loaded_config in self.loaded_configs.items():
            # Skip MCP providers (handled separately)
            if loaded_config.agent_type == 'mcp':
                logger.info(f"ℹ️  {name}: MCP provider (not spawned via PTY)")
                continue

            # Get AgentType enum
            agent_type = self.AGENT_TYPE_MAP.get(name)
            if not agent_type:
                logger.info(f"⚠️  {name}: Unknown agent type, skipping")
                continue

            # Build command list
            command = [loaded_config.command] + (loaded_config.args or [])

            # Create AgentConfig for spawner
            self.agent_configs[agent_type] = AgentConfig(
                agent_type=agent_type,
                command=command,
                env=loaded_config.env or {},
                auto_restart=loaded_config.auto_restart,
                max_restarts=loaded_config.max_restarts,
            )

        return self.agent_configs

    def get_config_for_agent(self, agent_type: AgentType) -> AgentConfig:
        """
        Get configuration for specific agent.

        Args:
            agent_type: Agent type enum

        Returns:
            AgentConfig for the agent

        Raises:
            KeyError: If agent not configured
        """
        if not self.agent_configs:
            self.load()

        return self.agent_configs[agent_type]

    def list_available_agents(self) -> list[AgentType]:
        """
        List all configured CLI agents (excludes MCP providers).

        Returns:
            List of available AgentType enums
        """
        if not self.agent_configs:
            self.load()

        return list(self.agent_configs.keys())

    def get_mcp_providers(self) -> Dict[str, LoadedAgentConfig]:
        """
        Get MCP provider configurations.

        Returns:
            Dictionary of MCP provider configs
        """
        if not self.loaded_configs:
            self.load()

        return {
            name: config
            for name, config in self.loaded_configs.items()
            if config.agent_type == 'mcp'
        }


# Convenience functions for easy migration
def create_agent_configs_from_file(config_path: str = None) -> Dict[AgentType, AgentConfig]:
    """
    Create AgentConfig instances from configuration file.

    This is a drop-in replacement for hardcoded agent configurations.

    Args:
        config_path: Optional path to config file

    Returns:
        Dictionary of AgentType -> AgentConfig

    Example:
        >>> # Old way (hardcoded):
        >>> spawner.register_agent(
        ...     AgentType.CLAUDE,
        ...     AgentConfig(
        ...         agent_type=AgentType.CLAUDE,
        ...         command=["/Users/hue/.local/bin/claude", "chat"],
        ...         env={},
        ...         auto_restart=True,
        ...     ),
        ... )
        >>>
        >>> # New way (from config):
        >>> configs = create_agent_configs_from_file()
        >>> for agent_type, config in configs.items():
        ...     spawner.register_agent(agent_type, config)
    """
    factory = AgentConfigFactory(config_path)
    return factory.load()


def auto_configure_spawner(spawner, config_path: str = None):
    """
    Auto-configure agent spawner from config file.

    Args:
        spawner: AgentSpawner instance
        config_path: Optional path to config file

    Example:
        >>> spawner = AgentSpawner()
        >>> auto_configure_spawner(spawner)
        >>> spawner.start_all()
    """
    configs = create_agent_configs_from_file(config_path)

    for agent_type, config in configs.items():
        spawner.register_agent(agent_type, config)

    logger.info(f"✅ Auto-configured {len(configs)} agents from config file")


if __name__ == "__main__":
    """Test agent config factory."""
    logger.info("🧪 Testing Agent Config Factory")
    logger.info("=" * 60)

    try:
        factory = AgentConfigFactory()
        configs = factory.load()

        logger.info(f"\n✅ Loaded {len(configs)} CLI agents:")
        for agent_type, config in configs.items():
            logger.info(f"\n  {agent_type.value}:")
            logger.info(f"    Command: {config.command}")
            logger.info(f"    Auto-restart: {config.auto_restart}")

        # Show MCP providers separately
        mcp_providers = factory.get_mcp_providers()
        if mcp_providers:
            logger.info(f"\n✅ Found {len(mcp_providers)} MCP providers:")
            for name, config in mcp_providers.items():
                logger.info(f"\n  {name}:")
                logger.info(f"    Zen Model: {config.zen_model}")
                logger.info(f"    Capabilities: {config.capabilities}")

        logger.info("\n✅ Agent config factory test passed!")

    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
