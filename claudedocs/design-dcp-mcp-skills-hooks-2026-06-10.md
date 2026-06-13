# Deep Design: DCP + MCP Skills & Hooks

**Date**: 2026-06-10
**Author**: Claude (Fable 5) — design only; implementation assigned to Sonnet
**Status**: DESIGN_READY — verified against `origin/main` @ `06f3344b6`
**Scope**: 5 skills (`/proof:bundle`, `/mcp:doctor`, `/dcp:doctor`, `/dcp:denylist-check`, `/tp:validate`) + 4 hooks (surface guard, denylist nudge, MCP health preflight, proof-tracking guard)

---

## 0. Ground Truth This Design Is Built On (verified 2026-06-10)

| Fact | Evidence |
|---|---|
| All 11 lifecycle events route through one dispatcher | `.claude/settings.json` → `src/dopemux/claude/native_hooks.py` (`NativeHookAdapter.handle_event`, line 253) |
| Helper-module pattern: try-import from `.claude/hooks/` with no-op fallbacks | `native_hooks.py:30-53` |
| `src/` is on `sys.path` inside the dispatcher (`CORE_DIR`) | `native_hooks.py:17-20` — `dopemux.dcp.*` is importable from hooks |
| Hard-block mechanism exists: `_deny_tool(message, additional_context)` → exit 2 + `permissionDecision: deny` | `native_hooks.py:211-221` |
| Advisory mechanism: `_allow(additional_context=...)` with `hookEventName` | `native_hooks.py:194-209` |
| Red-lane scanner has a CLI as of TP-DMX-DCP-SEAM-ENFORCEMENT-001: `PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner --repo-root . --files <f>...` — exit 0=PASS, 1=BLOCKED/UNKNOWN/CONFLICTING (fail-closed) | `task-packets/development-factory/TP-DMX-DCP-SEAM-ENFORCEMENT-001.md` (on main) |
| `FORBIDDEN_PATHS` constant exists | `src/dopemux/dcp/red_lane_rules.py:15` |
| Proof tracking policy: sanitized proof MUST be committed via `git add -f`; blanket `proof/*` gitignore stays as safety net | `task-packets/development-factory/TP-DMX-PROOF-TRACKING-POLICY-001.md` (on main) |
| Proof validator exists and runs in CI: `scripts/audit/validate_audit_proof.py --all proof/` | `.github/workflows/ci-complete.yml:475` |
| Proof scaffold script exists: `scripts/proof_bundle.sh --tp <ID> [--cmd ...]` | `scripts/proof_bundle.sh` |
| embedded_audit schema exists; rejects `none`/`unknown` auditor combos | `schemas/proof/embedded_audit.schema.json` + commit `93fc168fd` |
| `dopemux mcp doctor` CLI exists: env-var + port-listening + stdio checks for servers declared in worktree `.mcp.json` | `src/dopemux/commands/mcp_commands.py:814-876` |
| `mcp_catalog.yaml` is single source of truth for server scope/transport/ports/compose-service | `mcp_catalog.yaml` header |
| DCP facade route allow/deny data: `ALLOWED_ROUTES`, `DENIED_ROUTES`, `DENIED_TOKENS` (data-only module) | `services/dcp-readonly-facade/src/dcp_facade/route_manifest.py` |
| Orchestrator **already enforces** the proof-bundle complete-gate server-side (required notes / `canAdvance`) | `.claude/commands/dx/complete.md` Phase 2b |
| Task-orchestrator stdio launcher leaks per-client containers under churn; `docker kill <id>` (single-id) is the working prune on Docker Desktop 29.4.1; batched `stop`/`rm -f` 404 | operator memory, POC-verified 2026-05-31 |
| ConPort auto-fork hazard: `GET /api/progress` writes unless `DOPEMUX_AUTO_FORK_PROGRESS=0`; facade fail-closes unless registry sets `progress_readonly_safe: true` | `docs/03-reference/dcp/chatgpt-mcp-readonly/FACADE_LOCAL_RUN.md` §5 |
| dope-context adapter is BLOCKED in Phase 1 (MCP JSON-RPC vs REST transport gap) — expected, not a fault | `proof/TP-DCP-MCP-RO-0006/AUDIT.md` §A |
| Hook tests live flat in `tests/` (`test_orchestrator_hooks.py`, `test_native_hooks_workflow.py`, `test_orchestrator_enforcement_hooks.py`) | repo listing |
| dx-command authoring reference | `docs/03-reference/dx-command-authoring.md` |
| No JSON schema exists for task packets (`schemas/` has no task-packet entry); `.md` packets are frontmatter-validated by pre-commit (`docs_frontmatter_guard.py`, `docs_validator.py`) | repo listing + `.pre-commit-config.yaml` |

**Design invariants (apply to every item below):**

1. **Fail-open for advisories, fail-closed only for red lanes.** Helper functions never raise; a crashed helper must not block work (mirror `orchestrator_enforcement.py` docstring contract: "All functions are pure and never raise").
2. **No new settings.json hook entries.** All four hooks are new helper modules in `.claude/hooks/` wired into the existing dispatcher's try-import block. `settings.json` is untouched.
3. **Wrap existing tools, never reimplement.** Red-lane scanner CLI, `dopemux mcp doctor`, `validate_audit_proof.py`, `proof_bundle.sh`, `route_manifest.py` are the canonical engines; skills orchestrate them.
4. **ADHD output discipline**: max 3 surfaced problems before "… N more"; one clear next action per failure; PASS/FAIL/NOT_RUN buckets, never collapsed.
5. **DCP-RED-MERGE-SEAM-0001 is never lifted, relaxed, or bypassed** by anything in this design.
6. Skills are markdown command files under `.claude/commands/<ns>/<name>.md` (namespace dir → `/<ns>:<name>`), matching the `dx/` pattern and `docs/03-reference/dx-command-authoring.md`.

