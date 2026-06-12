# DCP Contract-Promotion + Tooling Layer v1 — Design

**Date:** 2026-06-12 · **Status:** proposed, pending adversarial validation (see 50-validation.md)
**Authority inputs:** repo runtime (highest) · GPT-5.5 synthesis D1–D16 + REV1 · adversarial audit must-fixes · DR-DCP-015 canonical · DR-016 seeded specs (EXTERNAL_PROPOSED — used as input, never authority)

---

## D-A. Promotion mechanics + contracts manifest (S1)

### A.1 Versioning reconciliation

Two version streams exist and stay distinct:

- **Contract identity version** — the `schema_version` const (`dcp-red-lane-taxonomy.v0`). Bumps `.v0`→`.v1` exactly once, at L3 (LOCKED), via a sponsoring TP. This is the README's authority marker.
- **Package semver** — satisfies PAL amendment 1 ("versioned schemas from v0.1.0") at the **package level**, not per-field: a new manifest (below) carries `contract_version` semver per contract, starting `0.1.0` at L1. Patch = doc/provenance edits; minor = additive fields; major = breaking shape change (requires TP + audit).

Rationale: amending every schema to embed semver is churn on contract-sensitive files; a manifest centralizes it and doubles as the registry (D-I.2). Rejected: per-schema semver fields (more diffs on red-laned files); git tags only (not machine-readable inside the repo).

### A.2 Contracts manifest — `schemas/dcp/manifest.json`

New, schema-validated file; one entry per contract:

```json
{
  "manifest_version": "0.1.0",
  "contracts": [
    {
      "contract_id": "dcp_red_lane_taxonomy",
      "schema_file": "schemas/dcp/dcp_red_lane_taxonomy.schema.json",
      "schema_version": "dcp-red-lane-taxonomy.v0",
      "contract_version": "0.1.0",
      "validation_state": "REPO_CROSS_CHECKED",
      "level": "L1",
      "instance_files": ["config/dcp/red_lane_taxonomy.json"],
      "runtime_producers": [],
      "runtime_consumers": ["src/dopemux/dcp/red_lane_rules.py:load_taxonomy"],
      "ci_gates": ["dcp-red-lane-gate", "dcp-contracts-consistency"],
      "enforcement_side": "deterministic"
    }
  ]
}
```

CI consistency test (new): manifest ↔ schema consts ↔ instance files ↔ declared consumers all agree; `level` claims are checked structurally (L2 requires non-empty producers/consumers; L3 requires the conformance gate listed). The manifest is where "locked" stops being prose.

`enforcement_side ∈ {deterministic, llm_advisory, human}` — every entry declares its side, implementing the det-vs-LLM ADR (A.3) as data.

### A.3 Det-vs-LLM ADR (Appendix B(10), PAL amendment 4)

Ship `docs/90-adr/adr-dcp-deterministic-vs-llm-boundary.md`. Content = DR-015 §3 table grounded to repo surfaces:

| Surface | Side | Hard-block capable? |
|---|---|---|
| `native_hooks.py` PreToolUse branches (incl. surface_guard) | deterministic | yes (exit-2 deny) |
| Pre-commit hooks | deterministic | local-only (bypassable → CI duplicates) |
| CI gates (`ci-complete.yml`) | deterministic | **yes — the authority tier** |
| `dopemux dcp` CLI | deterministic | yes (non-zero exit) |
| `.claude/commands/*.md` skills | llm_advisory | never |
| Personas/agents | llm_advisory | never |
| PostToolUse / Stop hooks | deterministic (receipts/feedback only) | no (already-happened) |

Rule (verbatim from constraints): *a probabilistic guard is a vibe plane, not a red-lane gate.* LLM surfaces may recommend `ask`/`warn`; they may never override a deterministic deny, and no deny may exist **only** in an LLM surface.

---

## D-B. C1 — Schema-driven red-lane enforcement (S2)

### B.1 Authoritative instance file

The taxonomy gets a **runtime instance** at `config/dcp/red_lane_taxonomy.json` (today the only instance is a test fixture). Validated against the schema in CI and at load. `config/` is a repo-validated config root (consistent with `config/repo_hygiene/`, `config/orchestrator/`).

### B.2 Schema evolution: detectors (L1 change, REPO_VALIDATED provenance)

Lanes gain an optional `detectors` array — the machine-actionable half the taxonomy lacks. Every detector field is derived from what `red_lane_rules.py` already does (provenance `REPO_VALIDATED`, citing the rules file):

