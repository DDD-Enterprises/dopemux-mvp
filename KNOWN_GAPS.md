# Known Gaps

This file documents explicitly deferred or stub implementations — features partially
wired but not fully operational.  Each entry records *what* is incomplete, *why* it
was deferred (scope, risk, or dependency), and *what* a future implementer must do.

Entries are added as stubs are discovered and audited; they are NOT bugs unless marked
`[BUG]`.  Completing an entry means: implement the missing behavior, add/extend tests,
update or remove this entry, and record the decision in ConPort.

---

## RTE — Repo Truth Extractor

### KG-RTE-01 — S7: truth-split per-step comparison not wired
**Status:** Deferred  
**File:** `services/repo-truth-extractor/validate_pre_live_gate_v25.py`  
**Function:** `collect_truth_split`  
**Description:** `collect_truth_split` fail-closes with a waivable P1 blocker
(`TRUTH_SPLIT_NOT_IMPLEMENTED`) rather than performing the real per-step
source-vs-extraction comparison.  The downstream `classify_truth_split_row` wiring
and diff generation are not implemented.  
**Why deferred:** Requires access to both the prescan output and the live extraction
result in the same validation pass; runtime plumbing not yet available.  
**To implement:** Wire `classify_truth_split_row` to compare prescan vs extraction
at each pipeline step; emit per-row pass/fail into the gate report; remove the
`TRUTH_SPLIT_NOT_IMPLEMENTED` stub and the associated waiver path.

---

### KG-RTE-02 — S8-002: extraction_hygiene policy YAML unwired
**Status:** Deferred  
**File:** `services/repo-truth-extractor/extraction_hygiene.py`  
**Description:** The extraction hygiene policy is hardcoded inside the module.
The canonical `config/extraction_hygiene/*.yaml` configuration files are documented
but not loaded at runtime; changes to hygiene rules require code edits rather than
config changes.  
**Why deferred:** Config-loading plumbing not prioritised in the current sprint.  
**To implement:** Load the YAML config at startup (or lazily on first use); merge with
or replace the hardcoded defaults; add a schema / validation pass for the YAML shape.

---

### KG-RTE-03 — S2: `required_prompt_sections` declared but unenforced
**Status:** Deferred  
**File:** `services/repo-truth-extractor/run_extraction_v4.py` (`load_promptset`)  
**Description:** `required_prompt_sections` is declared in the promptset schema and
the "Legacy Context" guardrail is documented, but neither is enforced at runtime.
A promptset missing required sections is loaded without error.  
**Why deferred:** Enforcement adds complexity to the promptset loader; deferred to
a dedicated promptset-validation task.  
**To implement:** Validate loaded promptsets against `required_prompt_sections`;
raise a clear error (or structured warning) when a section is absent; add tests.

---

## MCP / Integration Bridge

### KG-MCP-01 — MCP2-05: `str(e)` info disclosure in HTTP error details
**Status:** Deferred (low severity — no secrets exposed in current paths)  
**Files:** ~9 sites in `services/mcp-integration-bridge/main.py` that include
`str(e)` or `repr(e)` in HTTP 4xx/5xx response bodies.  
**Description:** Exception messages forwarded to HTTP clients can leak internal
path names, module names, or partial stack traces.  In current code paths no
credentials or secrets appear in exception strings, making this an info-disclosure
risk rather than a credential-exposure risk.  
**Why deferred:** Fixing requires auditing all ~9 sites and deciding on a
sanitisation strategy (generic message vs structured error code); deferred to a
dedicated security hardening task.  
**To implement:** Replace `str(e)` in HTTP response bodies with a generic user-facing
message; log the full exception server-side at ERROR level; assign error codes to
allow clients to react programmatically without needing the raw message.

---

### KG-MCP-02 — Broker `request_escalation` has no transport
**Status:** Deferred  
**File:** `src/dopemux/mcp/broker.py` (`request_escalation`)  
**Description:** `request_escalation` constructs an `EscalationRequest` and returns
`approval_required=True` in the response, but there is no mechanism to actually
notify an operator or record the pending approval anywhere (no webhook, no ConPort
entry, no queue message).  Callers receive `approval_required=True` and must poll
or retry indefinitely with no signal that the approval was handled.  
**Why deferred:** Transport layer (webhook URL, ConPort hook, or Redis queue) not
yet decided.  
**To implement:** Choose a transport; implement `notify_approver(escalation_request)`;
persist the pending escalation (e.g. ConPort `log_custom_data` with category
`"pending_escalations"`); add a complementary `approve_escalation` / `deny_escalation`
MCP tool or REST endpoint; add expiry / timeout logic.

---

## RTE — Phases

### KG-RTE-04 — Orphan phase "M" documented but not wired or removed
**Status:** Deferred  
**File:** `services/repo-truth-extractor/phases.py`  
**Description:** Phase "M" (merge / consolidation pass) is described in the module
docstring and phase registry but has no implementation.  It is never scheduled by
the phase runner.  This creates documentation drift — operators reading `phases.py`
expect a merge pass that does not execute.  
**Why deferred:** Scope for the merge pass is undefined; removal vs implementation
decision deferred.  
**To implement:** Either (a) implement the merge pass and wire it into the phase
runner, or (b) remove the phase "M" registry entry and documentation reference and
add a comment explaining why it was removed.  Either way, update `phases.py` and
any docs that reference it.
