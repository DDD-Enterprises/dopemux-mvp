# DopeconBridge Package

"""
Modular DopeconBridge - Central coordination layer for task management.

This package provides async event coordination between Dopemux services
using Redis Streams, with multi-instance support for git worktree architecture.

Modules:
- core/: Configuration, database, cache, event bus
- models/: SQLAlchemy ORM and Pydantic schemas
- clients/: MCP and ConPort clients
- services/: Business logic (task integration, DDG ingestion)
- api/: FastAPI routes
- auth/: JWT authentication
"""

from .config import settings

__version__ = "2.0.0"
