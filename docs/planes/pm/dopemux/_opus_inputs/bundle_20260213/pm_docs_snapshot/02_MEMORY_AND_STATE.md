---
title: Memory and State
plane: pm
component: dopemux
status: proposed
id: 02_MEMORY_AND_STATE
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Memory and State (explanation) for dopemux documentation and developer workflows.
---
# Memory and State

## Purpose
What state exists, where it lives, and how it is written/read without cross-worktree contamination. This document defines the single source of truth for all persistence in Dopemux.

## Scope
- All persistent data storage (files, databases, caches).
- State isolation boundaries between worktrees.
- ConPort as the decision/provenance authority.
- Session context schema and lifecycle.

---

## Non-negotiable invariants

### INV-MEM-001: Worktree Isolation

**INV-ID**: INV-MEM-001
**Statement**: A Dopemux process MUST NOT read or write state belonging to another worktree unless explicitly authorized via a global rollup API.
**Scope**: per-worktree
**Owner**: Supervisor
**Enforcement Surface**:
- `scripts/repo_preflight.sh` — validates `.repo_id` matches expected `project=` value before any operation.
- `scripts/taskx` — refuses to run if `.taskxroot` is absent from the resolved `REPO_ROOT`.
- SQLite file locking on `.dopemux/state.db` (one writer per process).
**Violation Mode**: Data corruption, context leakage across projects.
**Detection Method**:
- `repo_preflight.sh` emits `"Refusing: repo_id mismatch"` and exits 2.
- SQLite raises `OperationalError: database is locked` if two processes contend.
**Recovery Strategy**: Process halts immediately (exit 2). Operator verifies CWD and re-runs.
**Evidence**:
- `scripts/repo_preflight.sh` (lines 14-31): checks `.repo_id` exists, parses `project=`, enforces identity match.
- `.repo_id` contains `project=dopemux-mvp`, `owner=hu3mann`, `intent=...refuse if repo_id mismatches`.
- `scripts/taskx` (lines 4-9): refuses if `.taskxroot` missing from repo root.

---

### INV-MEM-002: ConPort Authority

**INV-ID**: INV-MEM-002
**Statement**: ConPort (PostgreSQL AGE on port 5432, exposed via MCP on port 3004) MUST be treated as the authoritative source for decision provenance, task progress, and knowledge graph relationships.
**Scope**: per-packet
**Owner**: Supervisor
**Enforcement Surface**:
- `compose.yml`: ConPort depends on `postgres` (service_healthy), `redis-primary` (service_healthy), `mcp-qdrant` (service_started).
- Task-orchestrator `depends_on: conport` — cannot start without ConPort available.
- ADHD-engine `depends_on: conport` (service_healthy in unified compose).
**Violation Mode**: Trust leak — decisions made but not recorded; lost provenance trail.
**Detection Method**:
- ConPort healthcheck: `curl -f http://localhost:3004/health || exit 0`.
- If ConPort is unreachable during a write, the calling service must refuse to proceed (fail-open is forbidden for authority operations).
**Recovery Strategy**: Queue writes and retry with backoff. If ConPort remains down, halt the operation and surface "ConPort unavailable" to operator.
**Evidence**:
- `compose.yml` (lines 226-258): ConPort service definition with `DATABASE_URL` pointing to `dopemux-postgres-age:5432`, healthcheck on port 3004.
- Task-orchestrator (line 402): `depends_on: conport`.
- `sync.py`: `MultiDirectionalSyncEngine` syncs to ConPort via `CONPORT_TO_LEANTIME`, `LOCAL_TO_CONPORT` directions.

---

### INV-MEM-003: Append-Only Ledger

**INV-ID**: INV-MEM-003
**Statement**: Event ledgers (runs, decisions, tool outputs) MUST be append-only. No UPDATE or DELETE on history tables.
**Scope**: per-run
**Owner**: Store (persistence layer)
**Enforcement Surface**:
- `.dopemux/state.db` schema: `events` table designed for INSERT only.
- `dope-memory` service (`compose.yml` line 464): `DOPEMUX_CAPTURE_LEDGER_PATH=/data/chronicle.sqlite` — the word "chronicle" signals append semantics.
- Database schema constraints (triggers or CHECK constraints) on history tables.
**Violation Mode**: Audit loss, history rewriting ("gaslighting"), unreliable replay.
**Detection Method**:
- Schema audit: `SELECT sql FROM sqlite_master WHERE name='events'` should show no UPDATE triggers that modify existing rows.
- Policy audit script checking for UPDATE/DELETE statements against history tables in codebase.
**Recovery Strategy**: Restore from backup snapshots. The append-only property means any intact prefix of the ledger is trustworthy.
**Evidence**:
- Session schema (this doc): `events` table with `id`, `session_id`, `timestamp`, `type`, `payload` — no UPDATE path specified.
- `dope-memory` service uses `chronicle.sqlite` with `SQLITE_JOURNAL_MODE=DELETE` (line 488 of compose.yml).

