"""Configuration management for the Genetic Coding Agent system."""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


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

    # MCP service URLs
    conport_url: str = Field(default="http://localhost:3000", description="ConPort service URL")
    serena_url: str = Field(default="http://localhost:3001", description="Serena service URL")
    dope_context_url: str = Field(default="http://localhost:3002", description="Dope-Context service URL")

    class Config:
        env_prefix = "GENETIC_AGENT_"
        case_sensitive = False


class MCPConfig(BaseSettings):
    """Configuration for MCP service connections."""

    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    health_check_interval: int = Field(default=300, description="Health check interval in seconds")

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False