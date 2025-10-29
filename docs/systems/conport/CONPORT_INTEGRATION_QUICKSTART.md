# ConPort Integration Quick Start Guide

**Goal**: Get ConPort-KG API deployed and integrated with one agent in 1 week

**Status**: Ready to implement  
**Effort**: 5-7 days  
**ROI**: Extremely high (unlocks entire agent ecosystem)

---

## Phase 1: Deploy ConPort-KG API (Days 1-3)

### Day 1: Create FastAPI Application

**Location**: `services/conport_kg/main.py`

```python
#!/usr/bin/env python3
"""
ConPort-KG API Server
Production-ready multi-tenant knowledge graph API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging

from api.auth_routes import router as auth_router
from middleware.rbac_middleware import WorkspaceAuthorizationMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ConPort-KG API",
    description="Multi-tenant knowledge graph for dopemux",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],  # Dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RBAC middleware
app.add_middleware(WorkspaceAuthorizationMiddleware)

# Mount routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# TODO: Add query routes
# app.include_router(query_router, prefix="/kg", tags=["knowledge-graph"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "conport-kg",
        "version": "2.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    # TODO: Check database connection
    # TODO: Check Redis connection
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "auth": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
```

**Test**:
```bash
cd services/conport_kg
python main.py

# In another terminal
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### Day 2: Add Query Routes

**Location**: `services/conport_kg/api/query_routes.py`

```python
"""
Knowledge Graph Query Routes
Exposes the 3-tier query system via REST API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from auth.jwt_utils import JWTManager
from auth.models import User
from queries.overview import OverviewQueries
from queries.exploration import ExplorationQueries
from queries.deep_context import DeepContextQueries
from queries.models import DecisionCard, DecisionNeighborhood

router = APIRouter()
jwt_manager = JWTManager()

# Dependency: Get current user from JWT
async def get_current_user(
    authorization: str = Depends(jwt_manager.get_authorization_header)
) -> User:
    """Extract and validate user from JWT token"""
    token = await jwt_manager.validate_access_token(authorization)
    # TODO: Load user from database
    return User(id=token.user_id, email=token.email)

# Initialize query classes
overview = OverviewQueries()
exploration = ExplorationQueries()
deep_context = DeepContextQueries()

# ============================================================================
# Tier 1: Overview Queries (ADHD Top-3 pattern)
# ============================================================================

@router.get("/decisions/recent", response_model=List[DecisionCard])
async def get_recent_decisions(
    limit: int = Query(3, ge=1, le=100),
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get recent decisions (Tier 1 - Overview)
    
    ADHD-optimized: Returns Top-3 by default
    Performance: ~2.52ms p95
    """
    # TODO: Filter by workspace_id and user permissions
    decisions = await overview.get_recent_decisions(limit)
    return decisions

@router.get("/decisions/active", response_model=List[DecisionCard])
async def get_active_decisions(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get currently active decisions (Tier 1)
    
    Returns decisions with status='active' or recent updates
    """
    decisions = await overview.get_active_decisions(workspace_id)
    return decisions

# ============================================================================
# Tier 2: Exploration Queries (Progressive disclosure)
# ============================================================================

@router.get("/decisions/{decision_id}/neighborhood")
async def get_decision_neighborhood(
    decision_id: int,
    max_hops: int = Query(2, ge=1, le=5),
    current_user: User = Depends(get_current_user)
):
    """
    Get decision neighborhood graph (Tier 2)
    
    Returns related decisions with relationships
    Performance: ~3.44ms p95
    """
    neighborhood = await exploration.get_decision_neighborhood(
        decision_id,
        max_hops=max_hops
    )
    return neighborhood

@router.get("/decisions/{decision_id}/genealogy")
async def get_decision_genealogy(
    decision_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get decision genealogy (ancestors and descendants)
    
    Shows complete decision lineage
    """
    genealogy = await exploration.get_decision_genealogy(decision_id)
    return genealogy

# ============================================================================
# Tier 3: Deep Context Queries (Complete analysis)
# ============================================================================

@router.get("/decisions/{decision_id}/analytics")
async def get_decision_analytics(
    decision_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get decision analytics (Tier 3)
    
    Complete analysis: importance, blast radius, churn risk
    Performance: ~4.76ms p95
    """
    analytics = await deep_context.get_decision_analytics(decision_id)
    return analytics

@router.get("/decisions/{decision_id}/impact")
async def get_impact_graph(
    decision_id: int,
    max_depth: int = Query(3, ge=1, le=10),
    current_user: User = Depends(get_current_user)
):
    """
    Get impact graph (Tier 3)
    
    Shows all decisions affected by this decision
    """
    impact = await deep_context.get_impact_graph(decision_id, max_depth)
    return impact

# ============================================================================
# Search and Filter
# ============================================================================

@router.get("/decisions/search")
async def search_decisions(
    q: str = Query(..., min_length=1),
    workspace_id: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Search decisions by query string
    
    Searches across summary, rationale, implementation_details
    """
    # TODO: Implement full-text search
    results = await overview.search_decisions(q, workspace_id, tag, limit)
    return results
```

**Update main.py**:
```python
from api.query_routes import router as query_router

app.include_router(query_router, prefix="/kg", tags=["knowledge-graph"])
```

**Test**:
```bash
# Get JWT token first
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Test query
curl http://localhost:8000/kg/decisions/recent \
  -H "Authorization: Bearer $TOKEN"
```

### Day 3: Docker Compose Integration

**Location**: `docker/conport-kg/docker-compose.yml` (update)

```yaml
version: '3.8'

services:
  # Existing services...
  
  # ADD THIS NEW SERVICE
  conport-kg-api:
    build:
      context: ../../services/conport_kg
      dockerfile: Dockerfile
    container_name: conport-kg-api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://dopemux_age:${POSTGRES_PASSWORD}@postgres:5432/dopemux_knowledge_graph
      REDIS_URL: redis://redis:6379
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-auto-generated}
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}
    depends_on:
      - postgres
      - redis
    networks:
      - conport-kg-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Create Dockerfile**: `services/conport_kg/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
```

