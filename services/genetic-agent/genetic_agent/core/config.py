"""Configuration management for the Genetic Coding Agent system."""

import asyncio
import logging
from typing import List, Tuple
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class AgentConfig(BaseSettings):
    """Configuration for agent behavior and limits."""

    # Token and resource limits
    max_tokens: int = Field(default=24000, description="Maximum tokens per repair operation")
    timeout_seconds: int = Field(default=300, description="Timeout for repair operations")
    max_iterations: int = Field(default=5, description="Maximum repair iterations")

    # Quality thresholds
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for successful repair")

    # Genetic algorithm parameters (for genetic agent)
    population_size: int = Field(default=10, description="Initial population size")
    max_generations: int = Field(default=5, description="Maximum generations")
    crossover_rate: float = Field(default=0.8, description="Crossover probability")
    mutation_rate: float = Field(default=0.2, description="Mutation probability")
    max_tree_depth: int = Field(default=5, description="Maximum tree depth for GP operators")

    # MCP service URLs
    conport_url: str = Field(default="http://localhost:3000", description="ConPort service URL")
    serena_url: str = Field(default="http://localhost:3001", description="Serena service URL")
    dope_context_url: str = Field(default="http://localhost:3002", description="Dope-Context service URL")
    zen_url: str = Field(default="http://localhost:3003", description="Zen MCP service URL")
    workspace_id: str = Field(default="/app/workspace", description="Workspace ID for MCP services")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    health_check_interval: int = Field(default=300, description="Health check interval in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")

    # EventBus and user context
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL for EventBus")
    user_id: str = Field(default="default_user", description="User ID for event filtering")

    class Config:
        env_prefix = "GENETIC_AGENT_"
        case_sensitive = False

    @field_validator('conport_url', 'serena_url', 'dope_context_url', 'zen_url')
    @classmethod
    def validate_mcp_url(cls, v: str) -> str:
        """Validate MCP service URLs for proper format."""
        if not v:
            raise ValueError("MCP URL cannot be empty")

        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {v}")
            if parsed.scheme not in ['http', 'https']:
                raise ValueError(f"URL must use http or https scheme: {v}")
        except Exception as e:
            raise ValueError(f"Invalid MCP URL '{v}': {e}")

        return v

    async def validate_mcp_connectivity(self) -> List[Tuple[str, bool, str]]:
        """Validate connectivity to MCP services."""
        services = [
            ("ConPort", self.conport_url),
            ("Serena", self.serena_url),
            ("Dope-Context", self.dope_context_url),
            ("Zen", self.zen_url),
        ]

        results = []
        timeout = aiohttp.ClientTimeout(total=5.0)  # 5 second timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for name, url in services:
                reachable = False
                error_msg = ""

                try:
                    # Try to reach the health endpoint
                    health_url = f"{url.rstrip('/')}/health"
                    async with session.get(health_url) as response:
                        if response.status == 200:
                            reachable = True
                        else:
                            error_msg = f"Health check failed with status {response.status}"
                except aiohttp.ClientError as e:
                    error_msg = f"Connection failed: {str(e)}"
                except asyncio.TimeoutError:
                    error_msg = "Connection timeout"
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"

                results.append((name, reachable, error_msg))
                if reachable:
                    logger.info(f"✓ {name} service reachable at {url}")
                else:
                    logger.warning(f"✗ {name} service unreachable at {url}: {error_msg}")

        return results

    def validate_environment(self) -> List[str]:
        """Validate environment configuration and return warnings."""
        warnings = []

        # Check required MCP URLs
        mcp_urls = [self.conport_url, self.serena_url, self.dope_context_url, self.zen_url]
        if any(not url for url in mcp_urls):
            warnings.append("Some MCP service URLs are not configured")

        # Check workspace ID
        if not self.workspace_id or self.workspace_id == "/app/workspace":
            warnings.append("Workspace ID not properly configured (using default)")

        # Check resource limits
        if self.max_tokens < 1000:
            warnings.append("Max tokens is very low (< 1000)")
        if self.confidence_threshold < 0.1:
            warnings.append("Confidence threshold is very low (< 0.1)")

        # Check genetic algorithm parameters
        if self.population_size < 3:
            warnings.append("Population size is too small for effective evolution")
        if self.max_generations < 2:
            warnings.append("Max generations is too low for meaningful evolution")

        return warnings


class MCPConfig(BaseSettings):
    """Configuration for MCP service connections."""

    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    health_check_interval: int = Field(default=300, description="Health check interval in seconds")

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False