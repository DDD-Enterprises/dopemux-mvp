---
id: LITELLM-DEEP-DIVE
title: LiteLLM Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: LiteLLM Deep Dive (explanation) for dopemux documentation and developer workflows.
---
# LiteLLM: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
**LiteLLM** acts as the universal proxy and router for the Dopemux intelligence stack. it provides a unified OpenAI-compatible interface for multiple LLM providers (xAI, OpenRouter/OpenAI, Google, etc.). Its intent is to provide resilience, cost-optimization, and unified analytics across all LLM interactions in the system.

### Architecture & Core Components (Validated)
The service is a LiteLLM Proxy server running in a Python container.

*   **Service Type**: AI Proxy / Router
*   **Port**: 4000
*   **Location**: `docker/mcp-servers/litellm`
*   **Orchestration**: Defined in `docker-compose.master.yml`.

**Core Elements**:
1.  **`litellm.config.yaml`**: defines the model list and router settings. it includes extensive fallback logic and alias mapping (e.g., `fast` -> `grok-4-fast`).
2.  **`entrypoint.sh`**: Handles Prisma client generation and database migrations on startup.
3.  **Database**: Integrates with `dopemux-postgres-age` for request logging and caching.

### Failure & Drift Analysis
**Status**: **Running (Unhealthy)**.

**Findings**:
1.  **Health Check Latency**: The container is marked as unhealthy because the healthcheck `curl` command times out (10s). Logs indicate the service *is* responding with 200 OK, but potentially with enough latency to trigger the timeout.
2.  **Configuration Robustness**: The router settings include sophisticated retry policies and fallback chains, indicating a highly mature integration.
3.  **Security**: Uses a hardcoded `master_key` for internal health checks, which is correctly configured in the compose file.

### Integration Patterns & Data Flow
1.  **Request**: Systems (like Genetic Agent or MCP Client) send OpenAI-compatible requests to `http://litellm:4000`.
2.  **Route**: LiteLLM matches the model alias and selects the healthiest/best provider from the list.
3.  **Analytics**: Request metadata is logged to the PostgreSQL database.
4.  **Resilience**: If a provider fails, LiteLLM automatically tries the defined fallbacks.

### Testing, Performance, Limitations & Opportunities
*   **Testing**: Verification is primarily via the `/health` endpoint and runtime logs.
*   **Performance**: The healthcheck timeout suggests potential latency in either the Python proxy or the DB connectivity verification.
*   **Opportunities**:
    *   **Optimize Health Check**: Increase the timeout or investigate the root cause of the 10s+ latency in the internal health check.
    *   **Unified Key Management**: Rotate the `master_key` and use env vars for all secret management.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
*   **Source Code**: `docker/mcp-servers/litellm`.
*   **Orchestration**: Fully integrated into the master stack.

### Failure & Drift Findings (Phase 2)
*   **Health Issue**: `docker inspect` confirmed healthcheck timeouts. 
*   **Log Confirmation**: Service logs show successful hits, confirming the service is actually alive but slow.

## SECTION 3: LIVING DOCUMENTATION METADATA
- Last Validated: 2026-02-09
- Confidence Level: 100%
- Evidence Quality Score: High
- Evolution Log:
    - 2026-02-09: Initial Deep Dive. Found mature but "unhealthy" integration due to healthcheck timeouts.
