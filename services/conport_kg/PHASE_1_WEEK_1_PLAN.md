# Phase 1 Week 1: Core Authentication Implementation

**Week**: 1 of 11
**Phase**: 1 - Authentication & Authorization
**Dates**: 2025-10-23 to 2025-10-27 (5 days)
**Effort**: 40 hours
**Team**: 1 backend developer

---

## Week Overview

**Objective**: Implement secure JWT authentication and password management system

**Deliverables**:
1. JWT token generation and validation (jwt_utils.py - 300 lines)
2. Password hashing with bcrypt + Argon2id (password_utils.py - 250 lines)
3. User data models (models.py - 200 lines)
4. Database schema (auth_schema.sql - 100 lines)
5. User service with CRUD operations (service.py - 400 lines)

**Total Output**: 1,250 lines of production code
**Success Criteria**: Working JWT auth, all password tests passing, user CRUD operational

---

## Day-by-Day Breakdown

### Day 1 (Wednesday): JWT Utilities + Password Security

**Morning (4 hours): JWT Implementation**

**Task 1.1**: Create jwt_utils.py (300 lines)
```python
# services/conport_kg/auth/jwt_utils.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import os

class JWTManager:
    """JWT token creation and validation using RS256"""

    # Token configuration
    ALGORITHM = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 30

    def __init__(self, private_key_path: Optional[str] = None, public_key_path: Optional[str] = None):
        """Initialize JWT manager with RSA keys"""
        self.private_key_path = private_key_path or os.getenv("JWT_PRIVATE_KEY_PATH", "auth/keys/jwt_private.pem")
        self.public_key_path = public_key_path or os.getenv("JWT_PUBLIC_KEY_PATH", "auth/keys/jwt_public.pem")

        # Load or generate keys
        if not os.path.exists(self.private_key_path):
            self._generate_rsa_keys()

        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()

    def _generate_rsa_keys(self):
        """Generate RSA key pair if not exists"""
        # Implementation...

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create short-lived access token (15 minutes)"""
        # Implementation...

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create long-lived refresh token (30 days)"""
        # Implementation...

    def validate_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Validate and decode JWT token"""
        # Implementation...

    # ... additional methods
```

**Acceptance Criteria**:
- [ ] RSA key pair generation working
- [ ] Access token creation with 15min expiry
- [ ] Refresh token creation with 30-day expiry
- [ ] Token validation with signature verification
- [ ] Expired token rejection
- [ ] Invalid token rejection

---

**Afternoon (4 hours): Password Security**

**Task 1.2**: Create password_utils.py (250 lines)
```python
# services/conport_kg/auth/password_utils.py

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import re
from typing import Dict, List
import httpx

class PasswordValidationError(Exception):
    """Password validation errors"""
    pass

class PasswordManager:
    """Secure password hashing with bcrypt + Argon2id hybrid"""

    # Password requirements
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True

    def __init__(self):
        self.argon2 = PasswordHasher(
            time_cost=2,       # Iterations
            memory_cost=65536, # 64 MB
            parallelism=4      # Threads
        )

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt + Argon2id hybrid.

        Strategy: bcrypt for compatibility, Argon2id for modern security
        Format: argon2id${argon2_hash}
        """
        # Validate strength first
        self.validate_password_strength(password)

        # Hash with Argon2id (primary)
        argon2_hash = self.argon2.hash(password)

        return f"argon2id${argon2_hash}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        # Implementation...

    def validate_password_strength(self, password: str) -> None:
        """
        Validate password meets strength requirements.
        Raises PasswordValidationError if weak.
        """
        # Implementation...

    async def check_password_breach(self, password: str) -> bool:
        """
        Check if password in HaveIBeenPwned database.
        Uses k-anonymity (first 5 chars of SHA-1 hash).
        """
        # Implementation...

    def generate_password_reset_token(self, user_id: int) -> str:
        """Generate secure password reset token"""
        # Implementation...
```

