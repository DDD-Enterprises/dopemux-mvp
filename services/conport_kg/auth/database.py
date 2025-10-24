#!/usr/bin/env python3
"""
ConPort-KG Database Utilities
Phase 1 Week 1 Day 2

SQLAlchemy database connection, session management, and initialization.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .models import Base

# ============================================================================
# Database Configuration
# ============================================================================

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "CONPORT_DATABASE_URL",
    "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph",
)

# ============================================================================
# SQLAlchemy Engine with Connection Pooling
# ============================================================================

# Create engine with optimized connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Minimum connections in pool
    max_overflow=10,  # Maximum extra connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before use (handles stale connections)
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for SQL query logging (debugging)
    future=True,  # Use SQLAlchemy 2.0 style
)

# ============================================================================
# Session Factory
# ============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Don't expire objects after commit
)

# ============================================================================
# Database Initialization
# ============================================================================


def init_database() -> None:
    """
    Initialize database schema.

    Creates all tables defined in models if they don't exist.
    Safe to call multiple times (idempotent).

    Usage:
        from auth.database import init_database
        init_database()  # Creates all tables
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """
    Drop all database tables.

    WARNING: Destructive operation! Only use for testing or development.

    Usage:
        from auth.database import drop_all_tables
        drop_all_tables()  # Drops ALL tables
    """
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# Session Context Managers
# ============================================================================


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Database session context manager.

    Automatically commits on success, rolls back on error, and closes session.

    Usage:
        from auth.database import get_db

        with get_db() as db:
            user = db.query(User).filter(User.email == "test@example.com").first()
            # Changes committed automatically when context exits
            # Rolled back automatically if exception raised
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_dependency() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Provides database session to FastAPI route handlers.
    Automatically handles commit/rollback/close.

    Usage:
        from fastapi import Depends
        from auth.database import get_db_dependency

        @app.get("/users")
        def get_users(db: Session = Depends(get_db_dependency)):
            users = db.query(User).all()
            return users
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Health Check
# ============================================================================


def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection successful, False otherwise

    Usage:
        from auth.database import check_database_connection

        if check_database_connection():
            print("Database connected ✓")
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


# ============================================================================
# Migration Helpers
# ============================================================================


def get_table_names() -> list[str]:
    """
    Get list of all table names in database.

    Returns:
        List of table names

    Usage:
        tables = get_table_names()
        print(f"Tables: {tables}")
    """
    from sqlalchemy import inspect

    inspector = inspect(engine)
    return inspector.get_table_names()


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in database.

    Args:
        table_name: Name of table to check

    Returns:
        True if table exists, False otherwise

    Usage:
        if not table_exists("users"):
            init_database()  # Create tables
    """
    return table_name in get_table_names()