---

### INV-MEM-004: Promotion is Interpretation

**INV-ID**: INV-MEM-004
**Statement**: The system MUST explicitly distinguish between "Raw Facts" (tool output, event records) and "Promoted Truth" (Supervisor interpretation). Promoted content MUST cite the source event ID.
**Scope**: global rollup
**Owner**: Supervisor
**Enforcement Surface**:
- Promotion operations must generate a new event of type `promotion` that references the original event ID.
- `docs/decisions/` and `summary.md` entries must carry a `source_event_id` field.
**Violation Mode**: Hallucinated status — a summary claims something happened that the raw logs contradict.
**Detection Method**:
- Audit: for every promoted summary, verify `source_event_id` resolves to a real event in the ledger.
- If `source_event_id` is NULL or points to a non-existent event, flag as integrity violation.
**Recovery Strategy**: Re-derive promoted content from raw logs. Promoted content is always rebuildable from the append-only ledger (INV-MEM-003).
**Evidence**:
- Rollup index contract (this doc): "Promotion is an interpretation event by the Supervisor, not just a raw fact."
- FUTURE: `src/dopemux/conport/` will contain promotion logic. Currently design-only.

---

### INV-MEM-005: Redaction Never Persists Secrets

**INV-ID**: INV-MEM-005
**Statement**: API keys, secrets, and PII MUST NOT be persisted to disk (logs, DB, or ConPort) in cleartext.
**Scope**: per-run
**Owner**: Supervisor
**Enforcement Surface**:
- Runtime regex scrubber on all DB writes and log emits.
- `dmux purge --session <id>` aggressively deletes all traces.
**Violation Mode**: Security breach — credential exposure in persisted state.
**Detection Method**:
- Scan `state.db` and log files for patterns matching `sk-`, `AKIA`, `ghp_`, email regex, phone patterns.
- CI gate: `grep -rn 'sk-\|AKIA\|ghp_\|Bearer ' .dopemux/ logs/` must return zero matches.
**Recovery Strategy**: Rotate compromised keys immediately. Purge affected session with `dmux purge`.
**Evidence**:
- FUTURE: `config/security/redaction_rules.json` (to be created).
- Design requirement in this document.

---

### INV-MEM-006: Session State Lifecycle

**INV-ID**: INV-MEM-006
**Statement**: Every Dopemux run MUST be associated with a session in `.dopemux/state.db`. Session lifecycle is: CREATED -> ACTIVE -> COMPLETED|FAILED|KILLED. A session MUST NOT transition backwards.
**Scope**: per-run
**Owner**: Supervisor
**Enforcement Surface**:
- `sessions` table schema with `status` column constrained to valid states.
- State machine enforcement in Supervisor's session management code.
**Violation Mode**: Zombie sessions (stuck in ACTIVE after crash), ghost data (events without session).
**Detection Method**:
- Startup check: any session in ACTIVE state that was not cleanly closed gets marked KILLED.
- Orphan detection: events with `session_id` not matching any `sessions.id`.
**Recovery Strategy**: Mark stale ACTIVE sessions as KILLED on startup. Orphaned events are retained in the ledger but flagged.
**Evidence**:
- Session schema (this doc): `sessions` table with `id`, `start_time`, `end_time`, `status`, `packet_id`.
- Lifecycle description (this doc): "Write synchronously as they happen."

---

### INV-MEM-007: Stale Read Prevention

**INV-ID**: INV-MEM-007
**Statement**: The Supervisor MUST operate on the latest state on disk. If file mtime changes during a read/plan cycle, the Supervisor MUST stop and force a context refresh.
**Scope**: per-run
**Owner**: Supervisor
**Enforcement Surface**:
- File mtime check before and after read operations.
- SQLite WAL mode or explicit locking to prevent reading during writes.
**Violation Mode**: Supervisor makes decisions based on stale cached content.
**Detection Method**:
- Compare mtime at read-start vs read-end. If different, abort.
- Log warning: "State changed during read cycle, forcing refresh."
**Recovery Strategy**: Discard cached state, re-read from disk, restart the current planning step.
**Evidence**:
- Design requirement: "Hard invariants" section of this document.