**Acceptance Criteria**:
- [ ] Argon2id hashing operational
- [ ] Password verification working
- [ ] Strength validation (12+ chars, complexity requirements)
- [ ] HaveIBeenPwned integration (k-anonymity)
- [ ] Reset token generation
- [ ] All edge cases tested

---

### Day 2 (Thursday): Data Models + Database Schema

**Morning (4 hours): SQLAlchemy Models**

**Task 1.3**: Create models.py (200 lines)
```python
# services/conport_kg/auth/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional, Dict, Any, List

Base = declarative_base()

# SQLAlchemy ORM Models

class User(Base):
    """User account"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspaces = relationship("UserWorkspace", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class UserWorkspace(Base):
    """User workspace membership with roles"""
    __tablename__ = "user_workspaces"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    workspace_id = Column(String(255), primary_key=True)
    role = Column(String(50), default="member")  # owner, admin, member, viewer
    permissions = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="workspaces")

class RefreshToken(Base):
    """JWT refresh tokens"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

class AuditLog(Base):
    """Security audit log"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    details = Column(JSON)
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

# Pydantic schemas (API contracts)

class UserCreate(BaseModel):
    """User creation schema"""
    email: EmailStr
    username: str
    password: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v

class UserResponse(BaseModel):
    """User response schema (no password)"""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# ... additional schemas
```

**Acceptance Criteria**:
- [ ] All 4 SQLAlchemy models created
- [ ] Pydantic schemas for API validation
- [ ] Relationships properly configured
- [ ] Validators for email/username
- [ ] Compatible with PostgreSQL

---

**Afternoon (4 hours): Database Schema**

**Task 1.4**: Create auth_schema.sql (100 lines)
```sql
-- services/conport_kg/auth_schema.sql
-- ConPort-KG 2.0 Authentication Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User workspaces (many-to-many with roles)
CREATE TABLE IF NOT EXISTS user_workspaces (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workspace_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, workspace_id)
);

-- Refresh tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_workspaces_user_id ON user_workspaces(user_id);
CREATE INDEX IF NOT EXISTS idx_user_workspaces_workspace_id ON user_workspaces(workspace_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Task 1.5**: Create database.py (150 lines)
```python
# services/conport_kg/auth/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from typing import Generator

from .models import Base

