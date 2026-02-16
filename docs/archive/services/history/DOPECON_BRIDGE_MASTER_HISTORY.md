---
id: DOPECON_BRIDGE_MASTER_HISTORY
title: Dopecon Bridge Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Dopecon Bridge Master History (explanation) for dopemux documentation and
  developer workflows.
---
# DopeconBridge: Master History & Feature Catalog

**Service ID**: `dopecon-bridge` (formerly Integration Bridge)
**Role**: Central Nervous System / Event Bus / Authority Gateway
**Primary Owner**: @hu3mann
**Latest Version**: 2.0 (Production Ready)
**Port**: 3016

---

## 1. Executive Summary & Evolution

DopeconBridge is the single authoritative gateway for all communication within Dopemux. It enforces the "No Direct Access" rule—preventing any service from touching ConPort's database directly. Instead, all traffic flows through the Bridge via defined events and routes.

**Evolutionary Phases:**
*   **Phase 1 (Integration Bridge)**: Originally a simple proxy to decouple services from ConPort.
*   **Phase 2 (DopeconBridge)**: Renamed and expanded into a full "Central Nervous System".
*   **Migration**: A massive effort migrated all 19 services (Cognitive, PM, Experimental) to use the bridge, effectively "closing the loop" on the architecture.

---

## 2. Feature Catalog (Exhaustive)

### Core Components
*   **Event Bus**: Redis Streams-backed event distribution with deduplication (10-minute window) and history.
*   **Cross-Plane Router**: Routes traffic between the **PM Plane** (Leantime, TaskMaster) and **Cognitive Plane** (Serena, ConPort, ADHD Engine).
*   **Knowledge Graph Authority**: The *only* valid way to write to ConPort (`/kg/*` endpoints).
*   **Decision Graph**: Search and retrieval of decisions (`/ddg/*`).

### Capabilities
*   **Broker Pattern**: Decouples producers (e.g., Serena) from consumers (e.g., Dashboard).
*   **Authority Enforcement**: Rejects direct SQL/HTTP connections to protected resources.
*   **Pattern Detection**: Analyzes event streams for "Decision Churn" or "Context Switching" patterns.
*   **Custom Data Storage**: Key-value store for workspace-specific data (`/kg/custom_data`).

---

## 3. Architecture Deep Dive

### The "Two-Plane" Connector
DopeconBridge sits physically and logically between the planes:
```
[PM Plane: Leantime] <---> [DopeconBridge] <---> [Cognitive Plane: ConPort/Serena]
```

### Protocol & Transport
*   **Transport**: HTTP (REST) for commands, Redis Streams for events.
*   **Security**: Token-based authentication (`DOPECONBRIDGE_TOKEN`).
*   **Clients**: Official Python client (`services/shared/dopecon_bridge_client`) used by all 19 services.

---

## 4. Validated Status (Audit Results)

**✅ Working / Production Ready:**
*   **Migration Status**: 100% Complete (19/19 services).
*   **Zero Direct Access**: Verified via `grep` audit (no `ConPortSQLiteClient` usage outside of tests).
*   **Documentation**: extensive (95KB+), including Master Guide and Quick Start.
*   **Performance**: Async client handles high throughput; verified via stress tests.

**⚠️ Gaps:**
*   **Experimental Services**: 4 services (e.g., Genetic Agent, GPT Researcher) are "Experimental" and less battle-tested than core ones.

---

*Sources: `DOPECONBRIDGE_MASTER_GUIDE.md`, `DOPECONBRIDGE_SERVICE_CATALOG.md`, `README.md`.*
