#!/usr/bin/env python3
"""
ConPort-KG Test Configuration
Phase 1 Week 1 Day 3

Pytest fixtures and configuration for all tests.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure auth package is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.models import Base, User, UserWorkspace
from auth.jwt_utils import JWTManager
from auth.password_utils import PasswordManager
from auth.service import UserService


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def test_database_url():
    """
    Test database URL.

    Uses in-memory SQLite for fast testing.
    For integration tests, use PostgreSQL.
    """
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Test database engine"""
    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_engine) -> Generator[Session, None, None]:
    """
    Test database session.

    Each test gets a fresh session with transaction rollback for isolation.
    """
    # Create connection
    connection = test_engine.connect()

    # Begin transaction
    transaction = connection.begin()

    # Create session bound to this connection
    TestSessionLocal = sessionmaker(bind=connection)
    session = TestSessionLocal()

    yield session

    # Rollback transaction (undoes all changes)
    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# Service Fixtures
# ============================================================================


@pytest.fixture
def jwt_manager(tmp_path):
    """JWT manager with temporary keys"""
    key_dir = tmp_path / "keys"
    key_dir.mkdir()

    return JWTManager(
        private_key_path=str(key_dir / "test_private.pem"),
        public_key_path=str(key_dir / "test_public.pem"),
    )


@pytest.fixture
def password_manager():
    """Password manager for testing"""
    return PasswordManager()


@pytest.fixture
def user_service():
    """UserService instance for testing"""
    return UserService()


# ============================================================================
# Data Fixtures
# ============================================================================


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "MyUn1que!Test#Pass2025$ConPort",  # Unique password not in HIBP
    }


@pytest.fixture
def sample_user_create(sample_user_data):
    """Sample UserCreate schema"""
    from auth.models import UserCreate

    return UserCreate(**sample_user_data)


@pytest.fixture
def created_test_user(test_db: Session, password_manager: PasswordManager) -> User:
    """
    Create a test user in database.

    Returns persisted User object ready for testing.
    """
    password_hash = password_manager.hash_password("MyUn1que!Test#Pass2025$ConPort")

    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash,
        is_active=True,
    )

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def created_test_user_with_workspace(
    test_db: Session, created_test_user: User
) -> tuple[User, UserWorkspace]:
    """
    Create test user with workspace membership.

    Returns tuple of (User, UserWorkspace).
    """
    workspace = UserWorkspace(
        user_id=created_test_user.id,
        workspace_id="/Users/hue/code/test-project",
        role="member",
        permissions={
            "read_decisions": True,
            "write_decisions": True,
            "delete_decisions": False,
        },
    )

    test_db.add(workspace)
    test_db.commit()
    test_db.refresh(workspace)

    return created_test_user, workspace


@pytest.fixture
def admin_user(test_db: Session, password_manager: PasswordManager) -> User:
    """Create admin user for authorization testing"""
    password_hash = password_manager.hash_password("Adm1nUn1que!Pass#2025$ConPort")

    user = User(
        email="admin@example.com",
        username="adminuser123",
        password_hash=password_hash,
        is_active=True,
    )

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Add to workspace as admin
    workspace = UserWorkspace(
        user_id=user.id,
        workspace_id="/Users/hue/code/test-project",
        role="admin",
        permissions={"manage_users": True, "write_decisions": True},
    )

    test_db.add(workspace)
    test_db.commit()

    return user


@pytest.fixture
def auth_tokens(jwt_manager: JWTManager, created_test_user: User):
    """Generate valid auth tokens for test user"""
    access_token = jwt_manager.create_access_token({
        "sub": str(created_test_user.id),
        "email": created_test_user.email,
        "username": created_test_user.username,
    })

    refresh_token = jwt_manager.create_refresh_token({
        "sub": str(created_test_user.id)
    })

    return {
        "access": access_token,
        "refresh": refresh_token,
    }


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no database)")
    config.addinivalue_line("markers", "integration: Integration tests (database required)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