# Database configuration
DATABASE_URL = os.getenv(
    "CONPORT_DATABASE_URL",
    "postgresql://user:password@localhost:5455/dopemux_knowledge_graph"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    echo=False  # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database schema"""
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Database session context manager.

    Usage:
        with get_db() as db:
            user = db.query(User).first()
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

# FastAPI dependency
def get_db_dependency():
    """FastAPI dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Acceptance Criteria**:
- [ ] JWT utilities complete with RS256
- [ ] Password manager with Argon2id + bcrypt
- [ ] SQLAlchemy models defined
- [ ] Database schema SQL created
- [ ] Database connection utilities working
- [ ] Unit tests written for JWT and password functions
- [ ] All tests passing

---

### Day 2 (Thursday): User Service Implementation

**Full Day (8 hours): User CRUD + Auth Service**

**Task 1.6**: Create service.py (400 lines)
```python
# services/conport_kg/auth/service.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import hashlib

from .models import User, UserWorkspace, RefreshToken, AuditLog, UserCreate, UserResponse
from .jwt_utils import JWTManager
from .password_utils import PasswordManager, PasswordValidationError

class AuthenticationError(Exception):
    """Authentication failures"""
    pass

class AuthorizationError(Exception):
    """Authorization failures"""
    pass

class UserService:
    """User management and authentication service"""

    def __init__(self):
        self.jwt_manager = JWTManager()
        self.password_manager = PasswordManager()

    async def create_user(self, db: Session, user_data: UserCreate) -> User:
        """
        Create new user account.

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            Created user object

        Raises:
            HTTPException: If user creation fails
        """
        try:
            # Validate password strength
            self.password_manager.validate_password_strength(user_data.password)

            # Check for breached password
            is_breached = await self.password_manager.check_password_breach(user_data.password)
            if is_breached:
                raise PasswordValidationError("Password found in breach database")

            # Hash password
            password_hash = self.password_manager.hash_password(user_data.password)

            # Create user
            user = User(
                email=user_data.email,
                username=user_data.username,
                password_hash=password_hash
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            # Audit log
            self._log_audit(db, user.id, "user.created", details={"email": user.email})

            return user

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        except PasswordValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def authenticate_user(self, db: Session, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return JWT tokens.

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "token_type": "bearer",
                "user": UserResponse
            }
        """
        # Get user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise AuthenticationError("Invalid credentials")

        # Check if active
        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # Verify password
        if not self.password_manager.verify_password(password, user.password_hash):
            self._log_audit(db, user.id, "login.failed", details={"reason": "invalid_password"})
            raise AuthenticationError("Invalid credentials")

        # Create tokens
        access_token = self.jwt_manager.create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "username": user.username
        })

        refresh_token = self.jwt_manager.create_refresh_token({
            "sub": str(user.id)
        })

        # Store refresh token (hashed)
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(refresh_token_obj)
        db.commit()

        # Audit log
        self._log_audit(db, user.id, "login.success")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }

    async def refresh_access_token(self, db: Session, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        # Implementation...

    async def logout_user(self, db: Session, refresh_token: str) -> None:
        """Revoke refresh token (logout)"""
        # Implementation...

    # Workspace management methods
    async def add_user_to_workspace(
        self,
        db: Session,
        user_id: int,
        workspace_id: str,
        role: str = "member"
    ) -> UserWorkspace:
        """Add user to workspace with role"""
        # Implementation...

    async def remove_user_from_workspace(
        self,
        db: Session,
        user_id: int,
        workspace_id: str
    ) -> None:
        """Remove user from workspace"""
        # Implementation...

    async def get_user_workspaces(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get all workspaces for user"""
        # Implementation...

    async def check_workspace_permission(
        self,
        db: Session,
        user_id: int,
        workspace_id: str,
        required_permission: str
    ) -> bool:
        """Check if user has permission in workspace"""
        # Implementation...

    # Helper methods
    def _log_audit(
        self,
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log security event to audit log"""
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit)
        db.commit()
```

**Acceptance Criteria**:
- [ ] User creation with validation
- [ ] User authentication returning JWT
- [ ] Refresh token flow working
- [ ] Logout (token revocation)
- [ ] Workspace membership management
- [ ] Permission checking
- [ ] Audit logging all auth events

---

**Evening (2 hours): Database Setup**

**Task 1.7**: Initialize database and run migrations
```bash
# Create database (if doesn't exist)
createdb dopemux_knowledge_graph

# Run schema
psql dopemux_knowledge_graph < services/conport_kg/auth_schema.sql

# Verify tables created
psql dopemux_knowledge_graph -c "\dt"
```

**Task 1.8**: Create init script (init_db.py - 50 lines)
```python
# services/conport_kg/init_db.py

from auth.database import engine, init_database
from auth.models import Base

def initialize():
    """Initialize all database tables"""
    print("Creating database schema...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database schema created")

if __name__ == "__main__":
    initialize()
```

**Acceptance Criteria**:
- [ ] Database schema applied successfully
- [ ] All tables exist with proper indexes
- [ ] Init script runs without errors
- [ ] Can query tables via psql

---

### Day 3 (Friday): Testing Infrastructure + Unit Tests

**Morning (4 hours): Test Infrastructure**

**Task 1.9**: Create tests/conftest.py (300 lines)
```python
# services/conport_kg/tests/conftest.py

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from datetime import datetime, timedelta
from typing import Dict, Any

from auth.models import Base, User, UserWorkspace
from auth.database import get_db
from auth.jwt_utils import JWTManager
from auth.password_utils import PasswordManager

# Test database configuration
@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL container for testing"""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def test_database_url(postgres_container):
    """Database URL for tests"""
    return postgres_container.get_connection_url()

@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Test database engine"""
    engine = create_engine(test_database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db(test_engine):
    """Test database session"""
    TestSessionLocal = sessionmaker(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def jwt_manager():
    """JWT manager for testing"""
    return JWTManager()

@pytest.fixture
def password_manager():
    """Password manager for testing"""
    return PasswordManager()

@pytest.fixture
def mock_user_data() -> Dict[str, Any]:
    """Mock user data for testing"""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!@#",
        "is_active": True,
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def created_user(test_db, password_manager):
    """Create a test user in database"""
    password_hash = password_manager.hash_password("SecurePass123!@#")
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def auth_tokens(jwt_manager, created_user):
    """Generate auth tokens for test user"""
    access_token = jwt_manager.create_access_token({
        "sub": str(created_user.id),
        "email": created_user.email,
        "username": created_user.username
    })
    refresh_token = jwt_manager.create_refresh_token({
        "sub": str(created_user.id)
    })
    return {
        "access": access_token,
        "refresh": refresh_token
    }
```

**Acceptance Criteria**:
- [ ] Testcontainers setup for isolated testing
- [ ] Database fixtures for each test
- [ ] User creation fixtures
- [ ] JWT token fixtures
- [ ] Mock data generators

---

**Afternoon (4 hours): Unit Tests**

**Task 1.10**: Create tests/unit/test_jwt_utils.py (200 lines)
```python
# services/conport_kg/tests/unit/test_jwt_utils.py

import pytest
from datetime import datetime, timedelta
from jose import JWTError

from auth.jwt_utils import JWTManager

class TestJWTTokenCreation:
    """Test JWT token creation"""

    def test_create_access_token_valid_payload(self, jwt_manager):
        """Test creating access token with valid user data"""
        payload = {"sub": "123", "email": "test@example.com"}
        token = jwt_manager.create_access_token(payload)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_includes_required_claims(self, jwt_manager):
        """Test access token includes exp, iat, type"""
        token = jwt_manager.create_access_token({"sub": "123"})
        decoded = jwt_manager.validate_token(token, "access")

        assert "exp" in decoded
        assert "iat" in decoded
        assert "type" in decoded
        assert decoded["type"] == "access"

    def test_create_refresh_token_longer_expiration(self, jwt_manager):
        """Test refresh token has longer expiry than access"""
        access = jwt_manager.create_access_token({"sub": "123"})
        refresh = jwt_manager.create_refresh_token({"sub": "123"})

        access_decoded = jwt_manager.validate_token(access, "access")
        refresh_decoded = jwt_manager.validate_token(refresh, "refresh")

        access_exp = datetime.fromtimestamp(access_decoded["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_decoded["exp"])

        assert refresh_exp > access_exp

class TestJWTTokenValidation:
    """Test JWT token validation"""

    def test_validate_token_valid_access_token(self, jwt_manager):
        """Test validating valid access token"""
        payload = {"sub": "123", "email": "test@example.com"}
        token = jwt_manager.create_access_token(payload)

        decoded = jwt_manager.validate_token(token, "access")
        assert decoded["sub"] == "123"
        assert decoded["email"] == "test@example.com"

    def test_validate_token_expired_token(self, jwt_manager):
        """Test that expired tokens are rejected"""
        # Create token that expires immediately
        payload = {"sub": "123", "exp": datetime.utcnow() - timedelta(minutes=1)}
        # ... implementation

    def test_validate_token_invalid_signature(self, jwt_manager):
        """Test that tokens with invalid signatures are rejected"""
        # ... implementation

    # ... 10 more tests
```

**Task 1.11**: Create tests/unit/test_password_utils.py (200 lines)
```python
# services/conport_kg/tests/unit/test_password_utils.py

import pytest
from auth.password_utils import PasswordManager, PasswordValidationError

class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_hash_password_creates_valid_hash(self, password_manager):
        """Test that password hashing produces valid Argon2id hash"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert hashed.startswith("argon2id$")
        assert len(hashed) > 50

    def test_verify_password_correct_password(self, password_manager):
        """Test that correct password verifies successfully"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert password_manager.verify_password(password, hashed) is True

    def test_verify_password_wrong_password(self, password_manager):
        """Test that wrong password is rejected"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert password_manager.verify_password("WrongPassword", hashed) is False

    # ... 12 more tests

class TestPasswordValidation:
    """Test password strength validation"""

    def test_validate_password_too_short(self, password_manager):
        """Test that short passwords are rejected"""
        with pytest.raises(PasswordValidationError):
            password_manager.validate_password_strength("Short1!")

    def test_validate_password_no_uppercase(self, password_manager):
        """Test that passwords without uppercase are rejected"""
        with pytest.raises(PasswordValidationError):
            password_manager.validate_password_strength("longpassword123!")

    # ... 8 more tests
```

**Acceptance Criteria**:
- [ ] 40+ unit tests created
- [ ] JWT creation tests (10 tests)
- [ ] JWT validation tests (10 tests)
- [ ] Password hashing tests (10 tests)
- [ ] Password validation tests (10 tests)
- [ ] All tests passing
- [ ] Coverage >80% for auth module

---

### Day 4 (Monday): Integration Tests + API Endpoints

**Morning (4 hours): Integration Tests**

**Task 1.12**: Create tests/integration/test_user_service.py (300 lines)
```python
# services/conport_kg/tests/integration/test_user_service.py

import pytest
from datetime import datetime, timedelta

from auth.service import UserService, AuthenticationError
from auth.models import UserCreate

class TestUserCreation:
    """Test user creation flow"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_db):
        """Test successful user creation"""
        service = UserService()
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="SecurePass123!@#"
        )

        user = await service.create_user(test_db, user_data)

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, test_db, created_user):
        """Test that duplicate email is rejected"""
        service = UserService()
        user_data = UserCreate(
            email=created_user.email,  # Duplicate
            username="different",
            password="SecurePass123!@#"
        )

        with pytest.raises(HTTPException) as exc:
            await service.create_user(test_db, user_data)

        assert exc.value.status_code == 400

    # ... 15 more tests

class TestAuthentication:
    """Test authentication flow"""

    @pytest.mark.asyncio
    async def test_authenticate_valid_credentials(self, test_db, created_user):
        """Test authentication with valid credentials"""
        service = UserService()

        result = await service.authenticate_user(
            test_db,
            email=created_user.email,
            password="SecurePass123!@#"
        )

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["user"].id == created_user.id

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self, test_db, created_user):
        """Test authentication with wrong password"""
        service = UserService()

        with pytest.raises(AuthenticationError):
            await service.authenticate_user(
                test_db,
                email=created_user.email,
                password="WrongPassword"
            )

    # ... 15 more tests
```

**Acceptance Criteria**:
- [ ] 30+ integration tests
- [ ] Full authentication flow tested
- [ ] User creation edge cases covered
- [ ] Workspace membership tested
- [ ] Audit logging verified
- [ ] All tests passing

---

**Afternoon (4 hours): FastAPI Endpoints**

**Task 1.13**: Create api/auth_routes.py (400 lines)
```python
# services/conport_kg/api/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from auth.database import get_db_dependency
from auth.service import UserService, AuthenticationError, AuthorizationError
from auth.models import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
user_service = UserService()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db_dependency)
):
    """
    Register a new user account.

    - **email**: Valid email address (unique)
    - **username**: Alphanumeric username (unique)
    - **password**: Minimum 12 characters with complexity requirements
    """
    try:
        user = await user_service.create_user(db, user_data)
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )

