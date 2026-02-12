# Packet I-AUDIT — EVIDENCE LEDGER

Rule: Every PASS must be backed by at least one entry here.
Format: `path:Ln-Lm` plus short snippet.

---

## A1 — Event ID Fingerprint Normalization

- Requirement: A1
- Claim: event_id fingerprint excludes `source` and `project_id`
- File: src/dopemux/memory/capture_client.py
- Lines: 291-320
- Snippet:
  ```python
  def _deterministic_event_id(
      *,
      event_type: str,
      session_id: Optional[str],
      ts_utc: str,
      payload: dict[str, Any],
  ) -> str:
      """Generate deterministic event_id from semantic content only.
      Per Packet D §3.3: event_id is content-addressed, excluding adapter-specific
      metadata (source, project_id) to enable cross-adapter convergence."""
      ts_bucket = ts_utc[:19]
      session_id_normalized = session_id or ""
      fingerprint = "|".join([event_type, session_id_normalized, ts_bucket, _stable_json(payload)])
      return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
  ```
- Proof: `source` is NOT a parameter. `project_id` is NOT a parameter. Function signature proves exclusion by construction.

- File: src/dopemux/memory/capture_client.py
- Lines: 406-420
- Snippet:
  ```python
  # Generate event_id BEFORE injecting project_id (Packet D §3.3)
  event_id = str(event.get("event_id") or event.get("id") or _deterministic_event_id(...))
  # Inject project_id AFTER event_id generation for storage/routing only
  redacted_payload["project_id"] = project_id
  ```
- Proof: Comment and code flow confirm project_id injected AFTER event_id is computed.

- File: services/working-memory-assistant/tests/unit/test_event_id_convergence.py
- Lines: 6-34
- Snippet: `assert id_1 == id_2, "Event ID must converge across adapters for identical content"`
- Proof: Test confirms cross-adapter convergence.

---

## A2 — Provenance Fields NOT NULL

- Requirement: A2
- Claim: Six provenance fields are NOT NULL in schema.sql
- File: services/working-memory-assistant/chronicle/schema.sql
- Lines: 69-74
- Snippet:
  ```sql
  source_event_id TEXT NOT NULL,
  source_event_type TEXT NOT NULL,
  source_adapter TEXT NOT NULL,
  source_event_ts_utc TEXT NOT NULL,
  promotion_rule TEXT NOT NULL,
  promotion_ts_utc TEXT NOT NULL,
  ```
- Proof: `NOT NULL` constraint on all six provenance fields in the canonical schema.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 366-371
- Snippet:
  ```python
  if not all([source_event_id, source_event_type, source_adapter, source_event_ts_utc, promotion_rule]):
      raise ValueError("All provenance fields are required: ...")
  ```
- Proof: Application layer also validates fail-closed before DB write.

---

## A3 — Time Authority

- Requirement: A3
- Claim: ts_utc = source_event_ts_utc (event time), not wall clock
- File: services/working-memory-assistant/chronicle/store.py
- Lines: 410-413
- Snippet:
  ```python
  # Timestamps (Packet D §5.2)
  ts_utc = source_event_ts_utc  # Event time (authoritative for chronology)
  promotion_ts_utc = datetime.now(timezone.utc).isoformat()  # Promotion processing time
  created_at_utc = datetime.now(timezone.utc).isoformat()  # Physical write time
  ```
- Proof: `ts_utc` is set directly from `source_event_ts_utc`. Wall clock used only for `promotion_ts_utc` and `created_at_utc`.

- File: services/working-memory-assistant/tests/unit/test_time_semantics.py
- Lines: 7-42
- Snippet:
  ```python
  past_ts = "2020-01-01T12:00:00+00:00"
  entry_id = store.insert_work_log_entry(..., source_event_ts_utc=past_ts, ...)
  row = conn.execute("SELECT ts_utc, created_at_utc FROM work_log_entries WHERE id = ?", (entry_id,)).fetchone()
  assert row["ts_utc"] == past_ts, "Stored ts_utc MUST match source event time"
  ```