**Implementation order** (each is an independent slice; suggested packets in §10):

1. H4 proof-tracking guard + S1 `/proof:bundle` (closes the documented silent-drop failure)
2. S2 `/mcp:doctor` + H3 MCP health preflight (kills the recurring leaked-container pain)
3. H1 surface guard (red-lane enforcement at edit time)
4. S3 `/dcp:doctor` + S4 `/dcp:denylist-check` + H2 denylist nudge (lands with packets 0007/0008)
5. S5 `/tp:validate` (smallest, last)

---

## 1. S1 — `/proof:bundle` (skill)

### Objective
One command surface for the proof-bundle lifecycle: **scaffold → validate → track**. Wraps `scripts/proof_bundle.sh`, `scripts/audit/validate_audit_proof.py`, and the TP-DMX-PROOF-TRACKING-POLICY-001 force-add policy. Closes the gap where AGENTS.md §9 requires ~13 proof fields but nothing checks them until CI (or never, for untracked proof).

### File
`.claude/commands/proof/bundle.md` → invoked as `/proof:bundle`

### Frontmatter
```yaml
---
description: "Scaffold, validate, or force-track a proof bundle (AGENTS.md §9 + TP-DMX-PROOF-TRACKING-POLICY-001)"
arguments: "<scaffold|validate|track> <TP-ID> [--strict]"
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
model: "claude-sonnet-4-5"
---
```

### Behavior

**Phase 1 — argument parsing.** First positional → mode (`scaffold` | `validate` | `track`). Second → `TP-ID` (required; if omitted, glob `proof/*/` modified in the last 24h and offer max 3 candidates). `--strict` → treat WARN as FAIL (for pre-PR use).

