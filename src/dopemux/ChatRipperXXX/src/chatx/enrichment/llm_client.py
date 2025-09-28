"""LLM client for message enrichment."""


from chatx.schemas.enrichment import EnrichmentMessage
from chatx.schemas.message import CanonicalMessage


class LLMClient:
    """Client for interacting with LLM providers."""
    
    def __init__(self, provider: str = "local") -> None:
        """Initialize LLM client.
        
        Args:
            provider: LLM provider name
        """
        self.provider = provider
    
    def enrich_messages(self, messages: list[CanonicalMessage]) -> list[EnrichmentMessage]:
        """Enrich messages with LLM-generated metadata.
        
        Args:
            messages: List of canonical messages to enrich
            
        Returns:
            List of enrichment results
        """
        # TODO: Implement LLM enrichment logic
        return []