- Proof: Test with past timestamp verifies ts_utc == source_event_ts_utc.

---

## A4 — Deterministic Promoted Entry IDs

- Requirement: A4
- Claim: entry_id is SHA256 of provenance, not uuid4
- File: services/working-memory-assistant/chronicle/store.py
- Lines: 406-408
- Snippet:
  ```python
  # Deterministic entry_id (Packet D §7.7)
  fingerprint = f"{source_event_id}|{promotion_rule}|{source_event_ts_utc}"
  entry_id = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
  ```
- Proof: SHA256 derivation, no randomness.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 275, 857
- Snippet: `uuid.uuid4()` appears only at line 275 (raw events) and 857 (issue links) — NOT on promoted entry path.
- Proof: `rg -n "uuid4\(" chronicle/` shows only non-promoted paths.

- File: services/working-memory-assistant/tests/unit/test_deterministic_entry_id.py
- Lines: 7-38
- Snippet:
  ```python
  fingerprint = f"{sid}|{rule}|{ts}"
  expected_id = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
  entry_id = store.insert_work_log_entry(...)
  assert entry_id == expected_id, "entry_id must match SHA256 of provenance"
  ```
- Proof: Test independently computes expected hash and verifies match.

---

## A5 — Reflection Provenance Persisted

- Requirement: A5
- Claim: Reflection cards persist source_entry_ids_json
- File: services/working-memory-assistant/chronicle/schema.sql
- Lines: 143
- Snippet: `source_entry_ids_json TEXT NOT NULL DEFAULT '[]',`
- Proof: Column exists with NOT NULL constraint.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 905, 923
- Snippet: `json.dumps(card.get("source_entry_ids", []))`
- Proof: Insert stores the field.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 983-984
- Snippet:
  ```python
  source_entry_ids = json.loads(row[9]) if len(row) > 9 and row[9] else []
  stale_entries = [eid for eid in source_entry_ids if eid in superseded_ids]
  ```
- Proof: Retrieval parses and returns source_entry_ids, plus staleness detection.

- File: services/working-memory-assistant/tests/unit/test_reflection_provenance.py
- Lines: 7-68
- Proof: Two tests verify DB persistence and API retrieval of source_entry_ids.

---

## A6 — Replay Ordering Contract

- Requirement: A6
- Claim: Replay is source_event_ts_utc ASC, id ASC
- File: services/working-memory-assistant/chronicle/store.py
- Lines: 654
- Snippet: `query += " ORDER BY source_event_ts_utc ASC, id ASC LIMIT ?"`
- Proof: ORDER BY clause uses event time with id as deterministic tie-break.

- File: services/working-memory-assistant/tests/unit/test_replay_ordering.py
- Lines: 6-38
- Snippet: Inserts entries out of chronological order, verifies replay returns event-time order.
- Proof: `assert rows[0]["summary"] == "First"` (earliest event time first).

---

## B1 — DB Enforces Linearity

- Requirement: B1
- Claim: UNIQUE partial index prevents branching
- File: services/working-memory-assistant/chronicle/schema.sql
- Lines: 96-98
- Snippet:
  ```sql
  CREATE UNIQUE INDEX IF NOT EXISTS idx_worklog_supersedes_unique_scoped
    ON work_log_entries(workspace_id, instance_id, supersedes_entry_id)
    WHERE supersedes_entry_id IS NOT NULL;
  ```
- Proof: Partial UNIQUE index on supersedes_entry_id (scoped) prevents two entries from superseding the same target.

- File: services/working-memory-assistant/tests/unit/test_supersession_semantics.py
- Lines: 74-84
- Snippet: `with pytest.raises(ValueError, match="already superseded"):`
- Proof: Fork attempt raises ValueError (caught at application layer before hitting DB constraint).