**Phase 2 — mode `scaffold`:**
1. Refuse if `proof/<TP-ID>/PROOF.json` already exists (point at `validate` instead). Never overwrite proof — proof is append-only evidence.
2. Collect git facts: `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, `git rev-parse --show-toplevel`, `git status --porcelain` (dirty list), `git diff --stat <merge-base origin/main>..HEAD`.
3. Write `proof/<TP-ID>/PROOF.json` skeleton pre-filled with: `tp_id`, `tp_path` (resolve from `task-packets/**/<TP-ID>.{md,json}` via Glob), `branch`, `head_sha`, `worktree_path`, `repo_identity` (origin URL), `files_changed` (from diff-stat), and empty-but-present keys for every AGENTS.md §9 field: `slices`, `validations` (array of `{command, exit_code, bucket}` — bucket ∈ PASS/FAIL/NOT_RUN), `codereview_status`, `precommit_status`, `commit_sha`, `pr_url_or_blocker`, `residual_risks`, `unknowns`, `cleanup_status`, `embedded_audit` (shape per `schemas/proof/embedded_audit.schema.json` — read the schema, don't guess; note it rejects the `none`/`unknown` auditor combo).
4. Write `SUMMARY.md` and `AUDIT.md` stubs (heading skeleton only, marked `NOT_RUN`).
5. Mention `scripts/proof_bundle.sh --tp <TP-ID> --cmd "<validation cmd>"` as the way to capture command transcripts into the bundle (do not duplicate its logic).
6. End with the track-tier reminder: these files are gitignored by `proof/*` until force-added — print the exact `git add -f` line.

**Phase 3 — mode `validate`:**
1. **Schema layer**: `python scripts/audit/validate_audit_proof.py --all proof/<TP-ID>/` — capture exit code. (CI parity: this is the same gate `ci-complete.yml` runs.)
2. **§9 completeness layer** (the gap CI doesn't cover): Read `PROOF.json`; for each §9 field report filled / empty / missing. `validations[]` entries must have integer `exit_code` and a bucket; flag any `NOT_RUN` entry missing a reason.
3. **Staleness layer**: compare `head_sha` in PROOF.json to `git rev-parse HEAD`; mismatch → WARN (same semantics as the DCP facade's stale-proof warning — warn, not block; `--strict` upgrades to FAIL).
4. **Tracking layer**: for each TRACK-tier file present (`PROOF.json`, `SUMMARY.md`, `AUDIT.md`, `MERGE_READINESS.json`, `VALIDATION.md`, `CMD_SUMMARY.md`, `MODEL_ROUTING.json`, `MANIFEST.json`), run `git ls-files --error-unmatch <path>` → untracked = FAIL with the `git add -f` remediation (this is a red line per `docs/03-reference/development-factory/red-lines-and-stop-conditions.md`).
5. Output: single table — layer / check / PASS|FAIL|WARN|NOT_RUN / remediation. Exit summary line suitable for pasting into the bundle's own `VALIDATION.md`.

**Phase 4 — mode `track`:**
1. List `proof/<TP-ID>/` files; partition into TRACK tier vs DO_NOT_TRACK tier using the policy tables in TP-DMX-PROOF-TRACKING-POLICY-001 (raw stdout >50KB, files >1MB, `.env`/secret-looking content, raw LLM transcripts → never track).
2. **Secret pre-scan** before any `git add -f`: grep each TRACK candidate for obvious credential patterns (`sk-`, `AKIA`, `BEGIN.*PRIVATE KEY`, `Bearer [A-Za-z0-9._-]{20,}`); any hit → STOP, report path (not the value), do not stage.
3. Stage TRACK-tier files with `git add -f <paths>`; print what was staged and what was deliberately skipped and why. **Never commits** — staging only; the operator/agent commits per normal flow.

### Tests
- None for the `.md` itself (commands aren't unit-tested in this repo), but the design requires a fixture-level test for the §9 completeness check **if** the implementer extracts it into a script (recommended: `scripts/audit/check_proof_completeness.py` so `/proof:bundle validate` and future CI share one engine; test at `tests/test_proof_completeness.py` with two fixtures — complete and §9-deficient PROOF.json).

### Acceptance criteria
- `scaffold` on a fresh TP-ID produces PROOF.json that passes `validate_audit_proof.py` structurally (or documents exactly which fields legitimately can't be pre-filled).
- `validate` on `proof/TP-DCP-MCP-RO-0006/` (known-good, on main) → all PASS except possibly staleness WARN.
- `track` never stages a file matching the DO_NOT_TRACK table; never prints secret values.
- No mode ever modifies an existing PROOF.json (validate/track are read-only on bundle content).

### Rollback
`rm .claude/commands/proof/bundle.md` (+ the optional script and test if created).

---

## 2. S2 — `/mcp:doctor` (skill)

### Objective
Full-fleet MCP health sweep that **wraps** the existing `dopemux mcp doctor` CLI and adds the three things it doesn't do: leaked-container detection/prune, singleton probing, and compose-service status. This is the operator command for "MCP calls are timing out / dropping."

### File
`.claude/commands/mcp/doctor.md` → `/mcp:doctor`

### Frontmatter
```yaml
---
description: "MCP fleet health: wraps `dopemux mcp doctor`, probes singletons, detects leaked task-orchestrator stdio containers, offers safe prune"
arguments: "[--prune] [--json]"
allowed-tools: ["Bash", "Read", "Grep"]
model: "claude-sonnet-4-5"
---
```

### Behavior

**Phase 1 — declared-server sweep.** Run `dopemux mcp doctor`; capture stdout + exit code verbatim. This covers env vars, port listening, and stdio checks for servers in the worktree's `.mcp.json`. Do not re-derive what it already checks.

**Phase 2 — singleton sweep.** Parse `mcp_catalog.yaml` (Read tool, it's YAML — extract `servers.*` where `scope: singleton`). For each http/sse singleton, probe with a bounded curl:
```bash
curl -s -o /dev/null -w '%{http_code}' --max-time 2 <url-from-catalog>
```
- http transport: POST an MCP `initialize` to `<url>` is overkill for a doctor; a TCP-level/HTTP-level response (any code, incl. 405/406) = "listening". Connection refused/timeout = down.
- `desktop-commander` has a Starlette `/health` endpoint (per catalog description) — use it.
- For each down singleton, the remediation is its `docker_compose_service` from the catalog: `docker compose up -d <service>`.

**Phase 3 — leaked-container sweep** (the headline feature):
```bash
docker ps --format '{{.ID}}\t{{.Names}}\t{{.RunningFor}}' | grep -i 'task-orchestrator' || true
```
- Read `scripts/mcp-wrappers/task-orchestrator-current-stdio.sh` at implementation time to confirm the exact container-name pattern (launcher names containers `…-$$` per operator memory) and encode that pattern in the skill text — **do not guess it in the skill; cite the wrapper as source**.
- Expected population: ≤1 per active MCP client per workspace. Report count; >2 → flag the SQLite-contention spiral by name so the operator recognizes it.
- `--prune`: kill **one id at a time** with `docker kill <id>` (NOT batched `docker stop`/`docker rm -f` — those 404 on Docker Desktop 29.4.1). Skip the newest container (likely the live session's). Without `--prune`, print the exact kill commands but do not run them.

**Phase 4 — compose status.** `docker compose ps --format json` (bounded, may be slow on cold Docker — 10s timeout, report NOT_RUN if exceeded). Cross-reference against the catalog's `docker_compose_service` values. Services in `starting`/`health: starting` → report as **cold-start grace** (BETA-MCP-02 races are known), not failure.

**Phase 5 — report.** One table: server / scope / transport / check performed / status (✅ ⚠️ ❌ NOT_RUN) / one-line fix. Max 3 fix actions listed prominently; remainder collapsed. `--json` mode emits machine-readable output for the statusline or future automation.

### Acceptance criteria
- With the fleet healthy: exits clean, ≤10s wall clock.
- With conport stopped: reports it ❌ with `docker compose up -d conport` as the fix.
- With ≥3 task-orchestrator containers: names the contention spiral and prints per-id kill commands; `--prune` leaves exactly the newest one running.
- Never runs `docker kill` without `--prune`.

### Rollback
`rm .claude/commands/mcp/doctor.md`.

### Note for a follow-up packet (not this slice)
The leaked-container sweep logically belongs inside `dopemux mcp doctor` itself (`mcp_commands.py:814`). Skill-first is deliberate: it validates the check cheaply; promotion into the CLI is a separate packet with its own tests. The durable cure remains the HTTP-singleton transport cutover (POC-verified `MCP_TRANSPORT=http`); this doctor is the mitigation until that cutover packet runs.

---

## 3. S3 — `/dcp:doctor` (skill)

### Objective
Preflight for the DCP read-only facade: registry contract, backend reachability, the ConPort auto-fork hazard, and the facade test suite — the four manual checks in `FACADE_LOCAL_RUN.md` that every facade/tunnel session repeats. This becomes the "manual validation" automation that packet TP-DCP-MCP-RO-0007 (tunnel docs) needs.

### File
`.claude/commands/dcp/doctor.md` → `/dcp:doctor`

### Frontmatter
```yaml
---
description: "DCP read-only facade preflight: registry contract, backend probes, ConPort auto-fork hazard, facade test suite"
arguments: "[--live] [--project <id>]"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
model: "claude-sonnet-4-5"
---
```

### Behavior

**Phase 1 — registry validation.**
1. Resolve registry path: `$DCP_FACADE_REGISTRY` else `~/.dopemux/dcp-facade-registry.yaml`. Missing → FAIL with "copy `services/dcp-readonly-facade/registry.example.yaml` and fill in" (the facade fail-closes without it — expected).
2. Validate against `docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md` (Read the contract doc; check required fields per project: `workspace_path` absolute + exists, `enabled` bool, `service_profiles.*.base_url`, `identity.project`).
3. **Loopback enforcement**: every `base_url` host must be `127.0.0.1` or `localhost`. Anything else = FAIL (security model violation), no exceptions.
4. **Never print the registry wholesale** — it's user-private, outside the repo. Quote only field names and failing values (hosts/ports), never tokens (registry should hold no secrets, but fail safe).

**Phase 2 — auto-fork hazard check** (the one that matters most):
- If `service_profiles.conport.progress_readonly_safe: true` for any project:
  1. Find the ConPort container: `docker ps --format '{{.Names}}' | grep -i conport`.
  2. `docker inspect <name> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep DOPEMUX_AUTO_FORK_PROGRESS`.
  3. Anything other than an explicit `DOPEMUX_AUTO_FORK_PROGRESS=0` → **FAIL loud**: "registry promises read-only progress but ConPort will auto-fork (write) on GET /api/progress. Set the env to 0 or set progress_readonly_safe back to false." This is the single misconfiguration that silently turns the read-only facade into a writer.
- If the flag is false/absent → PASS with note "search_progress will report BLOCKED — by design".

**Phase 3 — backend probes.** For each configured service profile, bounded curl (`--max-time 2`) to the base_url. Report per-service ✅/❌. Apply the **expected-limitations table** so known states aren't misreported as faults:

| Service | Expected Phase-1 state |
|---|---|
| dope-context | BLOCKED (MCP JSON-RPC transport gap — Phase 2 bridge pending) — ✅-with-note, not ❌ |
| conport `search_decisions` query mode | PARTIAL (backend `GET /api/search/{ws}` 500s — UUID serialization bug) |
| conport `search_progress` | BLOCKED unless Phase-2 hazard check passed |
| task-orchestrator | needs `task_orchestrator_project_id` set explicitly; fallback to `project_id` is a known ambiguity — WARN if unset |

**Phase 4 — test suite.**
- Always: `python -m pytest -q services/dcp-readonly-facade/tests` (excluding live), report pass/fail counts.
- `--live` only: `DCP_FACADE_LIVE_TESTS=1 DCP_FACADE_REGISTRY=<path> python -m pytest -q services/dcp-readonly-facade/tests/test_live_optional.py`. Never default — live tests hit real local backends.

**Phase 5 — report.** PASS/FAIL/WARN/NOT_RUN table + the registry path used + max 3 fixes. End with tunnel-readiness verdict: `READY` only if Phases 1–4 all PASS/expected.

### Acceptance criteria
- No registry → FAIL with the copy-from-example remediation, nothing crashes.
- `progress_readonly_safe: true` + missing env → loud FAIL naming both sides of the contradiction.
- dope-context unreachable → reported as expected-BLOCKED, not an error.
- Never echoes registry contents beyond failing field names/values.

### Rollback
`rm .claude/commands/dcp/doctor.md`.

---

## 4. S4 — `/dcp:denylist-check` (skill)

### Objective
The packet-grade regression gate, runnable on demand: red-lane scan + denied-route token sweep + denylist test suite, with output formatted for `COMMAND_LOG.md`. Today each TP-DCP-MCP-RO packet hand-rolls this; packet 0008 makes it a standing requirement.

### File
`.claude/commands/dcp/denylist-check.md` → `/dcp:denylist-check`

### Frontmatter
```yaml
---
description: "DCP regression gate: red-lane scanner + denied-route token sweep + denylist tests; output paste-ready for COMMAND_LOG.md"
arguments: "[--files <paths>] [--base <ref>]"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
model: "claude-sonnet-4-5"
---
```

### Behavior

**Phase 1 — determine file set.** `--files` wins; else changed files vs `--base` (default `origin/main`): `git diff --name-only $(git merge-base origin/main HEAD)..HEAD` plus dirty files from `git status --porcelain`.

**Phase 2 — red-lane gate** (canonical engine, never reimplement):
```bash
PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner \
  --repo-root . --files <file...> \
  [--proof-paths proof/<TP>/PROOF.json --expected-sha $(git rev-parse HEAD)]
```
- Exit 0 = PASS. Exit 1 = BLOCKED/UNKNOWN/CONFLICTING — print the `RedLaneReport` JSON status + blocker count. **UNKNOWN without proof-paths is the scanner's documented fail-closed behavior** — when no `--proof-paths` were provided, label it `UNKNOWN (no proof supplied — expected when run pre-proof)` rather than as a failure of the diff.

**Phase 3 — token sweep.** Extract `DENIED_TOKENS` from `services/dcp-readonly-facade/src/dcp_facade/route_manifest.py` by importing it (data-only module):
```bash
python -c "import importlib.util as u; s=u.spec_from_file_location('rm','services/dcp-readonly-facade/src/dcp_facade/route_manifest.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print('\n'.join(m.DENIED_TOKENS))"
```
Then `rg -n` each token over `services/dcp-readonly-facade/`. Classify every hit:
- `route_manifest.py` itself → **acceptable** (denylist data)
- under `tests/` → **acceptable** (assertions)
- a line that is a comment/docstring in an adapter → **acceptable-with-eyeball** (list it; human confirms)
- anything else in `src/dcp_facade/*.py` → **VIOLATION**

Single source of truth is the import — the skill must not carry its own copy of the token list (drift hazard).

**Phase 4 — denylist tests.** `python -m pytest -q services/dcp-readonly-facade/tests/test_route_denylist.py` (confirm the test filename at implementation time — it's referenced in TP-0005/0006 docs).

**Phase 5 — report.** Three-row PASS/FAIL table (red-lane / token-sweep / denylist-tests) followed by a fenced block formatted for direct paste into a packet's `COMMAND_LOG.md`: each command, exit code, one-line result.

### Acceptance criteria
- Clean tree vs origin/main → all three PASS (or red-lane UNKNOWN-no-proof, labeled as such).
- Planting `memory_store` in an adapter call-path → token sweep VIOLATION naming file:line.
- Token list provably comes from `route_manifest.py` at runtime (change the module → skill output changes).

### Rollback
`rm .claude/commands/dcp/denylist-check.md`.

---

## 5. S5 — `/tp:validate` (skill, smallest)

### Objective
Pre-execution lint for Task Packets so a session doesn't burn time on a malformed packet. There is **no JSON schema** for packets today; `.md` packets get frontmatter+graph validation from pre-commit. This skill adds the structural layer per `task-packets/TEMPLATE_TASK_PACKET.md`.

### File
`.claude/commands/tp/validate.md` → `/tp:validate`

### Frontmatter
```yaml
---
description: "Lint a Task Packet (.md or .json) against template structure + frontmatter before execution"
arguments: "<path-or-TP-ID> [--all]"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
model: "claude-haiku-4-5-20251001"
---
```
(Haiku is deliberate — this is mechanical per the model-routing policy: Opus=judgment, Sonnet=impl, Haiku=lookups/mechanical. **Implementer: after adding any `model:` frontmatter, run the routing-consistency suite — `pytest tests/ -k routing` — TP-DMX-AI-ROUTING shipped invariant tests that may scope command files.**)

### Behavior
1. Resolve packet: path, or glob `task-packets/**/<TP-ID>.{md,json}`.
2. `.md` packets: run `python3 scripts/docs_frontmatter_guard.py <file>` (no `--fix`) + check required sections present and non-empty: Objective, Scope (IN/OUT), Invariants, Acceptance Criteria, Rollback, Stop Conditions — per `TEMPLATE_TASK_PACKET.md` (Read the template at runtime; don't hardcode the section list).
3. `.json` packets: `python -m json.tool` parse + required keys check derived from an existing known-good packet (`task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json` as reference shape).
4. Report per-packet PASS/FAIL with missing sections named. `--all` sweeps `task-packets/` and reports only failures (capped at 10).

### Rollback
`rm .claude/commands/tp/validate.md`.

---

## 6. H1 — DCP surface guard (PreToolUse hook)

### Objective
Enforce DCP-RED-MERGE-SEAM-0001 at **edit time** (hard block) and inject the canonical-writer reminder when contract-sensitive surfaces are edited (advisory). Today the seam is enforced only by the scanner CLI (invoked manually) and the doctrine docs.

### Files
- New: `.claude/hooks/dcp_surface_guard.py`
- Modified: `src/dopemux/claude/native_hooks.py` (import block + `_on_pre_tool_use`)
- New tests: `tests/test_dcp_surface_guard.py`

### Helper API (all pure, never raise)
```python
# .claude/hooks/dcp_surface_guard.py
RED_LANE_ID = "DCP-RED-MERGE-SEAM-0001"