---

### INV-MEM-008: Database Integrity on Startup

**INV-ID**: INV-MEM-008
**Statement**: `state.db` integrity MUST be verified on every Supervisor startup via `PRAGMA integrity_check`. If the check fails, the process MUST stop and require operator intervention.
**Scope**: per-run
**Owner**: Supervisor
**Enforcement Surface**:
- First operation on startup: `PRAGMA integrity_check` on `.dopemux/state.db`.
- If result is not "ok", exit with error code and message.
**Violation Mode**: Operating on a corrupted database leads to unpredictable behavior.
**Detection Method**:
- `PRAGMA integrity_check` returns non-"ok" result.
- Zero-byte file detection (file exists but `os.path.getsize() == 0`).
**Recovery Strategy**: Do NOT attempt auto-repair. Require `dmux repair-state` which creates a new DB and imports what can be recovered from the corrupt file.
**Evidence**:
- Design requirement: "Hard invariants" section — "If `PRAGMA integrity_check` fails, STOP."

---

## FACT ANCHORS (Repo-derived)

- **OBSERVED: Repo Identity**: `.repo_id` contains `project=dopemux-mvp`, `owner=hu3mann`. `scripts/repo_preflight.sh` enforces match.
- **OBSERVED: TaskX Guard**: `scripts/taskx` refuses without `.taskxroot` and `.taskx-pin` in repo root.
- **OBSERVED: TaskX Pin**: `.taskx-pin` pins to `repo=https://github.com/hu3mann/taskX.git ref=v0.1.2`.
- **OBSERVED: Persistence Layer**: `services/adhd_engine/core/activity_tracker.py` uses direct SQLite access to `conport.db`.
- **OBSERVED: ConPort Authority**: Confirmed as an HTTP-first write interface in [enhanced_server.py](file:///Users/hue/code/dopemux-mvp/docker/mcp-servers/conport/enhanced_server.py).
- **OBSERVED: EventBus Model**: `Event` dataclass with `type`, `data`, `source`, `timestamp` in `event_bus.py`.
- **OBSERVED: Stream Naming**: Redis stream `dopemux:events` used for cross-service signaling.
- **OBSERVED: Dope-Memory**: `compose.yml` defines `dope-memory` service with `DOPEMUX_CAPTURE_LEDGER_PATH=/data/chronicle.sqlite`.
- **OBSERVED: State Persistence**: `task_coordinator.py` syncs session state to ConPort via `ConPortEventAdapter`.
- **OBSERVED: Authority**: ConPort (port 3004) is the designated Single Source of Truth for Project State.
- **DOC-CLAIM: Local Storage**: `packets/` directory mentioned in ADRs but not seen in active service usage.

---

## Failure modes

### 1. Cross-Worktree Contamination
- **Invariant**: INV-MEM-001
- **Failure Mode**: Process A (Worktree A) opens `.dopemux/state.db` of Worktree B.
- **Trigger**: CWD mismatch, symlink following, hardcoded paths.
- **Impact**: S0 critical — data corruption, context leakage.
- **Containment**: `repo_preflight.sh` exits 2 on mismatch. SQLite file locking prevents concurrent writes.
- **Refuse Condition**: Strict file locking; if lock held by another PID, STOP immediately (exit 1). Do not wait/spin.

### 2. ConPort Unavailability
- **Invariant**: INV-MEM-002
- **Failure Mode**: ConPort is down during a decision write.
- **Trigger**: PostgreSQL crash, network partition, container OOM.
- **Impact**: S1 high — decisions made but not recorded.
- **Containment**: Queue writes, retry with backoff. If queue exceeds threshold, halt operation.
- **Refuse Condition**: If a Mandate requires ConPort persistence and ConPort is unreachable after retries, STOP.

### 3. Ledger Mutation
- **Invariant**: INV-MEM-003
- **Failure Mode**: A code path issues UPDATE or DELETE against the events table.
- **Trigger**: Bug in migration, manual DB edit, admin tool misuse.
- **Impact**: S0 critical — audit trail destroyed, replay becomes unreliable.
- **Containment**: Schema triggers blocking UPDATE/DELETE. Backup snapshots.
- **Detection**: CI scan for SQL mutation statements against history tables.

### 4. Stale Reads
- **Invariant**: INV-MEM-007
- **Failure Mode**: Supervisor reads cached file content that has changed on disk.
- **Trigger**: External editor modifying files during a plan cycle.
- **Impact**: S2 medium — decisions based on stale data.
- **Containment**: mtime check before/after read. Force refresh on change.
- **Refuse Condition**: If mtime changes during read/plan cycle, STOP and refresh.

### 5. Database Corruption
- **Invariant**: INV-MEM-008
- **Failure Mode**: `state.db` is malformed (zero bytes, half-written page).
- **Trigger**: Kill -9 during write, disk full, filesystem corruption.
- **Impact**: S0 critical — process cannot operate.
- **Containment**: Integrity check on startup. No auto-repair.
- **Refuse Condition**: If `PRAGMA integrity_check` fails, STOP. Require `dmux repair-state`.

---

## Enforcement surface summary

| Invariant   | Enforcement Point   | Mechanism                               | Automated?                 |
| ----------- | ------------------- | --------------------------------------- | -------------------------- |
| INV-MEM-001 | `repo_preflight.sh` \| `.repo_id` match, exit 2                | Yes                        |
| INV-MEM-001 | `scripts/taskx`     \| `.taskxroot` check, exit 2              | Yes                        |
| INV-MEM-002 | `compose.yml`       \| `depends_on: service_healthy`           | Yes                        |
| INV-MEM-002 | Runtime             | Fail on ConPort write failure           | Yes                        |
| INV-MEM-003 | Schema              | No UPDATE/DELETE on `events`            | Partially (needs triggers) |
| INV-MEM-004 | Runtime             | `source_event_id` required on promotion | FUTURE                     |
| INV-MEM-005 | Runtime             | Regex scrubber on writes                | FUTURE                     |
| INV-MEM-006 | Schema/Runtime      | State machine enforcement               | Partially                  |
| INV-MEM-007 | Runtime             | mtime comparison                        | FUTURE                     |
| INV-MEM-008 | Startup             | `PRAGMA integrity_check`                | FUTURE                     |

---

## Degradation ladder

| Level                | Condition                   | Behavior                                                                    |
| -------------------- | --------------------------- | --------------------------------------------------------------------------- |
| L0: Nominal          | All stores healthy          | Full operation                                                              |
| L1: Cache Miss       | Redis down                  | Continue without cache, slower but correct                                  |
| L2: ConPort Degraded | ConPort slow (>5s)          | Queue writes, warn operator                                                 |
| L3: ConPort Down     | ConPort unreachable         | Refuse authority-requiring operations; read-only mode for non-authority ops |
| L4: State DB Corrupt | Integrity check fails       | Full stop. Require `dmux repair-state`                                      |
| L5: Identity Crisis  | `.repo_id` missing/mismatch | Refuse all operations (exit 2)                                              |

---

## Determinism guarantees

- **Session ID**: Generated from `{timestamp}_{random_suffix}`. Not deterministic across runs (intentional — each run is unique).
- **Event ordering**: Events within a session are ordered by insertion time. SQLite's `rowid` provides strict ordering.
- **Replay**: Given the same `state.db` snapshot, reading events produces identical results. The ledger is the replay source.
- **Promotion**: Deterministic given the same raw events. Re-running promotion on the same ledger prefix produces identical promoted content.

---

## Contradiction analysis

| Claim                                | Source                         | Status                                                             |
| ------------------------------------ | ------------------------------ | ------------------------------------------------------------------ |
| `.repo_id` enforces isolation        \| `repo_preflight.sh`            | CONFIRMED — script exits 2 on mismatch                             |
| ConPort is authority                 | Architecture docs, compose.yml | CONFIRMED — task-orchestrator depends_on conport                   |
| `packets/` directory is active       \| ADR references                 \| UNCONFIRMED — no active service references `packets/` directory    |
| `state.db` uses append-only triggers | Design doc                     | UNCONFIRMED — schema defined but triggers not observed in code     |
| Redaction rules exist                | Design doc                     | FUTURE — `config/security/redaction_rules.json` does not exist yet |

---

## State taxonomy

### Ephemeral
- **Session State**: In-memory Python objects during a Supervisor run (loaded context, current prompt buffer).
- **Focus Window State**: Short-lived timers or counters for the current 25-minute block.
- **Transient Caches**: `/tmp/dopemux/cache/` for large tool outputs or intermediate diffs. Cleared on reboot or explicit `dmux clean`.

### Workspace (per-worktree)
- **Workspace Identity**: `.repo_id` file containing `project=dopemux-mvp`, `owner=hu3mann`.
- **Local State Store**: `.dopemux/state.db` (SQLite) containing:
- Session history (prompts/responses).
- Local usage limits and quotas.
- Checkpoint metadata.
- **Per-worktree Memory Views**: `.dopemux/memory/` containing summarized context files.
- **Chronicle Ledger**: `.dopemux/chronicle.sqlite` (via dope-memory service).

### Project (per repo)
- **Canonical Repo-level Stores**: `docs/planes/` (PM/Arch/Eng/Compliance).
- **ConPort**: PostgreSQL AGE database (port 5432) exposed via MCP (port 3004) tracking decisions, risks, and packets.
- **Shared Read Paths**: Config files in `config/` checked into git.

### Global (rollups)
- **Cross-repo Summaries**: `~/.dopemux/global/stats.db` (optional).
- **Usage Aggregation**: Aggregated token costs across all projects (if enabled).

## ConPort as memory authority
ConPort is the "Constitution and Port" of the project. If it's not in ConPort, it didn't formally happen.

- **Decisions**: ADRs stored in `docs/decisions/`.
- **Progress**: Task Packets with status (DRAFT, APPROVED, COMPLETED).
- **Links**: `00_INDEX.md` files serving as entry points.
- **Provenance**: Traceability of *why* a change was made (linked to a Packet ID).

**Minimum Required ConPort Records for a Run**:
1. **Packet ID**: Every run must be associated with a valid Packet ID.
1. **Result State**: Success, Failure, or Refusal.
1. **Artifact List**: Files modified or created.

## Session Context SQLite usage
**Path**: `.dopemux/state.db`

**Schema (Draft)**:
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    status TEXT CHECK(status IN ('CREATED','ACTIVE','COMPLETED','FAILED','KILLED')),
    packet_id TEXT
);