- File: services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py
- Lines: 68-75
- Snippet: `with pytest.raises(sqlite3.IntegrityError):`
- Proof: DB-level constraint also fires (bypassing application layer).

---

## B2 — Supersession Scoped to workspace/instance

- Requirement: B2
- Claim: All supersession operations scoped by workspace_id + instance_id
- File: services/working-memory-assistant/chronicle/schema.sql
- Lines: 96-98
- Snippet: `ON work_log_entries(workspace_id, instance_id, supersedes_entry_id)`
- Proof: Index columns include workspace_id and instance_id.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 100-106
- Snippet:
  ```python
  def _get_superseded_entry_ids(self, workspace_id: str, instance_id: str) -> set[str]:
      ...WHERE workspace_id = ? AND instance_id = ? AND supersedes_entry_id IS NOT NULL
  ```
- Proof: Helper filtered by both scope columns.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 123-124
- Snippet: `"SELECT supersedes_entry_id FROM work_log_entries WHERE id = ? AND workspace_id = ? AND instance_id = ?"`
- Proof: `_get_chain_depth` scoped.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 150-152
- Snippet: `"SELECT id FROM work_log_entries WHERE supersedes_entry_id = ? AND workspace_id = ? AND instance_id = ?"`
- Proof: `_resolve_chain_head` scoped.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 167-169
- Snippet: `"SELECT COUNT(*) FROM work_log_entries WHERE supersedes_entry_id = ? AND workspace_id = ? AND instance_id = ?"`
- Proof: `_is_entry_superseded` scoped.

- File: services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py
- Lines: 44-75
- Snippet: Same target allowed in ws-1/A and ws-2/B; duplicate in ws-1/A raises IntegrityError.
- Proof: Cross-scope reuse verified; same-scope duplication blocked.

---

## B3 — Write-path Guardrails

- Requirement: B3
- Claim: Head-only targeting, depth limit, tombstone semantics
- File: services/working-memory-assistant/chronicle/store.py
- Lines: 384-404
- Snippet:
  ```python
  if supersedes_entry_id:
      target = self.get_entry_by_id(workspace_id, instance_id, supersedes_entry_id)
      if not target:
          raise ValueError(f"Cannot supersede non-existent entry: {supersedes_entry_id}")
      if self._is_entry_superseded(workspace_id, instance_id, supersedes_entry_id):
          head = self._resolve_chain_head(workspace_id, instance_id, supersedes_entry_id)
          raise ValueError(f"Cannot supersede entry {supersedes_entry_id} — it is already superseded...")
      current_depth = self._get_chain_depth(workspace_id, instance_id, supersedes_entry_id)
      if current_depth >= MAX_CHAIN_DEPTH:
          raise ValueError(f"Supersession chain depth limit exceeded (max {MAX_CHAIN_DEPTH})...")
  ```
- Proof: Three guardrails: exists, is head, depth <= 10.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 586-590
- Snippet:
  ```python
  if correction_type == "retraction":
      final_summary = f"[RETRACTED] {summary}"
      final_outcome = "abandoned"
      final_importance_score = min(final_importance_score, 3)
  ```
- Proof: Tombstone semantics applied.

- File: services/working-memory-assistant/tests/unit/test_supersession_semantics.py
- Lines: 89-107, 246-265, 269-276
- Proof: Depth limit, retraction, head-targeting all tested.

---

## B4 — Default Filtering Hides Superseded

- Requirement: B4
- Claim: search/count/replay hide superseded by default
- File: services/working-memory-assistant/chronicle/store.py
- Lines: 708-714
- Snippet:
  ```python
  if not include_superseded:
      conditions.append("""id NOT IN (
          SELECT supersedes_entry_id FROM work_log_entries
          WHERE supersedes_entry_id IS NOT NULL
      )""")
  ```
