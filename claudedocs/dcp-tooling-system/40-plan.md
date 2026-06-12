# DCP Contract-Promotion + Tooling Layer v1 — Implementation Plan (rev 2, post-validation)

**Date:** 2026-06-12 · **Series ID (proposed):** `DMX-DCP-TOOLING-1xx` · **Status:** validated by 4-lens adversarial round (see 50-validation.md); pending operator approval before TP authoring/orchestrator load
**rev 2 changes:** resequenced per validation findings — fallback regeneration moved into TP-103 (closes fail-open window), `--packet-id` argparse moved into TP-103 (was fiction in TP-104), sanctioned-change protocol (design B.6) threaded through TPs 102/104/112, TP-109 dependency corrected, TP-113 serialized after TP-102, CODEOWNERS became a real Wave-0 item.

## 0. Ground rules (every TP)

- Sponsoring-TP rule: every schema state change happens inside a TP with direct repo derivation.
- Build-time red lines (REV1 §5.3) restated in every packet: no merge-seam contact, no live fixture SHAs, no self-certification, no endpoint binding, no corroboration-as-authority.
- **Auditor ≠ implementer, enforced procedurally pre-TP-110 (amendment A13):** each proof bundle's auditor identity must differ from the implementer; operator verifies before orchestrator advance.
- Validation buckets PASS/FAIL/NOT_RUN per AGENTS.md; proof bundle per §8; the series dogfoods its own receipts from TP-106 on.
- Rollback: every TP is additive or revert-clean; no TP rewrites existing enforcement without the frozen fallback already covering it.
- Model economy: Haiku mechanical / Sonnet implementation / strong model audits only.
- **Sanctioned-change protocol (design B.6):** any TP whose diff touches `schemas/dcp/**`, `config/dcp/**`, or `.github/workflows/**` ships a hand-authored `proof/<TP>/APPROVAL.json` (schema-valid, requester≠approver, scoped to the flagged paths) — this is exercised from TP-102 onward, before the CLI producer exists.

## 1. Waves and packets

### Wave 0 — Foundations

**OP-0 — Operator action (no TP): CODEOWNERS entries** for `schemas/dcp/`, `config/dcp/`, `proof/` — the human-review backstop the v1 trust model depends on (design B.6). Do first; takes minutes.

**TP-101 — Contracts manifest + promotion mechanics + ADR**
- **Authoring precondition (validation FEAS-4):** author after PR #862 merges, or enumerate its 6 routing schemas in the manifest at authoring time. The consistency test must cover every schema present in `schemas/dcp/` — no unlisted contracts.
- Add `schemas/dcp/manifest.json` + manifest schema + `dcp-contracts-consistency` CI test with **cross-file validation**: `ci_gates` entries must name real jobs/steps in `ci-complete.yml` (amendment A1); L2 requires non-empty producers/consumers.
- Ship `docs/90-adr/adr-dcp-deterministic-vs-llm-boundary.md`; document the L0–L3 ladder + version precedence rule (A2) in `schemas/dcp/README.md`.
- Validation: manifest validates; consistency red/green demonstrated incl. a fake `ci_gates` name failing; ADR lint.
- Risk: low. Rollback: delete files.

**TP-102 — Taxonomy instance + detector schema evolution (C1 → L1+)**
- Schema: add `detectors[]` + `enforcement` to lane items (minor bump, provenance REPO_VALIDATED citing `red_lane_rules.py`).
- Create `config/dcp/red_lane_taxonomy.json`: 11 existing lanes + 4 repo-derived lanes (DOPETASK-EXECUTION, FORBIDDEN-NETWORK-CALL, LIVE-WRITE-CREEP, STALE-PROOF) + detectors per design B.2/B.4. `PROOF-CONTRACT-SCHEMA-MUTATION` stays **hard_block** (fixture already says so) covering `schemas/dcp/**` + `config/dcp/**`.
- Tighten `gh api` pattern scope (A7c) — recorded as deliberate change, exempt from TP-103's equivalence corpus.
- CI invariant tests: every hard_block lane has a non-manual detector or `manual` justification.
- **Ships its own APPROVAL.json** (first exercise of B.6, hand-authored).
- Sequencing: **serialize with TP-113** (both edit `ci-complete.yml` — FEAS-11): 102 → 113.
- Validation: schema validates instance; invariant tests; no scanner behavior change yet (loader not wired).
- Risk: low-medium (contract-sensitive; audited). Rollback: revert (instance unused until TP-103).

