"""Configuration management for ChatX."""

import json
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(..., description="LLM provider name")
    model: str | None = Field(None, description="Model identifier")
    api_key: str | None = Field(None, description="API key (use env var in production)")
    base_url: str | None = Field(None, description="Base URL for API")
    max_retries: int = Field(3, description="Maximum retry attempts")
    timeout: int = Field(60, description="Request timeout in seconds")


class RedactionConfig(BaseModel):
    """Privacy redaction configuration."""
    strict_mode: bool = Field(True, description="Enable strict redaction mode")
    policy_file: Path | None = Field(None, description="Path to privacy policy file")
    generate_report: bool = Field(True, description="Generate redaction reports")
    fail_on_leak: bool = Field(True, description="Fail if privacy leaks detected")


class EmbeddingConfig(BaseModel):
    """Embedding provider configuration."""
    default_provider: str = Field("stella", description="Default embedding provider")
    fallback_chain: List[str] = Field(
        default_factory=lambda: ["stella", "cohere", "legacy"],
        description="Provider fallback chain"
    )
    model_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Provider-specific model identifiers"
    )
    cache_enabled: bool = Field(True, description="Enable embedding cache")
    cache_ttl_hours: int = Field(24, description="Cache TTL in hours")


class Neo4jConfig(BaseModel):
    """Neo4j database configuration."""
    uri: str = Field(..., description="Neo4j connection URI")
    username: str = Field("neo4j", description="Database username")
    password: str = Field(..., description="Database password")
    max_connection_lifetime: int = Field(300, description="Max connection lifetime in seconds")
    max_connection_pool_size: int = Field(100, description="Max connection pool size")
    connection_timeout: int = Field(30, description="Connection timeout in seconds")
    connection_acquisition_timeout: int = Field(60, description="Max time to wait for connection from pool (seconds)")

    @classmethod
    def from_preset(cls, uri: str, username: str, password: str, preset_name: str) -> "Neo4jConfig":
        """Create Neo4jConfig using a predefined preset.
        
        Args:
            uri: Neo4j connection URI
            username: Database username  
            password: Database password
            preset_name: Name of preset configuration
            
        Returns:
            Neo4jConfig instance with preset parameters
        """
        preset_params = Neo4jPoolPreset.get_preset(preset_name)
        
        return cls(
            uri=uri,
            username=username,
            password=password,
            **preset_params
        )

class Neo4jPoolPreset:
    """Predefined connection pool configurations for different use cases."""
    
    @staticmethod
    def development() -> Dict[str, int]:
        """Development environment preset - minimal resources."""
        return {
            "max_connection_lifetime": 300,  # 5 minutes
            "max_connection_pool_size": 10,  # Small pool
            "connection_timeout": 15,        # Quick timeout
            "connection_acquisition_timeout": 30  # Quick acquisition
        }
    
    @staticmethod
    def production_low_traffic() -> Dict[str, int]:
        """Production environment with low traffic."""
        return {
            "max_connection_lifetime": 600,  # 10 minutes
            "max_connection_pool_size": 25,  # Medium pool
            "connection_timeout": 30,        # Standard timeout
            "connection_acquisition_timeout": 60  # Standard acquisition
        }
    
    @staticmethod
    def production_high_traffic() -> Dict[str, int]:
        """Production environment with high concurrent traffic."""
        return {
            "max_connection_lifetime": 900,  # 15 minutes
            "max_connection_pool_size": 100, # Large pool
            "connection_timeout": 45,        # Longer timeout for busy server
            "connection_acquisition_timeout": 120  # Longer acquisition wait
        }
    
    @staticmethod
    def batch_processing() -> Dict[str, int]:
        """Optimized for batch processing workloads."""
        return {
            "max_connection_lifetime": 1200, # 20 minutes - long-running
            "max_connection_pool_size": 50,  # Medium pool
            "connection_timeout": 60,        # Patient timeout
            "connection_acquisition_timeout": 180  # Very patient acquisition
        }
    
    @staticmethod
    def realtime_analytics() -> Dict[str, int]:
        """Optimized for real-time analytics with frequent queries."""
        return {
            "max_connection_lifetime": 300,  # 5 minutes - refresh frequently
            "max_connection_pool_size": 75,  # High pool for concurrency
            "connection_timeout": 20,        # Quick timeout for responsiveness
            "connection_acquisition_timeout": 45  # Quick acquisition
        }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Dict[str, int]:
        """Get preset configuration by name.
        
        Args:
            preset_name: Name of preset (development, production_low_traffic, 
                        production_high_traffic, batch_processing, realtime_analytics)
                        
        Returns:
            Dictionary with connection pool parameters
            
        Raises:
            ValueError: If preset name is not recognized
        """
        presets = {
            "development": cls.development,
            "production_low_traffic": cls.production_low_traffic,
            "production_high_traffic": cls.production_high_traffic,
            "batch_processing": cls.batch_processing,
            "realtime_analytics": cls.realtime_analytics
        }
        
        if preset_name not in presets:
            available = ", ".join(presets.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")
        
        return presets[preset_name]()


class Settings(BaseSettings):
    """Environment-based settings with feature flags."""
    
    # Feature flags
    allow_cloud: bool = Field(False, description="Allow cloud-based processing")
    enable_sota: bool = Field(True, description="Enable SOTA embedding models")
    enable_gpu: bool = Field(False, description="Enable GPU acceleration")
    
    # Provider settings
    default_provider: str = Field("stella", description="Default embedding provider")
    fallback_chain: List[str] = Field(
        default_factory=lambda: ["stella", "cohere", "legacy"],
        description="Provider fallback chain"
    )
    
    # Database connection
    neo4j_uri: str = Field("bolt://localhost:7687", description="Neo4j URI")
    neo4j_username: str = Field("neo4j", description="Neo4j username")  
    neo4j_password: str = Field("password", description="Neo4j password")
    
    # Model configurations
    model_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Provider-specific model identifiers"
    )
    
    class Config:
        env_prefix = "CHATX_"
        case_sensitive = False