```json
{
  "id": "DCP-RED-MERGE-SEAM-0001",
  "gate": "hard_block",
  "detectors": [
    {"type": "path_pattern", "patterns": ["^src/dopemux_pr_merge_specialist/queue_drain\\.py$", "..."]},
    {"type": "text_pattern", "patterns": ["..."], "path_scope": ".*"},
    {"type": "builtin", "name": "self_certification"}
  ],
  "recommended_action": "...",
  "enforcement": "deterministic"
}
```

- `type ∈ {path_pattern, text_pattern, builtin, manual}`. `builtin` names a check implemented in code (self-certification, stale-proof — things that aren't regexes). `manual` = honest marker for lanes that are not deterministically detectable (`AI-AGENT-AUTHORITY-COLLAPSE`) → they appear in advisory/LLM surfaces and review checklists only, never claimed as enforced.
- Severity binding: `hard_block → BLOCKER`, `project_gate → WARNING` (uses the dead `WARNING` severity the report schema already defines).

### B.3 Loader + Rule coupling

`red_lane_rules.py` gains `load_taxonomy(path) -> list[Rule]`: compiles patterns at load, stamps each `Rule` with **`lane_id`** (new field). `Finding` gains `lane_id` passthrough (additive to report schema — minor version).

**Fallback policy (fixes the PR #858 gap class):** the current hardcoded `FORBIDDEN_PATHS`/`TEXT_RULES` become `FROZEN_FALLBACK_RULES` — used only if the instance file is missing/invalid. CI sync test asserts: **fallback covers 100% of `hard_block`-lane detectors** (equality on the hard-block subset, not ⊆-of-3). Result: under any load failure, hard blocks still hold = fail-closed for the lanes that matter; advisory lanes may degrade = fail-open where safe. Same policy propagates to `dcp_surface_guard.py`'s `_FALLBACK_FORBIDDEN` (regenerate from hard_block lanes + keep its sync test, upgraded to full hard-block equality).

**Self-trigger protection:** exemption list becomes `{red_lane_rules.py, red_lane_scanner.py, receipts.py, config/dcp/red_lane_taxonomy.json}` for *text* rules only. Edits to the taxonomy file itself are caught by the now-implemented `DCP-RED-PROOF-CONTRACT-SCHEMA-MUTATION` lane — **gate `hard_block`** (matching the existing fixture, which already declares this lane `hard_block`; the validation round caught an earlier draft of this design weakening it to `project_gate`). Contract files therefore sit inside the frozen fallback too — the guard guards itself even under load failure. Sanctioned contract changes flow through the protocol in B.6.

### B.4 Coverage closure (both directions)

**Lanes → detectors** (new detectors for the 6 absent + 2 partial):

| Lane | Detector |
|---|---|
| BRANCH-PROTECTION-MUTATION | text: `gh api .*(branch.*protection|rulesets)`, `gh ruleset` |
| CODEOWNERS-MUTATION | path: `(^|/)CODEOWNERS$` |
| PULL-REQUEST-TARGET-UNTRUSTED-CHECKOUT | text: `pull_request_target` scoped to `.github/workflows/` |
| PROOF-CONTRACT-SCHEMA-MUTATION | path: `^schemas/dcp/`, `^config/dcp/` (**hard_block** per existing fixture; sanctioned changes via B.6) |
| SECRETS-IN-ARGV-CACHE-LOGS | text: token-shaped regex (reuse `redact_secret_like` pattern) → BLOCKER, finding text auto-redacted |
| AGENT-APPROVED-MERGE-WITHOUT-SUPERVISOR | builtin: merge-readiness artifact present without approval artifact (couples to C4) |
| WORKFLOW-PERMISSION-ESCALATION | keep blanket workflow-path block; add text: `permissions:` elevation patterns (best-effort, stays partial — documented) |
| AI-AGENT-AUTHORITY-COLLAPSE | `manual` (advisory only) |

**Rules → lanes** (taxonomy additions, provenance REPO_VALIDATED — they're already enforced): new lanes for `DOPETASK-EXECUTION`, `FORBIDDEN-NETWORK-CALL`, `LIVE-WRITE-CREEP`, `STALE-PROOF`, plus the merge-readiness checks fold under existing merge-seam/supervisor lanes. CI invariant tests: **every Rule has a lane_id; every hard_block lane has ≥1 non-manual detector or a `manual` justification.**

### B.5 Wire points

> **Current-state honesty:** today, nothing below exists. The only live enforcement is the pytest DCP suite on synthetic inputs, with the one test that examines real PR files (`test_16`) deselected. Everything in this section is forward-looking work assigned to TPs.

1. CI keeps the pytest gate **and adds a direct scanner invocation** as its own job step — the scanner becomes the enforcement path, not just a tested library. Implementation realities (validation findings adopted): `--packet-id` does **not** exist in `main()` today and is added in TP-103 alongside the loader; the changed-files list **reuses the existing bespoke `CHANGED_FILES` bash fragment** already in `ci-complete.yml`'s root-hygiene step (PR-base/push/fallback branching — do not write a second one); invocation form `PYTHONPATH=src uv run --frozen python -m dopemux.dcp.red_lane_scanner --files … --packet-id ci`. Because `.github/workflows/.*` is itself a hard-block path, the TP that adds this step is processed under the sanctioned-change protocol (B.6) and the gate ships **warn-only first, then enforcing**.
2. Pre-commit: new local hook entry running the scanner on staged files (advisory tier per L-06; CI is authority).
3. `dcp red-lines` CLI (D-G) wraps the same `scan()`.
4. `dcp_surface_guard` PreToolUse keeps importing from `red_lane_rules` — after coupling, those rules are taxonomy-derived automatically. No second source of truth at any point. (Note: the guard exists only on PR #858's branch — `main` has **no** hook-level path enforcement today; until #858 merges the hook-layer gap is 12/12 paths, and CI is the only enforcement tier.)

### B.6 Sanctioned-change protocol (added by validation round)

Hard-block lanes now cover the contract files (`schemas/dcp/**`, `config/dcp/**`, the manifest) and `.github/workflows/**` — which means every legitimate contract-evolution or CI-gate TP would block itself. The release valve is **an approval artifact, not an exemption list**:

- When the scanner raises a contract/workflow-mutation BLOCKER, it checks for a valid `proof/<TP>/APPROVAL.json` (schema-valid, `requester != approver`, fresh per `expiry_window`/`head_sha`, `decision ∈ {allow, gated}`, and whose scope covers the flagged paths). If present → finding downgrades to WARNING with the approval referenced; else → BLOCKED.
- Until the `dcp accept` producer ships (TP-110), sanctioned TPs use **hand-authored APPROVAL.json** instances (the schema + fixture pattern already exist) — the artifact is the gate, the CLI is later convenience.
- **Honest v1 trust model:** identities in approval artifacts are asserted, not authenticated. The v1 trust boundary is repo write access + human PR review; artifacts make approvals *auditable*, not unforgeable. CODEOWNERS entries for `schemas/dcp/`, `config/dcp/`, and `proof/` are a **plan item** (operator action in Wave 0), not a recommendation. Cryptographic identity is V2.
- This makes C4 a load-bearing consumer from Wave 1 onward — contract mutation literally requires an approval artifact.

---

## D-C. C2 — Helper receipt v1 + emitter (S3)

### C.1 Field reconciliation

Evolve `dcp_helper_receipt` to the DR-015 §8 core set, every field provenance-tagged. Where a repo-validated vocabulary exists, use it:

| Field group | Source | Provenance |
|---|---|---|
| `receipt_id`, `parent_receipt_id`, `packet_id` | DR-015 §8 | EXTERNAL_PROPOSED → validated by first producer |
| `helper_surface ∈ {cli, hook, pre-commit, skill, subagent, ci}` | DR-015 §8 ∩ repo surfaces | REPO_VALIDATED (each names a real surface) |
| `decision ∈ {allow, warn, block, defer, advisory, accepted, failed}` | DR-015 §8 (helper decisions ≠ tier decisions; policy.py's `allow/draft_only/gated/refuse/block` stays its own namespace — receipts may *reference* a tier decision, never merge vocabularies) | EXTERNAL_PROPOSED, documented mapping |
| `decision_reason` + `rule_ids[]` (lane_ids) | couples to C1 | REPO_VALIDATED |
| `mutation_class` | couples to C3 | REPO_VALIDATED |
| `checks[] {id, status, exit_code}` | mirrors PROOF.json validations + cockpit receipt | REPO_VALIDATED |
| `artifacts[] {path, sha256}` | DR-015 §8 | EXTERNAL_PROPOSED |
| `repo {root, branch, head_before, head_after, worktree}` | DR-015 §8; populated via read-only git (audit must-fix #3 carve-out) | REPO_VALIDATED |
| `actor {type, id, session_id}` | identity **asserted, not authenticated** in v1 — recorded verbatim, labeled | honest-limits note in schema |
| `integrity {alg: "sha256", value}` | hash of canonical receipt body. **v1 = hashing, not crypto signing** | decision below |

**Signing decision:** v1 uses sha256 content hashes + chaining (`parent_receipt_id`) + git-anchoring (receipts referenced from committed PROOF.json). No signing infrastructure exists in-repo; inventing key management here would be scope creep with weak threat-model payoff (local-first, single-operator). Crypto signing = V2, revisit when receipts cross trust boundaries. Rejected: GPG-sign every receipt (operational burden, no verifier exists); no integrity field (receipts must be tamper-evident at least).

**Non-negotiables carried:** record attempted-blocked mutations; never raw secrets (`redact_secret_like` applied to invocation/args); prompt hashes not prompt text.

### C.2 Store + lifecycle

- Emit to `.dcp/receipts/<session-or-run>/rcpt_<ulid>.json`; hooks append JSONL (`hooks-<session>.jsonl`) to keep per-event cost trivial.
- `.dcp/` gitignored; `dcp evidence-pack` collects relevant receipts into `proof/<TP>/receipts/` (force-added, same convention as PROOF.json) — receipts become part of the committed proof bundle. PROOF.json gains an optional `receipt_refs[]` (additive).
- Emitter = small library `src/dopemux/dcp/receipts.py` (producer used by CLI + hooks). Hook receipt-write failures: log-and-continue for advisory hooks; for a deny, the deny stands regardless (enforcement never depends on receipt success — but the failure itself is recorded in the session receipt on Stop where possible).

L2 = CLI + hooks emit; `dcp verify-proof` validates receipt schema + hash chain. L3 (later): complete-gate requires receipts in evidence.

---

## D-D. C3 — Mutation classes at runtime (S4)

- Instance file `config/dcp/mutation_classes.json` (from the TP-DCP-0002 fixture; tier vocab already REPO_CROSS_CHECKED against `approval_policy.yaml`).
- New pure function `classify_mutation(tool_name, tool_input) -> MutationClassDecision` in `src/dopemux/dcp/mutation_classes.py`: path/command pattern matching per class; no match → `MC-UNCLASSIFIED` (tier TU, posture refuse), mirroring `policy.py` defaults. **Honest label (validation finding adopted):** in v1 this is *fail-safe advisory*, not fail-closed — the classifier's `refuse` reaches the model as advisory context unless the class is `hard_block` (which denies via the surface-guard exit-2 path). Flipping `MC-UNCLASSIFIED` to a hard deny is a v1.5 decision after burn-in, recorded in the manifest when it happens.
- The 3 PROVISIONAL classes (dopetask/bridge/external-write): all deny-in-v1 under D8 regardless of tier; resolve their tiers by citing the corresponding `approval_policy.yaml` capability entries; where no entry exists they stay PROVISIONAL with `LIVE_WRITE_READY`-blocked posture (classifier returns `blocked: true, reason: LIVE_WRITE_READY undefined`). This system does **not** define LIVE_WRITE_READY.
- Consumers (v1): PreToolUse annotation (advisory context: "this action is MC-X / tier T4"; hard_block classes → deny via the same guard path), receipts (`mutation_class` field), `dcp red-lines` output.
- L2 = classifier shipped + hook annotation + tests; classification table exercised in CI.

---

## D-E. C4 — Approval artifact + `supervisor_accepted` plumbing (S5)

The missing piece is a **writer**. Design:

1. **Producer:** `dopemux dcp accept --tp <TP-ID> [--decision allow|gated|refuse] --as <identity>` writes `proof/<TP>/APPROVAL.json` conforming to `dcp_approval_artifact`. CLI enforces `requester != approver` at write time (the schema's test-only invariant becomes runtime-enforced). Required context (mutation_class, tier, head_sha, red_lanes_present) auto-populated from C1/C3 + git read-only — `head_sha` here is a **legitimate live runtime read** (audit must-fix #3 carve-out), distinct from the prohibition on live SHAs in *static fixtures* (red-line #2). **Anti-self-approval hardening (validation findings adopted):** (a) `accept` requires an interactive TTY + typed confirmation phrase (the existing T6 `typed_confirm` pattern) and **refuses when non-interactive** — agent-driven Bash has no TTY, so a model session cannot complete it; (b) the surface guard adds a PreToolUse deny matcher for `dcp accept` invocations from model sessions (defense in depth — string-matchable, acknowledged bypassable by determined obfuscation; the TTY refusal is the real barrier); (c) `dcp.accept` registers as a T6 capability in `approval_policy.yaml`; (d) `--tp` validated against `^[A-Za-z0-9_-]{1,64}$` before any path construction (no traversal); (e) requester sourced from the TP's PROOF.json implementer identity, approver from `--as` — both recorded as asserted-identity per B.6's trust model.
2. **Identity honesty:** v1 identity is asserted (`--as`, falls back to `git config user.name` + session id), recorded verbatim, and the artifact carries the existing schema note that supervisor identity resolution is not authenticated. No auth invented. Crypto identity = V2 with receipt signing.
3. **Reader:** `proof_family.py` gains family `DCP_APPROVAL_ARTIFACT` (classify + expose fields) — the deterministic read surface.
4. **First consumer (in-scope):** scanner builtin detector for `AGENT-APPROVED-MERGE-WITHOUT-SUPERVISOR` — merge-readiness present without a valid fresh APPROVAL.json → BLOCKER finding. This closes a taxonomy lane and gives C4 a real consumer in the same stroke.
5. **Second consumer (boundary):** adapting `steward_gate.py`/`classifier.py` to read APPROVAL.json instead of/alongside harvest-JSON `supervisor_accepted` is a **separate TP touching pr_steward** (different owner surface); this system delivers the artifact + reader and a documented adapter contract, not the steward rewiring.
6. Expiry: `expiry_window` honored by the reader (stale approval → not valid) — turns the SYNTHESIS_INVENTED field into enforced semantics or, if operator prefers, drops it at L1 reconciliation. Default: honor it (staleness is a real failure mode already modeled by `FreshnessStatus`).

L2 = accept writes + reader classifies + scanner consumes, all under tests.

---

## D-F. C5 — Resource map reconciliation (S6)

**Generate, don't hand-maintain.** A deterministic builder (`dcp resource-map sync`, also runnable as a script in CI) derives the instance `config/dcp/project_resource_map.json` sections from their canonical sources:

| Section | Canonical source |
|---|---|
| `forbidden_paths`, `red_line_paths` | C1 taxonomy path detectors (single source: taxonomy) |
| `canonical_writers_map` | `approval_policy.yaml` capability entries (`canonical_writer` fields) |
| root hygiene / placement | `config/repo_hygiene/root_hygiene_policy.json` |
| roots (source/schema/test/proof/packet/config) | repo layout, asserted by existence checks |
| `endpoint_bindings` | **unchanged, PROVISIONAL** (out of scope) |

CI consistency test: regenerate → diff → fail on drift (same pattern as docs-graph validation). `verify_runtime_authority.py` either becomes the validation step here or is retired — decision: **fold its useful checks into the consistency test and retire the dead script** (one validator, not two; its checks are subsumable). Rejected: wiring the dead script as-is (duplicates the new builder's validation, two sources of truth for validity).

L3 path: path sections REPO_CROSS_CHECKED by construction (generated from repo-validated sources) + CI gate ⇒ promotable; the const-pinned `validation_state` is lifted for path sections with endpoint bindings explicitly carved out as PROVISIONAL in the schema (split-state documented in the manifest).

---

## D-G. `dopemux dcp` CLI v1 (S7)

New click group `dcp` in `src/dopemux/cli.py` (additive; cli.py is not red-laned). All commands: `--json` + human output, every run emits a receipt, read-only unless stated.

| Command | Wraps | Mutation |
|---|---|---|
| `dcp preflight` | git posture + policy/taxonomy versions + instance-file validity + `SnapshotBlocked` checks | none |
| `dcp status` | `generate_control_snapshot()` summary view | none |
| `dcp red-lines [--files…\|--diff]` | `RedLaneScanner.scan()` (packet-id param) | none |
| `dcp verify-proof <tp\|path>` | `proof.validate_proof_file` + `validate_audit_proof.py` + receipt-chain verify | none |
| `dcp evidence-pack <tp>` | assemble proof/<tp>/ + receipts + snapshot + red-lane report | **local write to evidence path only** |
| `dcp accept <tp>` | D-E producer | **local metadata write (APPROVAL.json)** |
| `dcp receipts [list\|show\|verify]` | receipt store reader | none |
| `dcp resource-map sync [--check]` | D-F builder | local write to `config/dcp/` (or check-only in CI) |

Named-but-deferred (v1.5, spec'd only): `next`, `prompt implement|audit`, `render-to --dry-run` — they require packet-state plumbing that W3/W4 own. YAGNI now.

What this surface must never do (carried): impersonate approval, call live writers, auto-merge/approve, collapse helper into governor.

---

## D-H. Hooks spec (S8)

Repo-real events only (the 11 dispatched by `native_hooks.py`; DR-015's `UserPromptExpansion` has no analog here — its intent lands in `UserPromptSubmit` advisories, v1.5).

1. **surface_guard upgrade** (delta on PR #858): import taxonomy-derived rules; fallback regenerated to **all hard_block lanes** + CI equality test (B.3). Deny output unchanged (exit-2 `permissionDecision: deny`). Receipts-on-denial appended (C.2).
2. **Mutation-class annotation** in PreToolUse: advisory `additionalContext` ("MC-X, tier T4, approval required") via D-D classifier; hard_block classes deny.
3. **PostToolUse**: existing nudges + receipt line per intercepted event (cheap JSONL).
4. **Stop**: session receipt stub (id, counts, denials, artifacts touched) — feeds `evidence-pack`.
5. **Fail-open/fail-closed policy (explicit):** deny-capable checks fail **closed** for hard_block lanes (frozen fallback guarantees coverage); advisory checks fail **open** (never brick a session for a nudge). CI remains the non-bypassable authority for everything (L-06).
6. Pre-commit additions: scanner-on-staged-files entry (advisory; mirrors CI gate).

---

## D-I. TOOLING-0001 resolutions (S9)

**(1) Which surfaces → deterministic hooks vs LLM instruction?**
Resolved by the ADR (A.3) + manifest `enforcement_side`. Concretely: red-lane/path/schema/proof/receipt checks → deterministic (hook + CI duplicate); synthesis/authoring/summarization/gray-area-classification → LLM advisory; approvals → human (via `dcp accept`). Every *future* check must declare its side in the manifest — CI rejects unlabeled additions.

**(2) Centralized registry vs distributed discovery?**
**Hybrid: distributed discovery, centralized governance-metadata.** Harness auto-discovery of `.claude/commands/` stays (it works; replacing it = over-build). What centralizes is a validated **manifest of governance metadata** — starting with contracts (A.2), extensible to commands/skills (entry: name, surface, enforcement_side, mutation_class, owner) in a later wave. Rejected: full runtime registry service (YAGNI, new failure mode); pure status quo (the 122-command/100-dead drift is the evidence against it).

**(3) Enforce MCP config schema + deprecation tracking?**
**Yes — as CI lint, not runtime.** JSON-schema for `mcp_catalog.yaml` (+ `deprecated: {by, replacement, since}` field), CI validation step. Grounded by observed drift (configs referencing the removed `mas-sequential-thinking`). Small, additive, deterministic. Rejected: runtime schema enforcement in wrappers (couples session startup to lint state).

---

## D-J. Plugin packaging design (S10 — design now, build last)

Source-first layout (`packaging/dcp-plugin/` with `skills/ hooks/ agents/ mcp/`) compiled by a build script into the official `.claude-plugin/plugin.json` + `hooks/hooks.json` + `.mcp.json` shape (per canonical DR-015 §4 mapping). v1 manifest: `defaultEnabled: false`; **no monitors, no channels, no default-agent override, no `commands/` (skills only)**; side-effectful skills `disable-model-invocation: true`; stingy `allowed-tools`.

For dopemux itself the plugin is redundant (files already live in `.claude/`) — its value is **cross-project** (`dcp-core` + `dcp-profile-dopemux` + future `dcp-profile-dnh-crm`; profiles add denies, never weaken core — extension via rules/schemas/path-maps, never forked prompts). Build gate: only after C1+C5 reach L3 (the plugin packages *contracts*, so contracts precede packaging — the directive applied to ourselves).

---

## D-K. Security / threat notes (delta over DR-015 §11)

| Repo-specific risk | Mitigation in this design |
|---|---|
| Hook import-failure gap (PR #858: 9/12 paths fail open) | frozen fallback = 100% of hard_block lanes + CI equality test (B.3) |
| Taxonomy instance file becomes an attack surface (edit the data → disable the guard) | PROOF-CONTRACT-SCHEMA-MUTATION lane covers `config/dcp/**`; CI consistency gate re-validates; CODEOWNERS entry recommended (operator action) |
| Receipt store leaks secrets | `redact_secret_like` on all invocation capture; prompt hashes only |
| Self-certification of this very series | every TP's audit performed by non-author actor; `dcp accept` requester≠approver enforced; series follows AGENTS.md §8 proof bundles |
| `--no-verify` / hook bypass | unchanged truth: CI is the only authority tier; everything local is convenience (L-06) |

## D-L. Decision register (with rejected alternatives)

| # | Decision | Rejected |
|---|---|---|
| 1 | Manifest-level semver + `.v0→.v1` at L3 | per-schema semver fields; git-tags-only |
| 2 | Taxonomy instance in `config/dcp/`, detectors added at L1 with REPO_VALIDATED provenance | keep rules hardcoded (perpetuates decoupling); put instance in schemas/ (mixes shape+data) |
| 3 | Frozen fallback = all hard_block lanes, CI-equality | fallback ⊆ subset (fail-open gap); no fallback (session bricking on data error) |
| 4 | Receipts: sha256 hash-chain + git anchoring, no crypto in v1 | GPG signing (no infra/verifier); no integrity field |
| 5 | `dcp accept` writes APPROVAL.json beside PROOF.json; steward rewiring out of scope | wiring steward directly (crosses owner surface); approval in ConPort (live-write red lane) |
| 6 | Resource map generated from canonical sources + drift CI; retire `verify_runtime_authority.py` | hand-maintained instance (drift); wiring the dead script as-is (dual validators) |
| 7 | Registry = governance-metadata manifest; discovery stays distributed | runtime registry service; status quo |
| 8 | MCP catalog schema as CI lint | runtime enforcement in wrappers |
| 9 | Plugin built last, cross-project value, `defaultEnabled:false` | plugin-first packaging (BUILD_AFTER_CORE_CONTRACTS applies to ourselves) |
| 10 | LIVE_WRITE_READY untouched; classifier blocked-posture on it | defining it here (D8's owner) |
| 11 | Contract+workflow mutation = hard_block with approval-artifact carve-out (B.6) | project_gate warning (non-blocking = theatre); blanket exemptions (bypass) |
| 12 | `dcp accept` TTY+typed-confirm, non-interactive refuses | flag-only identity (agent self-approval); OAuth/auth system (overbuild for v1) |
| 13 | Receipts tamper model: hash-lock at evidence-pack into committed PROOF.json; pre-collection receipts tamper-evident only | claiming local receipts are tamper-proof (false); crypto signing v1 (no infra) |

---

## Amendments adopted from the adversarial validation round (2026-06-12)

Four independent challenge lenses (determinism/fail-closed, security/abuse, feasibility/migration, completeness — full register in [50-validation.md](50-validation.md)) produced 39 findings; the following are adopted into this design beyond the body edits already applied (B.3/B.5/B.6, D-D, D-E):

**A1 (manifest verification, DET-5):** the `dcp-contracts-consistency` CI test must cross-validate `ci_gates` entries against actual job/step names in `ci-complete.yml` — an L3 claim with a nonexistent gate name fails CI. The `level` field is checked, not trusted.

**A2 (version precedence, COMP-11):** `schema_version` (`.v0/.v1`) is the **authority marker**; `contract_version` semver is operational (pinning). At L3 both bump together; a consumer seeing `.v0` treats the contract as provisional regardless of semver.

**A3 (receipt fields completed, COMP-5):** D-C.1's field set extends to the full DR-015 §8 list: add `helper_name` (distinct from `helper_surface`), `helper_version`, `policy_version` (= taxonomy/manifest version at run time), `started_at`/`ended_at`/`duration_ms`, `model`, `mutations[]` (attempted + performed, including blocked attempts), `sensitivity {redacted: bool}`. No silent drops; any future drop must be justified in the manifest entry.

**A4 (provenance honesty, COMP-3/4, must-fix #1/#2):** fields with no repo reconciliation target at schema-evolution time are tagged `EXTERNAL_PROPOSED` or `SYNTHESIS_INVENTED` **in the schema**, with named reconciliation targets where they exist (`checks[]` → `proof.py` validations vocabulary; `decision` → documented mapping table vs `policy.py` decisions). "Validated by first producer" is not a provenance state — that phrasing is retracted.

**A5 (real redactor, SEC-4/DET-10):** `redact_secret_like` is a placeholder stub (its own comment says so) and must be replaced in TP-106 with a multi-pattern redactor: known token prefixes (`ghp_`, `ghs_`, `github_pat_`, `sk-`, `sk-ant-`, `AKIA…`), `KEY=VALUE` where KEY matches `(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)`, URL userinfo (`://user:pass@`), PEM blocks, `Authorization: Bearer/Basic/Token`. Applied **per-field** (invocation/args/env capture) — not blanket over forensic match evidence. The same pattern library powers the `SECRETS-IN-ARGV` lane detector.

**A6 (receipt store realities, SEC-3/DET-6):** `.dcp/` is **not** currently gitignored — TP-106 adds the entry. `dcp evidence-pack` hash-locks each collected receipt into PROOF.json `receipt_refs[{path, sha256}]`; `verify-proof` checks those hashes — the committed PROOF.json is the tamper anchor. Until TP-106 lands, "receipts even on denial" is a NOT_IMPLEMENTED design property, not a present capability.

**A7 (scanner hardening items for TP-103, DET-3/SEC-10/SEC-9):** (a) `diff_text` is accepted but **never scanned** today — either implement diff-text scanning or remove the parameter's implied claim (decide in TP-103; investigation doc corrected); (b) self-certification check's truthiness shortcut (`if impl and auditor`) means absent identity fields silently pass — absent fields in a completed-packet proof must raise a WARNING finding; (c) the `gh api` text pattern is overbroad (matches prose/comments) — scope it to executable contexts (`path_scope` py/sh/workflows), recorded as a deliberate tightening exempt from the equivalence corpus.

**A8 (receipts.py self-trigger, FEAS-7):** the emitter prefers direct `.git/HEAD`/refs parsing for branch/sha; where subprocess-git is unavoidable, `receipts.py` joins the text-rule exemption list (already reflected in B.3). The choice is made explicit in TP-106.

**A9 (CLI startup, FEAS-8):** `cli.py` is ~6.3k lines with non-lazy imports; the `dcp` group registers via guarded/deferred import so `dopemux <anything>` never pays DCP import costs and an emitter dependency failure cannot brick unrelated commands.

**A10 (proof validator second path, FEAS-9):** TP-108's backward-compat check covers **both** `proof.py` and `scripts/audit/validate_audit_proof.py` (separate code path run by the `audit-validator` CI job).

**A11 (skills reference data, COMP-9, DR-015 §13):** plugin/repo skills reference policy **exclusively** via contract instance files or `dcp` CLI calls — no lane lists, tier tables, or path denies in skill prose. Mutation-class `description` fields injected into `additionalContext` are template-constrained (structured fields only — `class_id`, `approval_tier` — never free text from data files) with schema `maxLength`, closing the data-file→prompt-injection channel (SEC-6).

**A12 (plugin never-list automated, SEC-8):** TP-114 includes a deterministic lint of the compiled `.claude-plugin/plugin.json` that fails on `monitors`, `channels`, default-agent override, or `commands/` — not an eyeball check.

**A13 (early-wave auditor separation, COMP-7, must-fix #4):** until `dcp accept` exists, every Wave 0–2 TP's proof bundle must carry an auditor identity distinct from the implementer, verified by the operator before orchestrator advance — procedural, named as such.

**A14 (P6 acknowledgment, COMP-10):** the PAL amendment designates the MCP cutover CRITICAL PATH in the parallel DX-overhaul wave; multi-worktree hook reliability is degraded until it lands. TP-105 carries this as a risk note. This system stays independent of P6 but does not pretend the degradation away.

**A15 (scope clarifications, COMP-1/12/15):** Appendix B(2) command-surface spec + the hard-delete list are **explicitly deferred to the DX-overhaul migration plan** (scope doc updated); "L3(split)" is defined as: L3 for path sections, endpoint bindings remain PROVISIONAL — the only sanctioned partial-L3 variant.

**A16 (contract history, COMP-2):** the three REV1-deferred contracts (mutation class, approval artifact, resource map) were subsequently derived by **TP-DCP-0002** — that packet's fixtures/tests are the current shape authority; this series builds *on* TP-DCP-0002's derivation, it does not re-derive. TP-109's dependency is corrected to TP-101 (manifest) only.