**TP-113 — MCP catalog schema lint (TOOLING-0001 #3)** *(after TP-102 lands its CI edits)*
- JSON-schema for `mcp_catalog.yaml` + `deprecated` field + CI step.
- Validation: lint catches known drift class in a fixture. Risk: low.

### Wave 1 — C1 runtime coupling

**TP-103 — Schema-driven rules loader + scanner hardening (C1 → L2)** *(blocked by 102)*
- `load_taxonomy()`; `Rule.lane_id`; `Finding.lane_id` (report schema minor bump).
- **Fallback regenerated here, not in TP-105** (closes the FEAS-5 fail-open window): `FROZEN_FALLBACK_RULES` covers **all** hard_block lanes including the 4 new ones; CI hard-block-equality test added here.
- **`--packet-id` added to `main()` argparse here** (removes the `TP-DCP-0005` hardcode; FEAS-1/DET-9).
- Scanner hardening (A7): self-cert truthiness fix (absent identity fields in completed-packet proofs → WARNING); `diff_text` decision (implement scanning or remove the parameter — no silent dead inputs).
- Validation: **behavioral equivalence corpus scoped to the 5 pre-existing rules only** (FEAS-6 — new lanes are net-new coverage with their own tests, explicitly excluded); corrupt-instance test → hard blocks still fire via fallback; fail-open/fail-closed policy per design D-H.5 verified (COMP-13).
- Risk: medium (live guard logic) — flag-gated: loader defaults to frozen rules until flipped.

**TP-104 — Scanner as direct CI gate + pre-commit entry** *(blocked by 103)*
- New CI step in the existing test job: **reuse the bespoke `CHANGED_FILES` bash fragment** from the root-hygiene step (FEAS-2 — do not write a second one); invocation `PYTHONPATH=src uv run --frozen python -m dopemux.dcp.red_lane_scanner --files … --packet-id ci`.
- **Self-gating handled by B.6** (FEAS-3): this TP edits `.github/workflows/` (a hard-block path) — ships its own APPROVAL.json; gate ships **warn-only**, flipped to enforcing in a follow-up commit after one green week.
- **test_16 resolution** (SEC-5/FEAS-10): its deselect exists because the test diffs against TP-DCP-0002's packet base SHA — PR-context-sensitive, false-positives on workflow edits. The direct scanner gate (proper PR base) **replaces** it; test_16 converted to packet-context-only (skip-unless-anchor-matches) or deleted with rationale recorded.
- Pre-commit staged-files entry (advisory tier).
- Validation: CI red/green on a deliberate violation branch; sanctioned-change downgrade demonstrated (approval present → WARNING).
- Risk: medium (gate affects all PRs) — staged enforcement.

**TP-105 — surface_guard taxonomy alignment** *(blocked by 103 AND PR #858 merge — hard dependency, DET-1: `main` has no surface guard today; if #858 stalls, this TP re-scopes to introduce the guard itself)*
- Rebase guard onto the loader; `_FALLBACK_FORBIDDEN` regenerated from hard_block lanes; sync test upgraded ⊆→equality.
- PreToolUse deny matcher for `dcp accept` from model sessions (defense-in-depth half of D-E hardening).
- Risk note (A14): multi-worktree hook reliability degraded until the P6 MCP cutover lands in the parallel DX-overhaul wave.
- Validation: #858's guard tests + equality test + fail-policy checks per D-H.5.

### Wave 2 — Receipts + CLI

**TP-106 — Helper-receipt v1 + emitter (C2 → L1/L2)** *(blocked by 101)*
- Schema evolution per design C.1 + amendment A3 (full DR-015 §8 field set — no silent drops) + A4 (provenance tags in-schema; named reconciliation targets; "validated by first producer" retracted).
- **Real redactor** (A5) replacing the placeholder stub; same pattern library powers the SECRETS lane detector.
- Emitter `src/dopemux/dcp/receipts.py`: prefers direct `.git/HEAD`/refs parsing; joins text-rule exemption list if subprocess unavoidable (A8). **`.dcp/` added to `.gitignore`** (A6 — currently missing).
- Validation: schema round-trip; property tests (no secrets in receipts incl. short tokens/URL-auth/PEM; hash chain verifies); provenance-tag completeness gate before schema lock (must-fix #2).
- Risk: medium (contract-sensitive).

**TP-107 — `dopemux dcp` CLI group v1** *(blocked by 103, 106)*
- `preflight / status / red-lines / verify-proof / receipts` + receipt per run + `--json`.
- **Lazy/guarded import registration** in `cli.py` (A9 — 6.3k-line non-lazy file; an emitter dep failure must not brick unrelated commands); name-conflict precheck (COMP-14); shared `--tp` sanitizer `^[A-Za-z0-9_-]{1,64}$` (SEC-7).
- Validation: CLI integration tests; receipt per invocation; exit codes (red-lines non-zero on BLOCKED); `dopemux --help` startup time unchanged.
- Risk: low.

**TP-108 — `dcp evidence-pack` + receipt hash-locking** *(blocked by 107)*
- Assembly into `proof/<TP>/`; PROOF.json `receipt_refs[{path, sha256}]` (A6 hash-lock); `verify-proof` checks hashes.
- Backward compat verified against **both** validators: `proof.py` AND `scripts/audit/validate_audit_proof.py` (A10) — existing 30+ bundles must still pass both.
- Validation: pack→verify round trip; tamper test (modified receipt → verify fails); old bundles green on both paths.
- Risk: low-medium.

### Wave 3 — Classes + approval

**TP-109 — Mutation-class instance + classifier + hook annotation (C3 → L2)** *(blocked by 101; 106 optional for the receipt field)*
- `config/dcp/mutation_classes.json` (from TP-DCP-0002 fixture — that packet is the shape authority, A16); `classify_mutation()`; PreToolUse annotation labeled **fail-safe advisory** (DET-7) — hard_block classes deny via guard path; `description` injection template-constrained to structured fields + `maxLength` (A11/SEC-6).
- **PROVISIONAL-class gate (COMP-8):** before L2, each PROVISIONAL class either gets a matching `approval_policy.yaml` entry or documents a concrete resolution path; unresolved = stays PROVISIONAL with LIVE_WRITE_READY-blocked posture.
- Validation: classification table incl. unmatched→MC-UNCLASSIFIED/refuse-advisory; injection-template test (free text from data file never reaches additionalContext).
- Risk: medium (new hook behavior; advisory-first).

**TP-110 — `dcp accept` + approval artifact + reader + scanner consumer (C4 → L2)** *(blocked by 107)*
- Producer per design D-E **as amended**: TTY + typed confirmation, non-interactive refuses; `dcp.accept` registered T6 in `approval_policy.yaml`; `--tp` sanitized; requester from PROOF.json implementer, approver from `--as` (asserted-identity, labeled); live `head_sha` legitimacy note (COMP-6).
- Reader: `proof_family` family `DCP_APPROVAL_ARTIFACT`; expiry honored.
- Scanner consumers: `AGENT-APPROVED-MERGE-WITHOUT-SUPERVISOR` builtin AND the **B.6 sanctioned-change downgrade** (replaces hand-authored-only flow).
- Validation: write→classify→scan integration; requester==approver rejected; non-TTY refused; traversal attempts rejected.
- Risk: medium. Boundary: steward/classifier rewiring stays out (adapter contract documented only).

**TP-111 — Resource-map builder + drift CI (C5 → L2)** *(blocked by 102)*
- `dcp resource-map sync [--check]`; generation from canonical sources; CI drift gate; fold-and-retire `verify_runtime_authority.py`.
- Validation: regenerate-diff-clean; source-mutation fixture → drift detected.
- Risk: low-medium.

### Wave 4 — Lock + package

**TP-112 — Promote C1 + C5 to L3** *(blocked by 104, 105, 111)*
- `.v0`→`.v1` + semver bump together (A2); validation_state lifts (C5: paths CROSS_CHECKED, endpoint bindings PROVISIONAL — the defined "L3(split)" variant, A15); manifest levels updated.
- The promotion diff itself touches `schemas/dcp/**` → **processed under B.6 with its own APPROVAL.json** — the gate provably guards its own promotion.
- Validation: full dcp suite + both CI gates green; manifest cross-file consistency; independent audit mandatory (non-author).
- Risk: medium (the formal lock).

**TP-114 — Plugin packaging build (cross-project)** *(blocked by 112)*
- `packaging/dcp-plugin/` source + compile per design D-J + A11 (skills reference contracts via data/CLI only — no policy prose).
- **Automated never-list lint** (A12/SEC-8): CI schema-check of compiled `.claude-plugin/plugin.json` fails on monitors/channels/default-agent/commands.
- Validation: scratch-project install; `defaultEnabled:false`; never-list lint red/green.
- Risk: low.

**TP-115 — Registry extension to commands/skills (TOOLING-0001 #2 completion)** *(blocked by 101; optional filler)*
- Governance-metadata manifest for commands/skills; CI rejects unlabeled additions. **Delete-list execution stays with DX-overhaul** (A15/COMP-12) — this TP only gives it the metadata substrate.
- Risk: low.

## 2. Dependency graph (rev 2)

```
OP-0 (operator, immediate)
101 ──┬─→ 106 ─→ 107 ─→ 108
      ├─→ 109
      └─→ 115
102 ──┬─→ 113
      ├─→ 103 ─→ 104 ─┐
      │        └─→ 105 ─┼─→ 112 ─→ 114
      └─→ 111 ──────────┘
107 ─→ 110
[105 additionally hard-blocked by PR #858 merge]
```

First wave (parallelizable now): **OP-0, TP-101, TP-102** (113 follows 102).
Critical path: **102 → 103 → 104/105 → 112** (C1 to L3).

## 3. Gate-open declaration

When TP-112 completes with proofs: C1=L3, C5=L3 (paths; endpoint bindings PROVISIONAL per the A15 definition), C2/C3/C4=L2, CLI v1 live, receipts flowing + hash-locked, both TOOLING-0001 lints active, ADR recorded → **`BUILD_AFTER_CORE_CONTRACTS` gate = OPEN**, recorded as a decision + manifest state. Broader tooling (V2 verbs, write-broker MCP, monitors-as-telemetry) may then be scoped under D8's still-standing dry-run rules.

## 4. Estimate discipline

No time estimates (no evidence base). Size: 101/113/115 small; 102/106/107/108/111/114 medium; 103/104/105/109/110/112 medium-large. **15 TPs** (101–115) + 1 operator action; 3-item first wave. *(Count corrected from "14" at load time — the orchestrator's own create response surfaced the off-by-one.)*

## 5. Validation strategy per AGENTS.md

- Narrow-first: per-TP focused tests → dcp suite → CI full.
- Equivalence corpus (TP-103) scoped to pre-existing rules; new coverage validated separately.
- Staged CI enforcement (warn → enforce) for the direct gate; sanctioned-change downgrade demonstrated before enforcing.
- Backward-compat on both proof validators against existing committed bundles.
- Every TP: independent audit (auditor ≠ implementer, procedurally verified pre-TP-110), proof bundle, PASS/FAIL/NOT_RUN; NOT_RUN never collapsed into PASS.