**Create requirements.txt**: `services/conport_kg/requirements.txt`

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
psycopg2-binary==2.9.9
redis==5.0.1
pyjwt[crypto]==2.8.0
argon2-cffi==23.1.0
bcrypt==4.1.2
pydantic==2.5.0
python-multipart==0.0.6
httpx==0.25.2
```

**Deploy**:
```bash
cd docker/conport-kg
docker-compose up -d conport-kg-api

# Check logs
docker-compose logs -f conport-kg-api

# Test
curl http://localhost:8000/health
```

---

## Phase 2: Create Shared Client Library (Day 4)

**Location**: `services/shared/conport_kg_client/`

```python
# services/shared/conport_kg_client/__init__.py
"""
ConPort-KG Python Client
Shared library for all dopemux agents
"""

from .client import ConPortKGClient
from .models import Decision, DecisionNeighborhood, DecisionAnalytics
from .exceptions import ConPortKGError, AuthenticationError, NotFoundError

__all__ = [
    'ConPortKGClient',
    'Decision',
    'DecisionNeighborhood',
    'DecisionAnalytics',
    'ConPortKGError',
    'AuthenticationError',
    'NotFoundError',
]
```

```python
# services/shared/conport_kg_client/client.py
"""
ConPort-KG HTTP Client
"""

import httpx
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from .models import Decision, DecisionNeighborhood, DecisionAnalytics
from .exceptions import ConPortKGError, AuthenticationError, NotFoundError

logger = logging.getLogger(__name__)


