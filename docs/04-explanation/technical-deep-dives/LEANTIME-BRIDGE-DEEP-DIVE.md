# Leantime Bridge: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
The Leantime Bridge is a critical integration component in the "PM Plane" of Dopemux, connecting the Task Orchestrator and ADHD Engine to the Leantime project management system. It serves as the authoritative interface for task synchronization, status updates, and project tracking.

Structured as an MCP (Model Context Protocol) server, it provides a standardized toolset (`create_ticket`, `list_projects`, etc.) that allows AI agents and internal services to interact with Leantime without needing to understand its internal JSON-RPC implementation details.

### Architecture & Core Components (Validated)
The service is a Python-based MCP server using `Starlette` and `Uvicorn`, implementing both SSE transport and REST compatibility endpoints.

*   **Service Type**: MCP Server (HTTP/SSE + REST)
*   **Port**: 3015
*   **Container**: `mcp-leantime-bridge`
*   **Upstream**: Leantime (HTTP JSON-RPC)

**Core Modules**:
1.  **`http_server.py`**: The main entry point. Implements the MCP server, tool registration, and the `Starlette` app. It handles:
    *   **SSE Transport**: `/sse` and `/messages/` for standard MCP clients.
    *   **REST Compatibility**: `/api/tools/{tool_name}` for legacy/simple clients.
    *   **Health & Info**: `/health` (deep/shallow) and `/info` (discovery).
2.  **`LeantimeClient`**: A wrapper around `httpx` that handles the specific JSON-RPC format of Leantime, including authentication tokens and error parsing.
3.  **Method Fallback Architecture**: The bridge implements a sophisticated "method candidate" system (e.g., trying `leantime.rpc.Projects.addProject`, then `leantime.addProject`) to remain robust across different Leantime API versions.

### Integration Patterns & Data Flow
1.  **Task Orchestrator Integration**:
    *   Orchestrator calls the bridge to create tasks, update statuses, and log work.
    *   **Data Flow**: `Orchestrator -> Bridge (MCP) -> Leantime (JSON-RPC)`.
2.  **Health & Readiness**:
    *   Implements a "Deep Health" check (`/health?deep=1`) that actively probes the upstream Leantime instance.
    *   Capable of detecting "Setup Required" states (redirects to `/install`) and reporting them as structured health degradation (`503 Needs Setup`).

### Testing, Performance, Limitations & Opportunities
*   **Testing**: Comprehensive contract tests (`test_contract_api_tools.py`) verify API interactions, error handling, and method fallbacks.
*   **Performance**: Uses `httpx.AsyncClient` for non-blocking I/O.
*   **Limitations**:
    *   **Auth Dependency**: Strictly requires `LEANTIME_API_TOKEN` to be configured. The service will be healthy but tools will fail if the token is missing.
    *   **Setup Gate**: Cannot function until Leantime itself is fully installed and an admin user is created.
*   **Opportunities**:
    *   Automated token generation/retrieval during the setup phase to reduce manual friction.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
*   **Source Code**: `docker/mcp-servers/leantime-bridge/leantime_bridge/` (Verified).
*   **Runtime**: Container `mcp-leantime-bridge` is healthy and listening on port 3015.

### Failure & Drift Findings (Phase 2)
*   **Configuration**: Matches standard MCP pattern.
*   **Drift**: None observed. The codebase is well-structure and aligned with recent audit reports.
*   **Readiness**: The `LEANTIME_BRIDGE_READINESS` audit confirms the service is "CLOSED" (operational) in fully configured environments, though it requires manual setup steps to reach that state.

### Cross-Validation Summary
*   **Audit Report**: `docs/05-audit-reports/LEANTIME_BRIDGE_READINESS_2026-02-06.md` provides definitive proof of readiness logic and recent hardening (e.g., explicit setup hints).
*   **Code Analysis**: `http_server.py` confirms the implementation of all features described in the audit report.

## SECTION 3: LIVING DOCUMENTATION METADATA
- Last Validated: 2026-02-09
- Confidence Level: 100% (Source, Runtime, and Audit validated)
- Evidence Quality Score: High (Comprehensive audit report + code verification)
- Evolution Log:
    - 2026-02-09: Initial Deep Dive. Confirmed alignment with 2026-02-06 Audit.
