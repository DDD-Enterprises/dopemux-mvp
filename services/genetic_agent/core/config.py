"""Configuration management for the Genetic Coding Agent system."""

from typing import List
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

    # Development mode configuration
    development_mode: str = Field(default="repair", description="Current development mode (repair, ideation, design, implementation, integration, testing, documentation)")

    # Ideation and research parameters
    research_depth: int = Field(default=5, description="Depth of research queries for ideation")
    max_ideas: int = Field(default=3, description="Maximum number of ideas to generate in ideation mode")

    # Design and planning parameters
    planning_steps: int = Field(default=3, description="Number of planning steps in design mode")
    max_components: int = Field(default=5, description="Maximum components to identify in design")

    # Implementation parameters
    code_generation_style: str = Field(default="modern", description="Code style preference (modern, legacy, minimal)")
    incremental_validation: bool = Field(default=True, description="Validate code incrementally during generation")

    # Integration parameters
    integration_strategy: str = Field(default="merge", description="Integration approach (merge, branch, patch)")
    dependency_resolution: bool = Field(default=True, description="Automatically resolve dependencies")

    # Testing parameters
    test_coverage_target: float = Field(default=0.8, description="Target test coverage percentage")
    test_types: List[str] = Field(default=["unit", "integration"], description="Types of tests to generate")

    # Documentation parameters
    doc_format: str = Field(default="markdown", description="Documentation format (markdown, html, api)")
    doc_level: str = Field(default="comprehensive", description="Documentation detail level")

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

    # EventBus and user context
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL for EventBus")
    user_id: str = Field(default="default_user", description="User ID for event filtering")

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