# Hardcoded fallback so the seam stays guarded even if the dopemux package
# import breaks. Kept in sync with red_lane_rules.FORBIDDEN_PATHS by a test.
_FALLBACK_FORBIDDEN = (
    "src/dopemux_pr_merge_specialist/queue_drain.py",
    "dopemux_pr_merge_specialist/queue_drain.py",
    "scripts/batch_resolve_and_merge.py",
)

def _forbidden_paths() -> tuple[str, ...]:
    """Prefer dopemux.dcp.red_lane_rules.FORBIDDEN_PATHS (src/ is on sys.path
    inside native_hooks); fall back to the hardcoded list."""

def surface_guard_block(tool_name: str, tool_input: dict) -> str | None:
    """Block reason when an Edit/Write/NotebookEdit targets a red-lane file.
    Path matching: normalize tool_input['file_path'] to repo-relative posix,
    match by suffix against forbidden paths. None = allow."""

def surface_guard_warnings(tool_name: str, tool_input: dict,
                           project_root: Path, session_id: str | None) -> list[str]:
    """One-time-per-(session,path) advisory when an edit targets a
    contract-sensitive surface. Cooldown state in
    .claude/.surface-guard-warned.json (same pattern as the edit-nudge cache)."""
```

### Tiers

**Block tier** (deny, exit 2): `file_path` suffix-matches a forbidden path → `_deny_tool` with:
> 🚫 {path} is protected by red lane DCP-RED-MERGE-SEAM-0001 (merge-seam, execute=True). Edits are hard-blocked. If this change is genuinely required, the seam must be lifted via its own ADR + task packet — not an inline edit. See docs/03-reference/dcp/README.md.

**Warn tier** (advisory, once per session per path). Watched globs:

| Pattern | Why |
|---|---|
| `schemas/dcp/**` | DCP authority contracts |
| `schemas/proof/**`, `schemas/audit/**` | proof/audit contracts (CI-enforced) |
| `services/dcp-readonly-facade/src/dcp_facade/route_manifest.py` | facade allow/deny authority |
| `docs/03-reference/dcp/chatgpt-mcp-readonly/{TOOL_CONTRACT,RESPONSE_ENVELOPE_SCHEMA,SECURITY_MODEL,MULTI_PROJECT_REGISTRY_CONTRACT}.md` | published contracts |
| `mcp_catalog.yaml`, `.mcp.json` | MCP manifest surfaces |
| `proof/**/PROOF.json` (existing files only — Write to a new path is the scaffold flow, don't warn) | proof is append-only evidence |

Warning text (one line + pointer):
> ⚠️ Contract-sensitive surface ({category}): identify the canonical writer and consumers before editing (governance: contract-sensitive surfaces). For facade surfaces run /dcp:denylist-check after.

### Dispatcher integration (exact anchors)
1. **Import block** (`native_hooks.py:30-53`): add to the existing `try:` —
   ```python
   from dcp_surface_guard import surface_guard_block, surface_guard_warnings
   ```
   and to the `except ImportError` fallbacks:
   ```python
   def surface_guard_block(_tool, _inp): return None      # type: ignore[misc]
   def surface_guard_warnings(_tool, _inp, _root, _sid=None): return []  # type: ignore[misc]
   ```
   **Caveat**: a single try-block means a broken new module would disable ALL orchestrator hooks. Either give the new import its own try/except, or accept the shared block — implementer's call; separate try/except is safer and costs 4 lines.
2. **`_on_pre_tool_use`** (line 327): immediately after the actor-attribution block (line 345), gated on `tool_name in {"Edit", "Write", "NotebookEdit"}`:
   ```python
   if tool_name in {"Edit", "Write", "NotebookEdit"}:
       reason = surface_guard_block(tool_name, tool_input)
       if reason:
           return self._deny_tool(reason)
       extra_parts.extend(surface_guard_warnings(tool_name, tool_input,
                                                 self.project_root, self.session_id))
   ```
   Note ordering: `extra_parts` is created at line 348 — move the guard call after its creation, before the existing `extra_context` join (line 352). Zero cost for non-edit tools.

### Performance
Path matching only — no subprocess, no scanner invocation in the hot path. The scanner CLI stays the deep engine for `/dcp:denylist-check`; the hook only needs the path constants.

### Tests (`tests/test_dcp_surface_guard.py`, mirror `tests/test_orchestrator_enforcement_hooks.py` style)
- Edit to `src/dopemux_pr_merge_specialist/queue_drain.py` → block reason non-None, mentions red-lane ID.
- Edit to the bare `dopemux_pr_merge_specialist/queue_drain.py` variant → blocked (the 0006-era test-gap lesson).
- Edit to `src/dopemux/dcp/red_lane_scanner.py` → not blocked.
- Edit to `schemas/dcp/dcp_control_snapshot.schema.json` → exactly one warning; second call same session → zero (cooldown).
- Write to a **new** `proof/TP-X/PROOF.json` → no warning; Edit to an existing one → warning.
- Sync test: `_FALLBACK_FORBIDDEN ⊆ red_lane_rules.FORBIDDEN_PATHS` (drift guard).
- `Read`/`Bash` tools → guard returns None/[] without touching the filesystem.

### Rollback
Remove the two dispatcher edits + delete the helper + test. No settings/schema/state changes.

---

## 7. H2 — facade denylist nudge (PostToolUse hook)

### Objective
Make the packet-0008 denylist regression continuous: the moment an edit introduces a denied-route token into a facade adapter, say so — instead of discovering it at packet-end review.

### Files
- New: `.claude/hooks/dcp_denylist_nudge.py`
- Modified: `native_hooks.py` `_on_post_tool_use` (advisory_parts block, lines 429-436)
- New tests: `tests/test_dcp_denylist_nudge.py`

### Helper API
```python
# .claude/hooks/dcp_denylist_nudge.py
_FACADE_SRC = "services/dcp-readonly-facade/src/dcp_facade"