CREATE TABLE events (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    type TEXT, -- 'tool_call', 'user_input', 'model_output', 'warning', 'promotion'
    payload TEXT, -- JSON (scrubbed for secrets before insert)
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);

-- INV-MEM-003 enforcement: prevent history mutation
CREATE TRIGGER prevent_event_update
BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'INV-MEM-003: events table is append-only');
END;

CREATE TRIGGER prevent_event_delete
BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'INV-MEM-003: events table is append-only');
END;
```

**Lifecycle**:
- **Write**: Supervisor writes events synchronously as they happen.
- **Read**: Supervisor reads recent events to build context window for the next turn.
- **Archive**: Old sessions are pruned or archived to flat files after N days (default: 30).

## Rollup index contract
- **What is Promoted**: High-level status changes, new ADRs, major milestone completions.
- **What is NEVER Promoted**: Raw tool outputs, massive diffs, debug logs, chatter.
- **When Promotion Happens**: At the successful completion of a Task Packet.
- **Attribution**: Promotion is an *interpretation* event (INV-MEM-004).

## Redaction and safety boundaries
- **Never Persist**: API Keys / Secrets, PII (emails, phone numbers) unless explicitly whitelisted.
- **Sensitive Fields**: `payload` in SQLite must be scrubbed before insert (INV-MEM-005).
- **Operator Controls**: `dmux purge --session <id>` aggressively deletes all traces.

## Open questions
- **Global Rollups**: How do we aggregate multi-repo stats without breaking isolation?
- *Resolution*: Define a separate "Observer" plane that reads-only from multiple approved roots.
- **Secret Redaction**: What is the exact regex list for redaction?
- *Resolution*: `config/security/redaction_rules.json` (to be created).
- **Global Search**: How do we search across all worktrees if ConPort is isolated?
- *Resolution*: `dope-context` (3010) supports multi-repo indexing via Qdrant/Voyage. Verify multi-tenant segregation.

## Acceptance criteria
1. **Isolation Test**: Spawn two shells in different repo roots. Ensure `dopemux run` in one does not affect the `.dopemux/state.db` of the other.
1. **Persistence Test**: Run a packet, kill the process, restart. Ensure session history up to the kill point is preserved in SQLite.
1. **Refusal Test**: Manually lock the `state.db` (e.g., via `sqlite3` shell). Attempt to run Dopemux. It must exit with a clear "Database Locked" error, not hang.
1. **Integrity Test**: Corrupt `state.db` (truncate to 100 bytes). Start Dopemux. It must refuse with "integrity check failed" and not attempt auto-repair.
1. **Append-Only Test**: Attempt `UPDATE events SET payload='hacked' WHERE id='evt-1'`. SQLite trigger must reject with INV-MEM-003 message.
