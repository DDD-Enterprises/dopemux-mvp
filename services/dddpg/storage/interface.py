"""
DDDPG Storage Interface
Abstract base class for all storage backends
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging
from ..core.models import Decision, DecisionRelationship, DecisionGraph, WorkSession

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract storage interface - all backends must implement this"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to storage backend"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from storage"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if storage is healthy"""
        pass
    
    # ===== Decisions =====
    
    @abstractmethod
    async def create_decision(self, decision: Decision) -> Decision:
        """Create a new decision, returns with ID assigned"""
        pass
    
    @abstractmethod
    async def get_decision(self, decision_id: int) -> Optional[Decision]:
        """Get decision by ID"""
        pass
    
    @abstractmethod
    async def list_decisions(
        self,
        workspace_id: str,
        instance_id: str,
        include_shared: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Decision]:
        """
        List decisions for instance
        
        Args:
            workspace_id: Workspace root path
            instance_id: Instance identifier (A, B, feature-auth, etc)
            include_shared: Include decisions with visibility=shared
            limit: Max results
            offset: Pagination offset
        """
        pass
    
    @abstractmethod
    async def update_decision(self, decision: Decision) -> Decision:
        """Update existing decision"""
        pass
    
    @abstractmethod
    async def delete_decision(self, decision_id: int) -> bool:
        """Delete decision (soft delete - set status=archived)"""
        pass
    
    # ===== Search =====
    
    @abstractmethod
    async def search_decisions(
        self,
        query: str,
        workspace_id: str,
        instance_id: str,
        limit: int = 10
    ) -> List[Decision]:
        """Full-text search for decisions"""
        pass
    
    # ===== Relationships (optional - implement if backend supports graphs) =====
    
    async def create_relationship(self, rel: DecisionRelationship) -> DecisionRelationship:
        """Create relationship between decisions (optional)"""
        logger.debug(
            "Storage backend %s does not support graph relationships; returning input relationship unchanged.",
            self.__class__.__name__,
        )
        return rel
    
    async def get_relationships(self, decision_id: int) -> List[DecisionRelationship]:
        """Get all relationships for a decision (optional)"""
        return []
    
    async def query_graph(
        self,
        start_decision_id: int,
        depth: int = 1,
        relationship_types: Optional[List[str]] = None
    ) -> DecisionGraph:
        """Traverse graph from starting decision (optional)"""
        logger.debug(
            "Storage backend %s does not support graph queries; returning empty DecisionGraph.",
            self.__class__.__name__,
        )
        return DecisionGraph(
            nodes=[],
            edges=[],
            query_type="unsupported",
            depth=max(1, depth),
            total_nodes=0,
        )
    
    # ===== Sessions (optional) =====
    
    async def create_session(self, session: WorkSession) -> WorkSession:
        """Create work session (optional)"""
        logger.debug(
            "Storage backend %s does not support sessions; returning input session unchanged.",
            self.__class__.__name__,
        )
        return session
    
    async def get_active_session(self, workspace_id: str, instance_id: str) -> Optional[WorkSession]:
        """Get active session for instance (optional)"""
        return None


__all__ = ["StorageBackend"]
