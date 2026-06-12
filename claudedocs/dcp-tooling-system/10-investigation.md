# DCP Contract-Promotion + Tooling Layer — Investigation Digest

| | |
|---|---|
| **Date** | 2026-06-12 |
| **Method** | 5 parallel read-only sub-investigations (Sonnet×4, Haiku×1) + direct read of canonical DR-DCP-015; Opus synthesis with corrections |
| **Supersedes** | refines `claudedocs/dr-dcp-015-evidence-pack/02-core-contract-status-audit.md` (two corrections noted below) |

## 1. Corrections to the prior contract audit

1. **C1 (red-lane taxonomy) is closer to promotion than graded.** Its contract-level `validation.state` is already `REPO_CROSS_CHECKED` (the only contract genuinely there). The gap is not reconciliation — it is **runtime coupling and lane coverage**.
2. **C5's "runtime enforcement" was overstated.** `scripts/verify_runtime_authority.py` is **invoked by nothing** (no CI, no pre-commit, no Makefile reference). Real enforcement analogs: the `root-hygiene` pre-commit hook + `policy.py` capability classifier (used by orchestrator workflows). The resource-map schema itself is consumed by nothing.

## 2. Current-state map (verified)

### 2.1 Enforcement runtime (`src/dopemux/dcp/`)

- **`RedLaneScanner`** (`red_lane_scanner.py`): scans changed files + proof artifacts → `RedLaneReport`. **Correction (validation round):** the `diff_text` parameter is accepted but **never scanned** — only `diff_text_supplied=bool(...)` is recorded; text rules run on file content only (deleted-lines-only patterns are invisible). Has an argparse `main()` (`python -m dopemux.dcp.red_lane_scanner`) that is **wired to nothing** and has **no `--packet-id` flag**; `packet_id` hardcoded `"TP-DCP-0005"` (scanner.py:121).
- **Rules** (`red_lane_rules.py`): 12 `FORBIDDEN_PATHS` regexes + 5 `TEXT_RULES` (`MERGE_SEAM_001`, `DOPETASK_001`, `NETWORK_001`, `EXTERNAL_WRITE_001`, `LIVE_WRITE_001`), all `BLOCKER`. `Rule` dataclass has `rule_id/category/severity/patterns/path_scope/recommended_action` — **no lane_id**. Patterns string-concatenated to avoid self-triggering; `is_safe_false_positive()` exempts only the two rules/scanner files.
- **Runtime invocation: tests-only.** CI gate `TP-DMX-DCP-CI-GATE-001` runs `pytest tests/dcp/` (with `test_16_no_forbidden_files_modified` **deselected**). No hook, pre-commit entry, CLI command, or service calls the scanner directly.
- **Other modules**: `proof_family.classify_artifact()` (proof-artifact classification, 6 families), `control_snapshot.generate/write_control_snapshot()` (derived audit view, raises `SnapshotBlocked`), `proof_pointer_reader` (thin wrapper). All **tests-and-library-only**; `services/repo-truth-extractor` carries a *parallel* `classify_artifact` (not imported — duplication debt, out of scope here).
- **Scanner output is structurally compliant** with `dcp_red_lane_report.schema.json` (one note: `INFO`/`WARNING` severities defined but never emitted).

### 2.2 Taxonomy ↔ rules namespace split (the C1 coupling gap)

11 taxonomy lanes (fixture `dcp_core_fixture.json`) vs scanner rules:

| Taxonomy lane | Scanner coverage |
|---|---|
| `DCP-RED-MERGE-SEAM-0001` | YES (paths + `MERGE_SEAM_001`) |
| `DCP-RED-SELF-CERTIFYING-LOOP` | YES (inline proof-field check, not a `Rule`) |
| `DCP-RED-WORKFLOW-PERMISSION-ESCALATION` | PARTIAL (blanket `.github/workflows/` path block) |
| `DCP-RED-IDENTITY-CONTACT-MERGE-…-EXTERNAL-WRITE` | PARTIAL (`EXTERNAL_WRITE_001` routes only) |
| `DCP-RED-SECRETS-IN-ARGV-CACHE-LOGS` | NO (redaction only, no detection rule) |
| `DCP-RED-BRANCH-PROTECTION-MUTATION` | NO |
| `DCP-RED-CODEOWNERS-MUTATION` | NO |
| `DCP-RED-PULL-REQUEST-TARGET-UNTRUSTED-CHECKOUT` | NO |
| `DCP-RED-PROOF-CONTRACT-SCHEMA-MUTATION` | NO (`schemas/dcp/**` not in FORBIDDEN_PATHS) |
| `DCP-RED-AGENT-APPROVED-MERGE-WITHOUT-SUPERVISOR` | NO |
| `DCP-RED-AI-AGENT-AUTHORITY-COLLAPSE` | NO (not deterministically detectable) |

