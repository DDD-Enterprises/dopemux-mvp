#!/usr/bin/env python3
"""
Knowledge Graph Authority Middleware
Part of CONPORT-KG-2025 Phase 10

Enforces Two-Plane Architecture authority boundaries:
- PM Plane: Read-only /kg/* access
- Cognitive Plane: Full access
- Blocks unauthorized cross-plane communication
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class KGAuthorityMiddleware(BaseHTTPMiddleware):
    """
    Two-Plane Authority Enforcement

    Validates X-Source-Plane header for KG requests.
    Ensures authority boundaries are respected.
    """

    # Authority matrix for KG endpoints
    AUTHORITY_RULES = {
        "/kg/health": {
            "allowed_planes": ["pm_plane", "cognitive_plane", None],  # Public
            "allowed_methods": ["GET"]
        },
        "/kg/decisions": {
            "allowed_planes": ["pm_plane", "cognitive_plane"],
            "allowed_methods": ["GET"]  # Read-only from PM plane
        },
    }

    async def dispatch(self, request: Request, call_next):
        """
        Middleware to enforce authority boundaries

        Checks:
        1. Is this a KG endpoint?
        2. What plane is making the request?
        3. Is that plane authorized?
        4. Is the HTTP method allowed?
        """

        path = request.url.path

        # Only enforce for /kg/* endpoints
        if not path.startswith("/kg/"):
            return await call_next(request)

        # Get source plane from header
        source_plane = request.headers.get("X-Source-Plane")
        method = request.method

        # Find matching authority rule
        for path_prefix, rules in self.AUTHORITY_RULES.items():
            if path.startswith(path_prefix):
                # Check plane authorization
                allowed_planes = rules["allowed_planes"]
                if allowed_planes and source_plane not in allowed_planes:
                    logger.warning(
                        f"❌ Authority violation: plane={source_plane}, "
                        f"path={path}, allowed={allowed_planes}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Plane '{source_plane}' not authorized for {path}"
                    )

                # Check method authorization
                allowed_methods = rules["allowed_methods"]
                if method not in allowed_methods:
                    logger.warning(
                        f"❌ Method violation: method={method}, "
                        f"path={path}, allowed={allowed_methods}"
                    )
                    raise HTTPException(
                        status_code=405,
                        detail=f"Method '{method}' not allowed for {path}"
                    )

                logger.info(f"✅ KG request authorized: {source_plane} {method} {path}")
                break

        # Request authorized, continue
        response = await call_next(request)
        return response


# Convenience function for adding to FastAPI app
def add_kg_authority_middleware(app):
    """Add KG authority middleware to FastAPI app"""
    app.add_middleware(KGAuthorityMiddleware)
    logger.info("✅ KG Authority Middleware registered")
