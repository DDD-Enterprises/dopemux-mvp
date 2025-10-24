# @dopemux/conport-client

**Unified ConPort Client** - Single canonical interface for all Dopemux systems

## Overview

Consolidates 3 different ConPort client implementations into one shared package:
- **Before**: Serena (PostgreSQL), ADHD Engine (SQLite), ConPort MCP (PostgreSQL AGE)
- **After**: Single client with backend adapters

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Unified ConPort Client API                              │
│  - get_decisions()                                      │
│  - log_decision()                                       │
│  - get_progress()                                       │
│  - update_progress()                                    │
│  - get_active_context()                                 │
│  - update_active_context()                              │
│  - semantic_search()                                    │
│  - get_linked_items()                                   │
└───────────────────┬─────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Backend Adapter Layer │
        └───────┬───────────────┘
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
┌────────┐  ┌────────┐  ┌─────────┐
│ PG AGE │  │ SQLite │  │ MCP RPC │
│Adapter │  │Adapter │  │ Adapter │
└────────┘  └────────┘  └─────────┘
```

## Features

### 1. Backend Agnostic
- PostgreSQL AGE (production)
- SQLite (development/testing)
- MCP RPC (Claude Code integration)
- File-based (offline mode)

### 2. Auto-Detection
- Detects available backends
- Falls back gracefully
- Configurable priority order

### 3. Unified API
- Single import for all systems
- Consistent error handling
- Type-safe with Pydantic models

### 4. Performance
- Connection pooling
- Query caching
- Batch operations

## Usage

```python
from dopemux.conport_client import ConPortClient

# Auto-detect best backend
client = ConPortClient(workspace_id="/path/to/project")

# Or specify backend
client = ConPortClient(
    workspace_id="/path/to/project",
    backend="postgresql_age"  # or "sqlite", "mcp", "file"
)

# Use unified API
decision = await client.log_decision(
    summary="My decision",
    rationale="Why I decided this",
    tags=["architecture"]
)

decisions = await client.get_decisions(limit=10)
```

## Migration Guide

### For Serena v2
```python
# Before
from conport_db_client import ConPortDBClient
conport = ConPortDBClient(workspace_id)

# After
from dopemux.conport_client import ConPortClient
conport = ConPortClient(workspace_id, backend="postgresql_age")
```

### For ADHD Engine
```python
# Before
from conport_client import ConPortSQLiteClient
conport = ConPortSQLiteClient(db_path, workspace_id)

# After
from dopemux.conport_client import ConPortClient
conport = ConPortClient(workspace_id, backend="sqlite", db_path=db_path)
```

### For New Systems
```python
# Just works!
from dopemux.conport_client import ConPortClient
conport = ConPortClient(workspace_id)  # Auto-detects best backend
```

## Benefits

1. **Reduced Technical Debt**: 3 implementations → 1
2. **Easier Maintenance**: Single codebase to maintain
3. **Better Testing**: Shared test suite
4. **Faster Development**: New systems get ConPort for free
5. **Consistent Behavior**: Same API across all systems
