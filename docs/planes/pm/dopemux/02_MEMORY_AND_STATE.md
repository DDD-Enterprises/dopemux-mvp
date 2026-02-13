---
title: "Memory and State"
plane: "pm"
component: "dopemux"
status: "proposed"
---

# Memory and State

## Purpose
What state exists, where it lives, and how it is written/read without cross-worktree contamination. This document defines the single source of truth for all persistence in Dopemux.

## Scope
- All persistent data storage (files, databases, caches).
- State isolation boundaries between worktrees.
- ConPort as the decision/provenance authority.
- Session context schema and lifecycle.

## Non-negotiable invariants

### INV-MEM-001: Worktree Isolation
**Statement**
- MUST NOT read or write state from another worktree unless explicitly authorized via a global rollup API.

**Owner**
- Supervisor

**Scope**
- Applies to: per-worktree
- Surfaces: `dopemux run`, `state.db`

**Evidence**
- FACT ANCHORS:
  - `scripts/repo_preflight.sh` (defines `.repo_id` check)

**Enforcement**
- Mechanism:
  - Runtime: refusal if `.repo_id` mismatches current root.
  - Storage: SQLite file locking.

**Test**
- Local command(s):
  - `cd /tmp/other_repo && dmux run` (simulated)
- Expected signals:
  - "Repository identity mismatch" or "Database locked"
- Failure signature:
  - Process accesses wrong DB file.
- Exit behavior:
  - Stop (Exit 1).

**Failure modes**
- If violated:
  - Impact: data corruption, context leakage.
  - Severity: S0 critical.
  - Containment: File system permissions / containerization.

### INV-MEM-002: ConPort Authority
**Statement**
- MUST treat ConPort as the authoritative source for decision provenance and task progress.

**Owner**
- Supervisor

**Scope**
- Applies to: per-packet
- Surfaces: `docs/planes/`, `docs/decisions/`

**Evidence**
- FACT ANCHORS:
  - `src/dopemux/conport/wire_project.py` (wiring logic)

**Enforcement**
- Mechanism:
  - Gate: `doc_gate.py` (checks structure)
  - Runtime: refusal to proceed if ConPort cannot be written.

**Test**
- Local command(s):
  - `chmod -w docs/decisions && dmux decide ...`
- Expected signals:
  - "ConPort write failed"
- Failure signature:
  - Decision made but not recorded.
- Exit behavior:
  - Stop.

**Failure modes**
- If violated:
  - Impact: trust leak, lost history.
  - Severity: S1 high.
  - Containment: Queue writes and retry.

### INV-MEM-003: Append-Only Ledger
**Statement**
- MUST treat event ledgers (runs, decisions, tool outputs) as append-only.

**Owner**
- Store

**Scope**
- Applies to: per-run
- Surfaces: `state.db`, `logs/`

**Evidence**
- FACT ANCHORS:
  - `services/session-manager/` (DB usage implied)

**Enforcement**
- Mechanism:
  - Storage: Database schema constraints (no UPDATE/DELETE on history tables).

**Test**
- Local command(s):
  - `sqlite3 .dopemux/state.db "UPDATE events ..."` (manual check)
- Expected signals:
  - SQL Error (if triggers implemented) or Policy Audit failure.
- Failure signature:
  - History rewritten.
- Exit behavior:
  - N/A (Storage layer).

**Failure modes**
- If violated:
  - Impact: audit loss, gaslighting.
  - Severity: S0 critical.
  - Containment: Backup snapshots.

### INV-MEM-004: Promotion is Interpretation
**Statement**
- MUST explicitly distinguish between "Raw Facts" (tool output) and "Promoted Truth" (Supervisor interpretation).

**Owner**
- Supervisor

**Scope**
- Applies to: global rollup
- Surfaces: `docs/decisions/`, `summary.md`

**Evidence**
- FACT ANCHORS:
  - `src/dopemux/conport/` (promotion logic TBD)

**Enforcement**
- Mechanism:
  - Runtime: Promoted content MUST cite source event ID.

**Test**
- Local command(s):
  - `dmux promote <ID>`
- Expected signals:
  - "Promoted event <ID> to ConPort"
- Failure signature:
  - Summary contradicts logs.
- Exit behavior:
  - Warn.

**Failure modes**
- If violated:
  - Impact: Hallucinated status.
  - Severity: S2 medium.
  - Containment: Re-derive from raw logs.

### INV-MEM-005: Redaction Never Persists Secrets
**Statement**
- MUST NOT persist API keys or PII to disk (logs, DB, or ConPort).

**Owner**
- Supervisor

**Scope**
- Applies to: per-run
- Surfaces: `state.db`, `logs/`

**Evidence**
- FACT ANCHORS:
  - `config/security/redaction_rules.json` (planned)

**Enforcement**
- Mechanism:
  - Runtime: Regex scrubber on all DB writes and Log emits.

**Test**
- Local command(s):
  - `dmux run --input "my key is sk-123"`
- Expected signals:
  - Log shows `my key is [REDACTED]`
- Failure signature:
  - Cleartext key in `state.db`.
- Exit behavior:
  - Log Warning & Scrub.

**Failure modes**
- If violated:
  - Impact: Security breach.
  - Severity: S0 critical.
  - Containment: Rotate keys immediately.