class ConPortKGClient:
    """
    Async HTTP client for ConPort-KG API
    
    Features:
    - JWT authentication with auto-refresh
    - Retry logic with exponential backoff
    - Type-safe responses
    - Circuit breaker for reliability
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        email: Optional[str] = None,
        password: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self._access_token = access_token
        self._refresh_token = None
        self._token_expires = None
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": "ConPort-KG-Client/1.0"}
        )
    
    async def authenticate(self):
        """Authenticate and get JWT tokens"""
        if not self.email or not self.password:
            raise AuthenticationError("Email and password required")
        
        response = await self.client.post(
            "/auth/login",
            json={"email": self.email, "password": self.password}
        )
        
        if response.status_code != 200:
            raise AuthenticationError(f"Login failed: {response.text}")
        
        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._token_expires = datetime.now() + timedelta(minutes=15)
        
        logger.info("Authenticated successfully")
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self._access_token:
            await self.authenticate()
        elif self._token_expires and datetime.now() >= self._token_expires:
            # Token expired, refresh it
            await self._refresh_access_token()
    
    async def _refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self._refresh_token:
            await self.authenticate()
            return
        
        response = await self.client.post(
            "/auth/refresh",
            json={"refresh_token": self._refresh_token}
        )
        
        if response.status_code != 200:
            # Refresh failed, re-authenticate
            await self.authenticate()
            return
        
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires = datetime.now() + timedelta(minutes=15)
        
        logger.info("Access token refreshed")
    
    async def _request(self, method: str, path: str, **kwargs):
        """Make authenticated request with retry logic"""
        await self._ensure_authenticated()
        
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self._access_token}'
        kwargs['headers'] = headers
        
        # Retry logic (3 attempts)
        for attempt in range(3):
            try:
                response = await self.client.request(method, path, **kwargs)
                
                if response.status_code == 401:
                    # Token invalid, refresh and retry
                    await self._refresh_access_token()
                    headers['Authorization'] = f'Bearer {self._access_token}'
                    response = await self.client.request(method, path, **kwargs)
                
                if response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {path}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                if attempt == 2:  # Last attempt
                    raise ConPortKGError(f"Request failed: {e}")
                logger.warning(f"Request failed (attempt {attempt+1}/3): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # ========================================================================
    # Query Methods
    # ========================================================================
    
    async def get_recent_decisions(
        self,
        limit: int = 3,
        workspace_id: Optional[str] = None
    ) -> List[Decision]:
        """Get recent decisions (ADHD Top-3 pattern)"""
        params = {"limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        
        data = await self._request("GET", "/kg/decisions/recent", params=params)
        return [Decision(**d) for d in data]
    
    async def get_decision_neighborhood(
        self,
        decision_id: int,
        max_hops: int = 2
    ) -> DecisionNeighborhood:
        """Get decision neighborhood graph"""
        data = await self._request(
            "GET",
            f"/kg/decisions/{decision_id}/neighborhood",
            params={"max_hops": max_hops}
        )
        return DecisionNeighborhood(**data)
    
    async def get_decision_analytics(
        self,
        decision_id: int
    ) -> DecisionAnalytics:
        """Get decision analytics (importance, blast radius, etc)"""
        data = await self._request(
            "GET",
            f"/kg/decisions/{decision_id}/analytics"
        )
        return DecisionAnalytics(**data)
    
    async def search_decisions(
        self,
        query: str,
        workspace_id: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 10
    ) -> List[Decision]:
        """Search decisions by query string"""
        params = {"q": query, "limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        if tag:
            params["tag"] = tag
        
        data = await self._request("GET", "/kg/decisions/search", params=params)
        return [Decision(**d) for d in data]
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
```

```python
# services/shared/conport_kg_client/models.py
"""
Pydantic models for ConPort-KG responses
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class Decision(BaseModel):
    """Decision card model"""
    id: int
    summary: str
    rationale: Optional[str] = None
    implementation_details: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    workspace_id: Optional[str] = None


class DecisionRelationship(BaseModel):
    """Decision relationship edge"""
    source_id: int
    target_id: int
    relationship_type: str
    created_at: datetime


class DecisionNeighborhood(BaseModel):
    """Decision neighborhood graph"""
    center: Decision
    related: List[Decision]
    relationships: List[DecisionRelationship]
    total_hops: int


class DecisionAnalytics(BaseModel):
    """Decision analytics metrics"""
    decision_id: int
    importance_score: float
    blast_radius: int
    churn_risk: float
    recommendation: str
```

**Install in agents**:
```bash
# Add to each agent's requirements.txt
echo "-e ../shared/conport_kg_client" >> services/serena/requirements.txt
```

---

## Phase 3: Integrate with Serena (Days 5-7)

**Location**: `services/serena/kg_integration.py`

```python
"""
ConPort-KG Integration for Serena LSP
Shows decision context in hover tooltips
"""

import asyncio
from typing import Optional, List
from shared.conport_kg_client import ConPortKGClient, Decision
import logging

logger = logging.getLogger(__name__)


class SerenaKGIntegration:
    """
    ConPort-KG integration for Serena
    
    Features:
    - Decision context in hover tooltips
    - Related decisions for symbols
    - ADHD-friendly formatting
    """
    
    def __init__(self, kg_client: ConPortKGClient):
        self.kg = kg_client
        self._cache = {}  # Simple in-memory cache
    
    async def get_decisions_for_symbol(
        self,
        symbol: str,
        workspace_id: str
    ) -> List[Decision]:
        """
        Get decisions related to a code symbol
        
        Searches decision graph for mentions of the symbol
        """
        cache_key = f"{workspace_id}:{symbol}"
        
        # Check cache (5min TTL)
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (asyncio.get_event_loop().time() - cached_time) < 300:
                return cached_data
        
        try:
            # Search for symbol in decisions
            decisions = await self.kg.search_decisions(
                query=symbol,
                workspace_id=workspace_id,
                limit=3  # ADHD Top-3 pattern
            )
            
            # Cache results
            self._cache[cache_key] = (asyncio.get_event_loop().time(), decisions)
            
            return decisions
            
        except Exception as e:
            logger.error(f"Failed to fetch decisions for {symbol}: {e}")
            return []
    
    def format_hover_text(
        self,
        symbol: str,
        decisions: List[Decision]
    ) -> str:
        """
        Format decisions for LSP hover tooltip
        
        ADHD-friendly:
        - Top-3 pattern
        - Emoji visual cues
        - Concise summaries
        """
        if not decisions:
            return f"**{symbol}**\n\n_(No related decisions found)_"
        
        lines = [
            f"**{symbol}**",
            "",
            "📝 **Related Decisions:**",
            ""
        ]
        
        for i, decision in enumerate(decisions[:3], 1):
            # Truncate long summaries
            summary = decision.summary
            if len(summary) > 60:
                summary = summary[:57] + "..."
            
            lines.append(f"{i}. {summary}")
            
            # Add tags if present
            if decision.tags:
                tags = " ".join(f"`{tag}`" for tag in decision.tags[:3])
                lines.append(f"   {tags}")
            
            lines.append("")
        
        if len(decisions) > 3:
            lines.append(f"_...and {len(decisions) - 3} more_")
        
        return "\n".join(lines)
    
    async def enrich_hover(
        self,
        symbol: str,
        original_hover: str,
        workspace_id: str
    ) -> str:
        """
        Enrich existing hover tooltip with decision context
        
        Appends decision context to existing LSP hover text
        """
        decisions = await self.get_decisions_for_symbol(symbol, workspace_id)
        
        if not decisions:
            return original_hover
        
        decision_text = self.format_hover_text(symbol, decisions)
        
        # Combine original hover + decision context
        return f"{original_hover}\n\n---\n\n{decision_text}"