class Config(BaseModel):
    """Main ChatX configuration."""
    
    # General settings
    verbose: bool = Field(False, description="Enable verbose output")
    output_dir: Path = Field(Path("./output"), description="Default output directory")
    temp_dir: Path | None = Field(None, description="Temporary directory")
    
    # LLM settings
    llm: LLMConfig = Field(
        default_factory=lambda: LLMConfig(
            provider="local",
            model=None,
            api_key=None,
            base_url=None,
            max_retries=3,
            timeout=60
        ),
        description="LLM configuration"
    )
    
    # Embedding settings
    embeddings: EmbeddingConfig = Field(
        default_factory=lambda: EmbeddingConfig(
            default_provider="stella",
            cache_enabled=True,
            cache_ttl_hours=24
        ),
        description="Embedding provider configuration"
    )
    
    # Database settings
    neo4j: Neo4jConfig = Field(
        default_factory=lambda: Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j", 
            password="password",
            max_connection_lifetime=300,
            max_connection_pool_size=100,
            connection_timeout=30,
            connection_acquisition_timeout=60
        ),
        description="Neo4j database configuration"
    )
    
    # Privacy settings
    redaction: RedactionConfig = Field(
        default_factory=lambda: RedactionConfig(
            strict_mode=True,
            policy_file=None,
            generate_report=True,
            fail_on_leak=True
        ),
        description="Redaction configuration"
    )
    
    # Processing settings
    batch_size: int = Field(10, description="Default batch size for processing")
    max_workers: int = Field(4, description="Maximum parallel workers")
    
    @classmethod
    def load(cls, config_path: str | Path) -> "Config":
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Config instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with config_path.open() as f:
                data = json.load(f)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}") from e
        except Exception as e:
            raise ValueError(f"Error loading config: {e}") from e
    
    def save(self, config_path: str | Path) -> None:
        """Save configuration to file.
        
        Args:
            config_path: Path where to save configuration
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with config_path.open("w") as f:
            json.dump(self.dict(), f, indent=2, default=str)
    
    @classmethod
    def default(cls) -> "Config":
        """Create default configuration.
        
        Returns:
            Config instance with default values
        """
        return cls(
            verbose=False,
            output_dir=Path("./output"),
            temp_dir=None,
            batch_size=10,
            max_workers=4
        )


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from file or create default.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Config instance
    """
    if config_path is None:
        # Look for config in standard locations
        candidates = [
            Path("./chatx.json"),
            Path("~/.config/chatx/config.json").expanduser(),
            Path("~/.chatx.json").expanduser(),
        ]
        
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break
    
    if config_path and Path(config_path).exists():
        return Config.load(config_path)
    else:
        return Config.default()


# Global settings instance
settings = Settings(
    allow_cloud=False,
    enable_sota=True,
    enable_gpu=False,
    default_provider="stella",
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="password"
)