## FACT ANCHORS (Repo-derived)
- **ConPort Wiring**: `src/dopemux/conport/wire_project.py`
- **Worktree Identity**: `scripts/repo_preflight.sh` (defines `.repo_id` and root check)
- **Session Manager DB**: `services/session-manager/` (implies local state).
- **Serena DB**: `services/serena/intelligence/database.py` (references `SERENA_DB_PASSWORD`).

## Open questions
- **Global Rollups**: How do we aggregate multi-repo stats without breaking isolation?
  - *Resolution*: Define a separate "Observer" plane that reads-only from multiple approved roots.
- **Secret Redaction**: What is the exact regex list for redaction?
  - *Resolution*: `config/security/redaction_rules.json` (to be created).

## State taxonomy

### Ephemeral
- **Session State**: In-memory Python objects during a Supervisor run (e.g., loaded context, current prompt buffer).
- **Focus Window State**: Short-lived timers or counters for the current 25-minute block.
- **Transient Caches**: `/tmp/dopemux/cache/` for large tool outputs or intermediate diffs. Cleared on reboot or explicit `dmux clean`.

### Workspace (per-worktree)
- **Workspace Identity**: `.repo_id` (file) containing project name and owner.
- **Local State Store**: `.dopemux/state.db` (SQLite) containing:
  - Session history (prompts/responses).
  - Local usage limits and quotas.
  - Checkpoint metadata.
- **Per-worktree Memory Views**: `.dopemux/memory/` containing summarized context files (e.g., `arch_summary.md`, `active_decisions.md`).

### Project (per repo)
- **Canonical Repo-level Stores**: `docs/planes/` (PM/Arch/Eng/Compliance).
- **ConPort**: The directory structure in `docs/` or `.dopemux/conport/` that tracks formal decisions (ADRs), risks, and packets.
- **Shared Read Paths**: Config files in `config/` that are checked into git.

### Global (rollups)
- **Cross-repo Summaries**: `~/.dopemux/global/stats.db` (optional).
- **Usage Aggregation**: Aggregated token costs across all projects (if enabled).

## ConPort as memory authority
ConPort is the "Constitution and Port" of the project. If it's not in ConPort, it didn't formally happen.

- **Decisions**: ADRs (Architecture Decision Records) stored in `docs/decisions/`.
- **Progress**: Task Packets in `docs/packets/` with status (DRAFT, APPROVED, COMPLETED).
- **Links**: `00_INDEX.md` files serving as entry points.
- **Provenance**: Traceability of *why* a change was made (linked to a Packet ID).

**Minimum Required ConPort Records for a Run**:
1. **Packet ID**: Every run must be associated with a valid Packet ID (e.g., `TP-123`).
2. **Result State**: Success, Failure, or Refusal.
3. **Artifact List**: Detailed list of files modified or created.

## Session Context SQLite usage
**Path**: `.dopemux/state.db`

**Schema (Draft)**:
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    status TEXT,
    packet_id TEXT
);

CREATE TABLE events (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    type TEXT, -- 'tool_call', 'user_input', 'model_output', 'warning'
    payload TEXT, -- JSON
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
```

**Lifecycle**:
- **Write**: Supervisor writes events synchronously as they happen.
- **Read**: Supervisor reads recent events to build context window for the next turn.
- **Archive**: Old sessions are pruned or archived to flat files after N days (default: 30).

## Rollup index contract
- **What is Promoted**: High-level status changes, new ADRs, major milestone completions.
- **What is NEVER Promoted**: Raw tool outputs, massive diffs, debug logs, chatter.
- **When Promotion Happens**: At the successful completion of a Task Packet.
- **Attribution**: Promotion is an *interpretation* event by the Supervisor ("We finished X"), not just a raw fact.

## Redaction and safety boundaries
- **Never Persist**:
  - API Keys / Secrets (even if found in logs).
  - PII (emails, phone numbers) unless explicitly whitelisted for the domain.
- **Sensitive Fields**: `payload` in SQLite must be scrubbed for secrets before insert.
- **Operator Controls**: `dmux purge --session <id>` must aggressively delete all traces of a session.

## Hard invariants & Failure Modes

### 1. Cross-Worktree Contamination
- **Invariant**: Process A (Worktree A) cannot open `.dopemux/state.db` of Worktree B.
- **Failure Mode**: `sqlite3.OperationalError` (database locked) or data corruption if multiple processes fight.
- **Refuse Condition**: strict file locking on DB; if lock held by another PID, **STOP** and fail immediately. Do not wait/spin.

### 2. Stale Reads
- **Invariant**: Supervisor operates on the latest state on disk.
- **Failure Mode**: Supervisor makes decisions based on cached file content that has changed on disk.
- **Refuse Condition**: If file mtime changes during a read/plan cycle, **STOP** and force a context refresh.

### 3. Memory Corruption
- **Invariant**: `state.db` integrity check passes on startup.
- **Failure Mode**: DB file is malformed (zero bytes, half-written page).
- **Refuse Condition**: If `PRAGMA integrity_check` fails, **STOP**. Do not attempt auto-repair. Require operator intervention (`dmux repair-state`).

## Acceptance criteria
1. **Isolation Test**: Spawn two shells in different repo roots. Ensure `dopemux run` in one does not affect the `.dopemux/state.db` of the other.
2. **Persistence Test**: Run a packet, kill the process, restart. Ensure session history up to the kill point is preserved in SQLite.
3. **Refusal Test**: Manually lock the `state.db` (e.g., via `sqlite3` shell). Attempt to run Dopemux. It must exit with a clear "Database Locked" error, not hang.
