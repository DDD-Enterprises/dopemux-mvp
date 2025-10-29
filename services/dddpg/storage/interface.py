"""
DDDPG Storage Interface
Abstract base class for all storage backends
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..core.models import Decision, DecisionRelationship, DecisionGraph, WorkSession


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
        raise NotImplementedError("Graph relationships not supported by this backend")
    
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
        raise NotImplementedError("Graph queries not supported by this backend")
    
    # ===== Sessions (optional) =====
    
    async def create_session(self, session: WorkSession) -> WorkSession:
        """Create work session (optional)"""
        raise NotImplementedError("Sessions not supported by this backend")
    
    async def get_active_session(self, workspace_id: str, instance_id: str) -> Optional[WorkSession]:
        """Get active session for instance (optional)"""
        return None


__all__ = ["StorageBackend"]