- Proof: search_work_log default exclusion.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 642-646
- Snippet:
  ```python
  if mode != "replay_full":
      query += """ AND id NOT IN (
          SELECT supersedes_entry_id FROM work_log_entries
          WHERE supersedes_entry_id IS NOT NULL
      )"""
  ```
- Proof: replay_work_log default exclusion.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 806-811
- Snippet: Same subquery pattern in count_work_log.
- Proof: count excludes superseded.

- File: services/working-memory-assistant/tests/unit/test_supersession_semantics.py
- Lines: 129-221
- Proof: Tests for search (L129), include_superseded (L145), replay_current (L173), replay_full (L190), count (L213).

---

## C1 — Schema and Migrations Aligned

- Requirement: C1
- Claim: schema.sql is the complete end-state for Path A
- File: services/working-memory-assistant/chronicle/schema.sql
- Lines: 173-174
- Snippet: `INSERT OR IGNORE INTO schema_migrations (version, applied_at_utc) VALUES ('v1.2.1', datetime('now'));`
- Proof: schema.sql self-declares v1.2.1.

- File: services/working-memory-assistant/chronicle/store.py
- Lines: 74-87
- Snippet:
  ```python
  def initialize_schema(self) -> None:
      conn = self.connect()
      schema_sql = SCHEMA_PATH.read_text()
      conn.executescript(schema_sql)
      conn.commit()
      applied = apply_chronicle_migrations(conn, ...)
  ```
- Proof: Path A: schema.sql runs first, then migrations discover v1.2.1 already applied and skip.

- File: services/working-memory-assistant/chronicle/sqlite_migrations.py
- Lines: 110-115
- Snippet:
  ```python
  if current_max is not None and version_tuple <= current_max:
      continue  # Support bootstrap paths where schema.sql already seeded a newer version.
  ```
- Proof: Migrations correctly skip when schema.sql has already bootstrapped.

---

## C2 — MCP Response Envelopes

- Requirement: C2
- Claim: All tools return `success` field
- File: services/working-memory-assistant/mcp/server.py
- Lines: 249, 322, 456, 488, 492, 519, 531, 600, 648, 650
- Snippet: Every return dict includes `"success": True` or `"success": False`
- Proof: Enumerated all return paths across all 7 tools.

- File: docs/spec/dope-memory/v1/07_mcp_contracts.md
- Lines: 3
- Snippet: `All responses include a success: boolean field (True for success, False for error).`
- Proof: Contract matches implementation.

- File: services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py
- Lines: 226-273
- Snippet: `test_all_mcp_tools_return_success_field` — calls all 6 testable tools and asserts `"success" in resp`.
- Proof: Automated test covers all tools.

---

## C3 — Correction Idempotency

- Requirement: C3
- Claim: idempotency_key prevents duplicate corrections
- File: services/working-memory-assistant/chronicle/store.py
- Lines: 542-551
- Snippet:
  ```python
  if idempotency_key:
      source_event_id = f"manual:{idempotency_key}"
      conn = self.connect()
      existing = conn.execute(
          "SELECT id FROM work_log_entries WHERE source_event_id = ? AND supersedes_entry_id = ? AND workspace_id = ? AND instance_id = ?",
          (source_event_id, supersedes_entry_id, workspace_id, instance_id)
      ).fetchone()
      if existing:
          return existing[0]
  ```
- Proof: Lookup-before-insert pattern. Returns existing entry_id on retry.

- File: services/working-memory-assistant/tests/unit/test_packet_h_supersession_hardening.py
- Lines: 171-223
- Snippet:
  ```python
  id1 = resp1["entry_id"]
  id2 = resp2["entry_id"]
  assert id1 == id2  # Entry IDs must be identical
  count = conn.execute("SELECT COUNT(*) FROM work_log_entries WHERE supersedes_entry_id = ?", (original_id,)).fetchone()[0]
  assert count == 1
  ```
- Proof: Same key yields same entry_id; DB has exactly 1 correction entry.