def _denied_tokens(project_root: Path) -> tuple[str, ...]:
    """Load DENIED_TOKENS by importlib-from-file on route_manifest.py
    (data-only module, no deps). Cache in module global after first load.
    On any failure return () — fail open."""

def on_facade_edit(project_root: Path, file_path: str,
                   session_id: str | None) -> str | None:
    """If file_path is under _FACADE_SRC (excluding route_manifest.py and
    anything under tests/), scan the file's current content for denied
    tokens. Return one advisory naming token + line numbers, or None.
    Cooldown: once per (session, file, token-set-hash) via
    .claude/.denylist-nudge-cache.json."""
```

### Advisory text
> ⚠️ Denied-route token(s) in {file}: {token}@L{n}[, …]. Acceptable only as denylist data (route_manifest), docstrings, or test assertions — never in an adapter call path. Run /dcp:denylist-check for the authoritative classification before filing this slice's notes.

### Dispatcher integration
In `_on_post_tool_use`, inside the existing `if tool_name in {"Edit", "Write"}:` branch (line 432) — after the `on_edit_tool` nudge:
```python
fp = str((tool_input or {}).get("file_path") or "")
if fp:
    deny_nudge = on_facade_edit(self.project_root, fp, self.session_id)
    if deny_nudge:
        advisory_parts.append(deny_nudge)
