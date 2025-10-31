#!/usr/bin/env python3
"""
ConPort-KG Authentication Database Connection
Part of Phase 1 Security Hardening

Database connection and session management for authentication.
"""

import os
import sys
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models
from .models import Base

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph"
)

# Connection pool settings
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """
    Initialize database tables.

    Creates all tables defined in the models if they don't exist.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Authentication database tables initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

def reset_database():
    """
    Reset database by dropping and recreating all tables.

    WARNING: This will delete all data!
    Only use in development/testing.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("⚠️ Authentication database reset (all data deleted)")
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        raise

def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection check failed: {e}")
        return False

def get_database_stats() -> Dict[str, Any]:
    """
    Get database connection pool statistics.

    Returns:
        Dictionary with connection pool information
    """
    try:
        pool = engine.pool
        return {
            "pool_size": getattr(pool, "size", "unknown"),
            "checkedin": getattr(pool, "checkedin", "unknown"),
            "checkedout": getattr(pool, "checkedout", "unknown"),
            "overflow": getattr(pool, "overflow", "unknown"),
            "invalid": getattr(pool, "invalid", "unknown")
        }
    except Exception as e:
        return {"error": str(e)}

# Initialize database on module import
try:
    init_database()
except Exception as e:
    print(f"⚠️ Database initialization deferred: {e}")
    print("   Run init_database() manually when database is available")

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_database",
    "reset_database",
    "check_database_connection",
    "get_database_stats"
]