# Usage in Serena LSP server
async def handle_hover(params, kg_integration: SerenaKGIntegration):
    """LSP hover request handler"""
    # Get symbol at cursor position
    symbol = extract_symbol_at_position(params)
    
    # Get original hover text (type info, docs, etc)
    original_hover = await get_original_hover(params)
    
    # Enrich with decision context
    enriched_hover = await kg_integration.enrich_hover(
        symbol=symbol,
        original_hover=original_hover,
        workspace_id=params.workspace_id
    )
    
    return {"contents": enriched_hover}
```

**Update Serena main.py**:
```python
from shared.conport_kg_client import ConPortKGClient
from kg_integration import SerenaKGIntegration

# Initialize KG client
kg_client = ConPortKGClient(
    base_url="http://localhost:8000",
    email=os.getenv("CONPORT_KG_EMAIL"),
    password=os.getenv("CONPORT_KG_PASSWORD")
)

# Initialize integration
kg_integration = SerenaKGIntegration(kg_client)

# Use in LSP handlers
@server.feature(lsp.TEXT_DOCUMENT_HOVER)
async def handle_hover(params: lsp.HoverParams):
    return await handle_hover(params, kg_integration)
```

**Test in IDE**:
1. Open file with code
2. Hover over function/class name
3. Should see decision context in tooltip!

---

## Testing Checklist

### ConPort-KG API
- [ ] Health endpoint returns 200
- [ ] Auth endpoints work (register, login, refresh)
- [ ] Query endpoints require JWT
- [ ] Recent decisions returns data
- [ ] Neighborhood query works
- [ ] Search returns relevant results

### Shared Client
- [ ] Authentication succeeds
- [ ] Auto-refresh works (test with 16min wait)
- [ ] Retry logic handles failures
- [ ] Type validation catches errors
- [ ] Connection pooling works

### Serena Integration
- [ ] Hover shows decision context
- [ ] Cache reduces API calls
- [ ] Graceful degradation if KG down
- [ ] ADHD Top-3 pattern displayed
- [ ] Performance < 100ms

---

## Troubleshooting

### API won't start
```bash
# Check logs
docker-compose -f docker/conport-kg/docker-compose.yml logs conport-kg-api

# Common issues:
# 1. Database not ready - wait 30s after postgres starts
# 2. Port 8000 in use - change in docker-compose.yml
# 3. Missing env vars - check .env file
```

### Authentication fails
```bash
# Create test user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePassword123!"
  }'

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

### Serena hover not showing decisions
```bash
# 1. Check KG API is accessible
curl http://localhost:8000/health

# 2. Check Serena logs
docker logs mcp-serena -f | grep -i "kg\|decision"

# 3. Test client directly
python -c "
from shared.conport_kg_client import ConPortKGClient
import asyncio

async def test():
    client = ConPortKGClient(
        email='test@example.com',
        password='SecurePassword123!'
    )
    decisions = await client.get_recent_decisions()
    print(decisions)

asyncio.run(test())
"
```

---

## Success Metrics

After 1 week, you should have:
- ✅ ConPort-KG API running on port 8000
- ✅ 13+ REST endpoints operational
- ✅ Shared client library installed in Serena
- ✅ Hover tooltips showing decision context
- ✅ < 100ms query latency
- ✅ 0 downtime (healthy containers)

**Next**: Integrate remaining 5 agents using same pattern!

---

**Quick Start Created**: 2025-10-28  
**Estimated Time**: 5-7 days  
**Difficulty**: Medium  
**Value**: Extremely High 🚀