@router.post("/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Authenticate user and receive JWT tokens.

    Returns access token (15min) and refresh token (30 days).
    """
    try:
        result = await user_service.authenticate_user(db, email, password)
        return result
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db_dependency)
):
    """Refresh access token using refresh token"""
    # Implementation...

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_dependency)
):
    """Logout user (revoke refresh token)"""
    # Implementation...

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_dependency)
):
    """Get current authenticated user"""
    # Implementation...

@router.get("/workspaces")
async def get_my_workspaces(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_dependency)
):
    """Get all workspaces for authenticated user"""
    # Implementation...

# ... additional endpoints
```

**Acceptance Criteria**:
- [ ] All 6+ auth endpoints implemented
- [ ] OpenAPI documentation generated
- [ ] Request/response validation via Pydantic
- [ ] Error handling with proper HTTP status codes
- [ ] Bearer token authentication working

---

**Afternoon (4 hours): API Tests + Documentation**

**Task 1.14**: Create tests/api/test_auth_endpoints.py (250 lines)
```python
# services/conport_kg/tests/api/test_auth_endpoints.py

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestRegistrationEndpoint:
    """Test /auth/register endpoint"""

    def test_register_success(self):
        """Test successful user registration"""
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!@#"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "password" not in data  # Password not in response

    def test_register_duplicate_email(self, created_user):
        """Test registration with duplicate email fails"""
        response = client.post("/auth/register", json={
            "email": created_user.email,
            "username": "different",
            "password": "SecurePass123!@#"
        })

        assert response.status_code == 400

    # ... 10 more tests

class TestLoginEndpoint:
    """Test /auth/login endpoint"""

    def test_login_success(self, created_user):
        """Test successful login"""
        response = client.post("/auth/login", json={
            "email": created_user.email,
            "password": "SecurePass123!@#"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    # ... 10 more tests
```

**Task 1.15**: Create API documentation (README.md - 200 lines)
```markdown
# ConPort-KG Authentication API

## Endpoints

### POST /auth/register
Create a new user account.

**Request**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePass123!@#"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "created_at": "2025-10-23T..."
}
```

### POST /auth/login
Authenticate and receive JWT tokens.

... (complete API reference)
```

**Acceptance Criteria**:
- [ ] 25+ API endpoint tests
- [ ] Full request/response coverage
- [ ] Error case testing
- [ ] API documentation complete
- [ ] Postman collection created

---

### Day 5 (Tuesday): Polish + Week 1 Validation

**Morning (4 hours): Security Hardening**

**Task 1.16**: Add security middleware (middleware/security.py - 200 lines)
```python
# services/conport_kg/middleware/security.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import re

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting (enhanced in Phase 3)"""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In-memory for now, Redis in Phase 3

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host

        # Track requests
        now = datetime.utcnow()
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if (now - req_time).total_seconds() < self.window_seconds
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds}s"
            )

        # Record request
        self.requests[client_ip].append(now)

        response = await call_next(request)
        return response
