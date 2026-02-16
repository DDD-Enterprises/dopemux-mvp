---
id: CONPORT_MASTER_HISTORY
title: Conport Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Conport Master History (explanation) for dopemux documentation and developer
  workflows.
---
# ConPort (Context Portal): Master History & Feature Catalog

**Service ID**: `conport`
**Role**: Central Nervous System / Memory Hub
**Primary Owner**: @hu3mann
**Latest Version**: V2.0 (PostgreSQL/AGE/Qdrant)

---

## 1. Executive Summary & Evolution

ConPort began as a simple "Context Portal" for properly logging developer context but evolved into the **central nervous system** of the Dopemux architecture. It effectively replaced disparate "memory" solutions with a unified Knowledge Graph (KG) that connects human strategy (Leantime), AI execution (Agents), and tactical coordination (Orchestrator).

**Evolutionary Phases:**
*   **Phase 1 (Legacy)**: Simple SQLite database for logging "decisions". Direct synchronous Access.
*   **Phase 2 (Service Mesh)**: Standalone Docker service, but still limited integration.
*   **Phase 3 (The "Bridge" Era - Current)**: A highly distributed architecture where ConPort is not just a database, but a set of "Bridge Clients" embedded in every major service (Serena, Orchestrator, GPT-Researcher). It now supports:
  * **Vector Search** (Semantic understanding)
  * **Graph Queries** (AGE/Cypher)
  * **Multi-Workspace Support**
  * **Async Event Bus Integration**

---

## 2. Feature Catalog (Exhaustive)

### Core Capabilities
* **Semantic Search**: Uses Voyage AI embeddings to find "similar decisions" or "related work" across projects.
* **Knowledge Graph**: Stores entities (Decisions, Work Items, Artifacts) and their relationships (`implements`, `blocked_by`, `verifies`).
* **Distributed Bridge Architecture**: Functionality is distributed via SDKs (`conport_bridge.py`, `age_client.py`) rather than a monolithic API.
* **Multi-Workspace Namespaces**: Data is isolated by `workspace_id`, allowing a single ConPort instance to manage detailed context for multiple distinct repositories.
* **Async Event Handling**: Listens for system events (`decision.logged`, `task.started`) to proactively load context.

### Data Namespaces (The "Big Three")
1.  **Decisions (`decisions/*`)**:
  * Atomic units of architectural history.
  * Schema: `title`, `rationale`, `implementation_details`, `tags`, `links`.
  * **Feature**: "Genealogy" - tracking parent/child relationships between decisions.
2.  **Work Items (`work/*`)**:
  * Unified task queue bridging Leantime tickets and internal tasks.
  * Schema: `priority`, `cognitive_load`, `energy_required`.
3.  **Artifacts (`artifacts/*`)**:
  * Evidence of work (Logs, Screenshots, Diffs).
  * Schema: `kind`, `path`, `hash`, `mime_type`.

### ADHD Optimizations
* **Progressive Disclosure**: Three tiers of data presentation to prevent overwhelm:
  * Tier 1: `DecisionCard` (Summary)
  * Tier 2: `DecisionSummary` (Details)
  * Tier 3: `DecisionNeighborhood` (Graph relations)
* **Cognitive Load Scoring**: Automatic calculation of complexity (0.0 - 1.0) based on task metadata.
* **Context Preservation**: "Spooling" operations to disk if the service is down, ensuring no thought is ever lost ("No User Context Lost" guarantee).
* **Proactive Context**: Automatically finding relevant decisions when a file is opened (via Serena).

---

## 3. Architecture Deep Dive

### The "Bridge" Pattern
Unlike a traditional REST API, ConPort's power lies in its client libraries:
*   **`age_client.py`**: Handles raw Cypher/SQL over `psycopg2` with connection pooling.
*   **`conport_bridge.py`** (Serena): Bidirectional linking between Code and Decisions.
*   **`orchestrator_client.py`**: Dual-mode (MCP + HTTP) for reliability.

### The Storage Layer
*   **Primary**: PostgreSQL (Metadata, Structured Data).
*   **Graph**: Apache AGE (Graph traversal, Cypher queries).
*   **Vector**: Qdrant (Embeddings).
*   **Cache**: Redis (Query results, frequent context).

---

## 4. Integration Points

| Integration | Direction | Features |
|-------------|-----------|----------|
| **Serena** | Bidirectional | Code-to-Decision linking. "Show me why this code exists" (Reverse lookup). |
| **Task Orchestrator** | Bidirectional | Logs progress. Retrieves "Next Best Action" based on energy/priority. |
| **Leantime** | Inbound | Syncs "Strategic Tickets" into "Tactical Work Items". |
| **Playwright** | Inbound | Attaches validation artifacts (Screenshots) to Work Items. |
| **GPT-Researcher** | Bidirectional | Persists long-running research sessions. Auto-saves every 30s. |

---

## 5. Validated Status (Audit Results)

**✅ Working / Production Ready:**
*   AGE Client connection pooling (1-5 connections).
*   Event-Driven trigger patterns (`decision.logged` → auto-similarity search).
*   Error Handling (Retry logic, Circuit breakers).
*   MCP Streamable Transport (Stdio/HTTP).
*   Active decision logging (396+ decisions in prod).

**⚠️ Gaps / Incomplete:**
*   **Security**: Cypher injection risk identified (raw string formatting in `age_client.py`).
*   **Encryption**: No SSL/TLS on DB connections.
*   **Docs**: "Technical Deep Dive" and "Executive Summary" files were found to be empty placeholders.
*   **Metrics**: No query performance monitoring yet.

---

## 6. Development Artifacts & Schemas

**`mem4sprint` Meta-Schema**:
Defines strict validation rules for Sprint entities: `sprint_goal`, `sprint_subtask`, `bug`, `risk`, `rfc_doc`.
*   *Key Rule*: `id_uniqueness`, `require_existing_nodes_for_edges`.

**FTS Rules**:
Specific prefixes for SQLite FTS5 compatibility: `summary:`, `rationale:`, `tags:`.

---

*Sources: `phase2-conport-deep-analysis.md`, `conport-dopemux.md` (Blueprint), `mem4sprint-schema-and-patterns.md`, System Audit.*