Reverse direction: scanner categories with **no lane** — `DOPETASK_EXECUTION`, `FORBIDDEN_CALL` (network), `LIVE_WRITE_CREEP`, `STALE_PROOF`, `UNKNOWN_REVIEWER_OR_BOT`, `UNRESOLVED_BLOCKING_THREAD`, `CI_OR_WORKFLOW_MUTATION`, `UNCLASSIFIED_RISK`. The taxonomy and the enforcement are **two unlinked namespaces**.

### 2.3 Contract schema states (refined)

| Contract | validation.state | Const-pinned? | Promotion blocker (per schema's own notes) |
|---|---|---|---|
| C1 `dcp_red_lane_taxonomy` | `REPO_CROSS_CHECKED` | no | none at reconciliation level — needs runtime coupling + TP for version bump |
| C2 `dcp_helper_receipt` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | **yes (const)** | "no repo-runtime helper-receipt analog exists"; missing signer/signature/verdict-style fields |
| C3 `dcp_mutation_class` | `REPO_CROSS_CHECKED` (contract level) | no | 3 PROVISIONAL classes (dopetask/bridge/external-write); "promotion path … not yet defined"; `LIVE_WRITE_READY` undefined+blocking |
| C4 `dcp_approval_artifact` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | **yes (const)** | envelope `SYNTHESIS_INVENTED`; supervisor signoff "not proven wired"; `requester != approver` only test-enforced |
| C5 `dcp_project_resource_map` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | **yes (const)** | `endpoint_bindings[].binding_status` constrained to `PROVISIONAL\|UNKNOWN` at .v0 — endpoint promotion requires runtime proof (out of this system's scope, blocked on MCP topology work) |

**Contract history (added by validation round):** REV1 deferred C3/C4/C5 ("shapeless") from TP-DCP-0001; **TP-DCP-0002 subsequently derived all three** — its schemas/fixtures/tests (`test_dcp_0002_contract_derivation.py`, 17 tests) are the current shape authority. This series builds on TP-DCP-0002's derivation; it does not re-derive.

Shared vocab: `validation.state ∈ {REPO_CROSS_CHECKED, PROVISIONAL_UNVERIFIED_ENFORCEMENT, DEFERRED}`; field provenance ∈ `{REPO_VALIDATED, REPO_VALIDATED_BY_AUDIT, EXTERNAL_PROPOSED, SYNTHESIS_INVENTED}`. **Promotion rule (README, verbatim):** *"No schema in this directory should be treated as the authoritative source for runtime enforcement until upgraded past `.v0` by a subsequent task packet with direct repo derivation."* Const-pinned states mean the schema file itself must change to promote. **No formal promotion process exists beyond "a subsequent task packet."**

Note: PROOF.json runtime uses a **different** `validation_state` vocabulary (`NOT_STARTED/IN_PROGRESS/PASSED/FAILED/PARTIAL` in `orchestrator/validation/proof.py`) — same field name, different namespace. Design must not conflate them.

### 2.4 PR #858 cross-check

- **Not a divergent red-lane source.** `dcp_surface_guard.py` imports `red_lane_rules.FORBIDDEN_PATHS` at runtime (primary path); `_FALLBACK_FORBIDDEN` = 3-path subset used only on ImportError, with a test-enforced ⊆ invariant.
- **Known gap**: on import failure, 9 of 12 forbidden paths lose hook enforcement (fail-open for those 9). Merge-seam core stays blocked.
- `/proof:bundle` scaffolds AGENTS.md §9 PROOF.json + `schemas/proof/embedded_audit.schema.json` — **not** `dcp_helper_receipt`. No code anywhere produces a helper receipt.
- PR treats `schemas/dcp/**` as a warn-tier protected surface; never consumes the contract schemas.
- CI status: `mergeable: UNKNOWN`, all check states null — **not confirmed green**.

### 2.5 Approval plumbing

- Tier system T0–T6/TX/TU fully defined (`approval_policy.yaml` + `policy.py`); `classify_capability()` is a fail-closed read-only registry/classifier (unregistered → TU/refuse). Enforcement boundary lives in orchestrator workflows, not policy.py.
- **`supervisor_accepted`: read-only consumers** (`steward_gate.py:133`, `tools/pr_steward/classifier.py:873`) — **zero writers** in runtime code. DX-overhaul Phase-1 claim confirmed.
- Existing runtime receipt artifacts to align with (not reinvent): `PROOF.json` (validated by `proof.py`), cockpit `safe_action_gate.receipt.v1` (richest: tier/safety_class/canonical_writer/typed_confirmation/timestamps), `TransitionReceipt` (in-memory), `memory_route_receipt`, `CanonicalReceipt`/`MirrorReceipt` (pm/writes).

### 2.6 CI / pre-commit / hygiene wiring

- CI: single `ci-complete.yml`; DCP gate = pytest `tests/dcp/` (97 tests across 6 files), with `test_16_no_forbidden_files_modified` deselected (reason unestablished — flagged for the plan).
- Pre-commit: `proof-embedded-audit-schema` (validates `proof/*/PROOF.json` embedded_audit), `root-hygiene`, docs guards. **No red-lane/scanner entry.**
- `verify_runtime_authority.py`: exists, checks `forbidden_authority_paths` etc. — **never invoked**.

## 3. Binding design constraints (already decided — do not re-litigate)

From the GPT-5.5 synthesis (D1–D16, REV1) + adversarial audit (GO_WITH_FIXES, 5 must-fixes adopted) + PAL-validated workflow maps:

1. **D15 (DECIDED, HOLD)**: contracts first; deterministic hooks/CLI enforce; LLM skills synthesize; humans approve; plugin v1 `defaultEnabled:false`.
2. **PAL amendments**: P1 contracts as versioned machine-readable schemas from v0.1.0; det-vs-LLM boundary codified as an ADR; (P6 MCP cutover critical-path — adjacent system, not this one); W8 auto-fix idempotent-only.
3. **Five build-time red lines (REV1 §5.3)**: never wire the merge seam; never compute live SHAs for static fixtures; never self-certify the contract-locking packet; never bind ConPort/dope-memory/TO endpoints in v1; never promote external corroboration to repo authority.
4. **L-06**: config ≠ enforcement — client-side hooks/pre-commit are AUTHORITY-AS-CONFIGURED only; every critical check duplicates in CI.
5. **DR-015 §8 receipt requirements** (receipt_id/parent/packet_id/helper_surface/policy_version/decision+rule-IDs/checks+exit-codes/artifact hashes/no-raw-secrets/record-attempted-blocked-mutations) and **§12 V1/V2/Never table** (Never: channels, default-agent override, auto-approve/merge, CRM sends from skills, broad live-writer plugin).
6. **v1 dry-run/forbidden set (D8)**: live TO writes, Dopetask execution, GitHub mutation, PR merge, CRM/channel writes all stay deny.
7. **DR-016 control split**: skills synthesize · hooks/CLI enforce · Git/CI duplicate · humans approve. Block > ask > warn > allow; receipts even on denial.
8. **`LIVE_WRITE_READY` stays undefined+blocking** — this system must not define it (D8's owner); classifiers must fail closed on it.

## 4. Genuinely open questions this system must answer

1. Promotion mechanics: what exactly is "locked," and how does `.v0`→`.v1` reconcile with the "semver from v0.1.0" amendment?
2. How does the scanner become schema/data-driven without losing its self-trigger protections, and what closes the 2-way lane↔rule coverage gap?
3. What produces helper receipts, where do they live, and how do they chain into PROOF.json?
4. Who writes `supervisor_accepted` (the C4 producer), and what consumes it first?
5. How does the resource map stop drifting from `root_hygiene_policy.json`/`policy.py` (generate vs validate)?
6. TOOLING-0001 (1) surface split, (2) registry vs distributed discovery, (3) MCP config schema enforcement.
7. Fail-open vs fail-closed policy for hooks (PR #858's import-failure gap).
8. Where the `dopemux dcp` CLI lands in `cli.py` and which subcommands are v1.

## 5. Evidence & confidence

| Area | Confidence | Notes |
|---|---|---|
| Scanner internals + caller map | high | sub-agent full read with file:line cites |
| Lane↔rule diff table | high | both sides read directly |
| Contract states + promotion vocab | high | schemas read verbatim |
| PR #858 verdict | high | diff read; CI status genuinely UNKNOWN |
| supervisor_accepted unplumbed | high | corroborated by 2 independent passes |
| Constraint corpus (D1–D16, audit, gates) | high | extracted near-verbatim with line refs |
| `test_16` deselection rationale | UNKNOWN | flagged for plan TP-104 |
| PR #858 exact test counts | medium | PR-body claim, CI not green-confirmed |