```
Cost when the file isn't under the facade: one string prefix check.

### Tests
- Edit adding `memory_store(` to a fake adapter under a tmp facade tree → advisory with token + line.
- Same edit to `route_manifest.py` → None.
- Same under `tests/` → None.
- `route_manifest.py` import failure (missing file) → None, no exception.
- Cooldown: second identical call → None.

### Rollback
Remove dispatcher branch + helper + test.

---

## 8. H3 — MCP health preflight (SessionStart hook)

### Objective
Surface a dead per-worktree MCP or a leaked-container pile-up at minute zero of a session instead of as a confusing mid-task tool failure. Extends the existing SessionStart context-cache pattern.

### Files
- New: `.claude/hooks/mcp_health_probe.py`
- Modified: `native_hooks.py` `_on_session_start` (line 282)
- New tests: `tests/test_mcp_health_probe.py`

### Helper API
```python
# .claude/hooks/mcp_health_probe.py
_CACHE_FILENAME = ".mcp-health-cache.json"   # .claude/, same dir as context cache
_CACHE_MAX_AGE_MIN = 15
_TOTAL_BUDGET_SEC = 2.0
_PORT_TIMEOUT_SEC = 0.25
_DOCKER_TIMEOUT_SEC = 0.8

def emit_mcp_health(project_root: Path) -> str | None:
    """Return a 1-3 line health summary for SessionStart injection, or None.
    Reads fresh results from cache when <15min old; otherwise probes and
    rewrites the cache. Never raises; returns None on any failure."""
```

### Probe design (inside the 2s budget)
1. **Declared servers**: parse `<project_root>/.mcp.json`. For `type: http`/`sse` entries, extract the port — URLs use `${VAR:-default}` templating, so regex the default out (`r":\$\{[A-Z_]+:-(\d+)\}"`) and prefer `os.environ[VAR]` when set. Probe with `socket.create_connection(("127.0.0.1", port), timeout=0.25)` — no HTTP round-trip needed for a liveness line.
2. **Leaked containers**: `subprocess.run(["docker", "ps", "--format", "{{.Names}}"], timeout=0.8)`; count names containing `task-orchestrator`. Docker absent/slow → skip the line entirely (None for that component), never block session start.
3. **Output policy** (ADHD: anomalies loud, health quiet):
   - All healthy, ≤1 TO container → single line: `🩺 MCP: conport ✅ · dope-memory ✅ · task-orchestrator ✅`
   - Problems → that line plus per-problem lines (max 3) with one action each, e.g. `⚠️ dope-memory :3020 not listening → docker compose up -d dope-memory` / `⚠️ 4 task-orchestrator stdio containers (SQLite-contention risk) → /mcp:doctor --prune`

### Dispatcher integration
`_on_session_start` (line 282-296): probe after `emit_session_context`, prepend to the combined context:
```python
mcp_health = emit_mcp_health(self.project_root)
...
combined = "\n\n".join(filter(None, [mcp_health, orch_ctx, workflow_ctx]))
```
Also in the no-workflow-state early path (line 287-289): combine `mcp_health` with `orch_ctx` the same way.

### Cache rationale
SessionStart fires on every session and resume; 15-min TTL keeps repeated starts at ~0 cost while staying fresher than the 4-hour orchestrator cache (container state churns faster than work-item state).

### Tests
- Mock socket: port open → ✅ line; closed → ⚠️ line with compose remediation.
- Docker timeout (mock subprocess raising `TimeoutExpired`) → output omits container line, no exception.
- Cache fresh → no probing (assert socket mock not called).
- `.mcp.json` missing → returns None.
- Port-template regex: `"http://localhost:${CONPORT_MCP_PORT:-3005}/mcp"` → 3005; env override wins.

### Rollback
Remove dispatcher lines + helper + test + delete `.claude/.mcp-health-cache.json`.

---

## 9. H4 — proof-tracking guard (PostToolUse hook)

### Objective
Catch the **documented silent-drop failure** (TP-DMX-DDF-DOCS-001: proof written, gitignored by `proof/*`, never committed — discovered only later) at the moment it happens. The orchestrator's complete-gate checks the proof-bundle *note*; nothing checks that proof *files* are actually tracked in git. "Proof not committed after packet completion" is a red line in `red-lines-and-stop-conditions.md`.

> Design note: the originally-floated "PreToolUse deny on advance_item(complete)" was dropped — the orchestrator already enforces the complete-gate server-side (`canAdvance` / required notes, see `/dx:complete` Phase 2b). Duplicating server-side enforcement in a client hook adds failure modes without adding safety. The *git-tracking* dimension is the part the orchestrator cannot see.

### Files
- New: `.claude/hooks/proof_tracking_guard.py`
- Modified: `native_hooks.py` `_on_post_tool_use` (same advisory block as H2)
- New tests: `tests/test_proof_tracking_guard.py`

### Helper API
```python
# .claude/hooks/proof_tracking_guard.py
TRACK_TIER = frozenset({
    "PROOF.json", "SUMMARY.md", "AUDIT.md", "MERGE_READINESS.json",
    "VALIDATION.md", "CMD_SUMMARY.md", "MODEL_ROUTING.json", "MANIFEST.json",
})  # source: TP-DMX-PROOF-TRACKING-POLICY-001 TRACK table

def on_proof_write(project_root: Path, file_path: str,
                   session_id: str | None) -> str | None:
    """When a Write/Edit lands under proof/ and basename ∈ TRACK_TIER:
      1. `git check-ignore -q <path>` (cwd=project_root, timeout=1s)
      2. ignored AND not already tracked (`git ls-files --error-unmatch`) →
         return the force-track advisory.
    Cooldown once per (session, path). Never raises; None on any git error."""
```

### Advisory text
> 📌 {path} is a TRACK-tier proof artifact but is gitignored by the `proof/*` safety net. Policy (TP-DMX-PROOF-TRACKING-POLICY-001): sanitized proof MUST be force-tracked before the packet completes — `git add -f {path}`. Un-committed proof for a completed packet is a red-line stop condition.

### Dispatcher integration
Same `Edit`/`Write` branch in `_on_post_tool_use` as H2:
```python
if fp:
    proof_nudge = on_proof_write(self.project_root, fp, self.session_id)
    if proof_nudge:
        advisory_parts.append(proof_nudge)
```
Two `git` subprocesses (~10ms each) only when the path is under `proof/` and the basename matches the tier — prefix+basename checks short-circuit everything else.

### Deliberate non-goals
- Does **not** auto-run `git add -f` (staging is an explicit, auditable operator action per the policy's own rationale).
- Does **not** fire for DO_NOT_TRACK artifacts (raw dumps etc.) — those being ignored is correct.
- A Stop-time sweep ("any TRACK-tier proof touched this session still untracked?") is a natural phase 2 — keep out of this slice; the per-write nudge covers the creation moment.

### Tests
- Write `proof/TP-X/PROOF.json` (tmp repo with `proof/*` gitignore) → advisory with `git add -f`.
- Same path after force-add → None.
- `proof/TP-X/raw_stdout.log` → None (not TRACK tier).
- Non-proof path → None, no subprocess (assert via mock).
- git missing/erroring → None, no exception.
- Cooldown honored.

### Rollback
Remove dispatcher branch + helper + test.

---

## 10. Packaging Into Slices (for the implementer)

Each row is one packet/PR-sized slice with its own tests + proof bundle. Hooks touching `native_hooks.py` are contract-sensitive (hook dispatcher) — keep diffs minimal, run the existing `tests/test_native_hooks_workflow.py` + `tests/test_orchestrator_*` suites after each.

| Slice | Contents | Validation gate |
|---|---|---|
| 1 | H4 + S1 (`proof_tracking_guard.py`, `/proof:bundle`) | new tests + `validate_audit_proof.py --all proof/` on a scaffolded fixture + existing hook suites green |
| 2 | S2 + H3 (`/mcp:doctor`, `mcp_health_probe.py`) | new tests + manual run against the live fleet (record in COMMAND_LOG) |
| 3 | H1 (`dcp_surface_guard.py`) | new tests incl. the FORBIDDEN_PATHS sync test + red-lane scanner CLI still exits 1 on the seam files |
| 4 | S3 + S4 + H2 (`/dcp:doctor`, `/dcp:denylist-check`, `dcp_denylist_nudge.py`) | new tests + facade suite green + `/dcp:denylist-check` self-run pasted into proof |
| 5 | S5 (`/tp:validate`) | run against TEMPLATE + one known-good + one deliberately broken packet |

**Cross-cutting implementer checklist:**
- [ ] New imports in `native_hooks.py` use their **own** try/except (don't share the orchestrator block's failure domain) — or document why shared.
- [ ] Every helper: pure, never raises, cooldown caches under `.claude/` (gitignored — verify; add to `.gitignore` if the cache names aren't covered).
- [ ] Skill files follow `docs/03-reference/dx-command-authoring.md`; namespace dirs `proof/`, `mcp/`, `dcp/`, `tp/` under `.claude/commands/`.
- [ ] After adding `model:` frontmatter anywhere: `pytest tests/ -k routing` (TP-DMX-AI-ROUTING consistency suite).
- [ ] Verify at impl time (marked above): exact denylist test filename; task-orchestrator container-name pattern from the wrapper script; `red_lane_rules.FORBIDDEN_PATHS` exact entries; `.claude/` cache gitignore coverage.
- [ ] Update `.claude/CLAUDE.md` "Lifecycle Hooks" section (observed-support list) for each hook that lands — keep observed vs planned honest.
- [ ] PAL chain per AGENTS.md §5 for each slice; proof bundle per §9 (and, fittingly, use `/proof:bundle` once slice 1 lands).

## 11. Explicitly Out of Scope
- Wiring/removing the six dormant ADHD scripts (`check_energy.sh` etc.) — separate decision.
- Task-orchestrator HTTP-singleton transport cutover — the durable fix for container leaks; own packet.
- Promoting the leaked-container sweep into `dopemux mcp doctor` CLI — follow-up after the skill proves the check.
- CI wiring for `tests/dcp/` — already deferred by TP-DMX-DCP-SEAM-ENFORCEMENT-001's follow-up.
- Any change to DCP red lanes, `LIVE_WRITE_READY`, facade route allowlists, or settings.json.