```

**Acceptance Criteria**:
- [ ] Security headers middleware
- [ ] Basic rate limiting (enhanced in Phase 3)
- [ ] CORS configuration
- [ ] Input sanitization helpers
- [ ] Security tests passing

---

**Afternoon (4 hours): Week 1 Validation**

**Task 1.17**: End-to-end authentication flow test
```bash
# Test complete auth flow
pytest tests/ -v --cov=auth --cov-report=term-missing

# Expected:
# - 70+ tests passing
# - Coverage >80%
# - All security tests green
```

**Task 1.18**: Manual testing checklist
```markdown
Manual Testing Checklist - Week 1:

[ ] Register new user via API
[ ] Login with valid credentials
[ ] Login with invalid credentials (should fail)
[ ] Access protected endpoint with valid token
[ ] Access protected endpoint with expired token (should fail)
[ ] Refresh access token
[ ] Logout (revoke token)
[ ] Try using revoked token (should fail)
[ ] Check audit logs populated
[ ] Verify password hashing (can't reverse)
[ ] Test password breach detection
[ ] Verify JWT signature validation
```

**Task 1.19**: Week 1 retrospective + planning
- Document what worked/what didn't
- Adjust Week 2 estimates if needed
- Log decision about any architecture changes
- Prepare for PostgreSQL RLS implementation

**Acceptance Criteria**:
- [ ] All 70+ tests passing
- [ ] Coverage >80%
- [ ] Manual testing complete
- [ ] No critical security issues
- [ ] Ready for Week 2 (RLS implementation)

---

## Week 1 Success Criteria

### Code Metrics
- [x] 1,250 lines of production code
- [ ] 750 lines of test code
- [ ] 70+ tests passing
- [ ] Coverage >80%
- [ ] Zero critical bugs

### Functional Requirements
- [ ] User registration working
- [ ] Login returning JWT tokens
- [ ] Token validation operational
- [ ] Refresh token flow working
- [ ] Password security (Argon2id + breach checking)
- [ ] Audit logging all auth events

### Security Requirements
- [ ] JWT signatures validated (RS256)
- [ ] Passwords never stored plaintext
- [ ] Breach detection prevents compromised passwords
- [ ] Tokens expire appropriately (15min access, 30d refresh)
- [ ] Revoked tokens cannot be used
- [ ] All security tests passing

### Documentation
- [ ] API reference complete
- [ ] Code comments comprehensive
- [ ] Testing guide written
- [ ] Week 1 summary document

---

## Risk Mitigation

### Risk 1: Crypto Key Generation Issues
**Likelihood**: Low
**Mitigation**: Use cryptography library (battle-tested), test key generation thoroughly
**Contingency**: Provide manual key generation instructions

### Risk 2: Password Hashing Performance
**Likelihood**: Low
**Mitigation**: Benchmark Argon2id with realistic parameters, adjust if too slow
**Contingency**: Reduce time_cost parameter if needed (security/performance trade-off)

### Risk 3: Test Infrastructure Setup
**Likelihood**: Medium
**Mitigation**: Use testcontainers (proven pattern), allocate extra time Day 3
**Contingency**: Use Docker Compose for tests if testcontainers fails

---

## Daily Standup Format

**Each morning, review**:
1. Yesterday's accomplishments
2. Today's plan (specific tasks)
3. Any blockers
4. Estimated hours remaining

**Each evening, log**:
1. Tasks completed
2. Tests passing count
3. Lines of code written
4. Issues encountered
5. Tomorrow's priorities

---

## Week 1 Deliverable Checklist

### Files to Create (10 files)
- [ ] auth/jwt_utils.py (300 lines)
- [ ] auth/password_utils.py (250 lines)
- [ ] auth/models.py (200 lines)
- [ ] auth/database.py (150 lines)
- [ ] auth/service.py (400 lines)
- [ ] auth_schema.sql (100 lines)
- [ ] tests/conftest.py (300 lines)
- [ ] tests/unit/test_jwt_utils.py (200 lines)
- [ ] tests/unit/test_password_utils.py (200 lines)
- [ ] tests/integration/test_user_service.py (300 lines)

### Additional Files
- [ ] tests/api/test_auth_endpoints.py (250 lines)
- [ ] api/auth_routes.py (400 lines)
- [ ] middleware/security.py (200 lines)
- [ ] init_db.py (50 lines)
- [ ] auth/README.md (200 lines)

**Total**: 15 files, 3,500 lines

---

## Next Steps After Week 1

**Week 2 Preview** (PostgreSQL RLS + Query Refactoring):
- Implement RLS policies on all AGE tables
- Refactor all 12 query methods for workspace isolation
- Add RBAC middleware
- Test cross-workspace isolation (100+ test cases)
- Performance regression testing

**Week 2 Output**: Secure multi-tenant system (security score 7/10)

---

**Phase 1 Week 1 Plan Created**
**Status**: Ready to start Day 1 (JWT + Password implementation)
**First Task**: Create auth/jwt_utils.py (300 lines)

Should I start implementing Day 1 tasks now?
