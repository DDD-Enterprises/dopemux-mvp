"""
API Key Authentication Middleware for Task Orchestrator

Secures all API endpoints with API key validation using X-API-Key header.
Follows same security patterns as ADHD Engine for consistency.

Security features:
- API key validation via X-API-Key header
- Environment-based configuration (TASK_ORCHESTRATOR_API_KEY)
- Development mode bypass (no key required)
- Proper HTTP error responses (401/403)
- CORS header allowance for X-API-Key
"""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Load API key from environment
EXPECTED_API_KEY = os.getenv("TASK_ORCHESTRATOR_API_KEY")


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify API key from request header.

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If no API key configured in environment, skip auth (development mode)
    if not EXPECTED_API_KEY:
        return None

    # Check if API key provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key
    if api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
        )

    return api_key
