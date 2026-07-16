# Embedded Audit — AUDITOR_REPORT

- **Packet:** `TP-DMX-UR-ARTIFACT-INTAKE-001` (Universal Router architecture + audit evidence intake)
- **Class:** governance / evidence / documentation-only (final packet of series `UR-ROUTER-GOV-001`)
- **Branch / HEAD:** `codex/ur-artifact-intake-001` @ `45b5ee3f320e777111a6f00227072efeb725996b`. This is the **base commit the staged diff sits on** — the intake changes are staged/uncommitted, so no commit yet contains them. (== `origin/main` pinned base.)
- **Verdict:** `PASS_WITH_RISKS`
- **Primary evidence:** Claude Code Opus objective evidence battery — recomputed SHA-256 over all 41 manifest entries, `shasum -c` on the audit bundle, `dopemux orchestrator packet validate`, allowlist regex, pre-commit docs hygiene, secret scan. These are mechanically verifiable facts (table below), independent of the `codex` implementer.
- **Soft corroboration:** Tier-1 route #2 — an independent Claude Code CLI (Sonnet) run via the repo's `claude-audit` clink config (`scripts/audit/pal_clink_runner.run_audit`, `--permission-mode plan`, read-only). It did real tool calls (118.5s) and agreed, but its prompt pre-stated the expected answers, so treat it as a leading-prompt second look, not fully independent re-derivation.
- **Independence / provenance:** implementer was `codex`; both auditor paths are separate from it. Provider-attested model identity is **not** claimed (runner-configured only; UR-OQ-007 caveat).

## Scope of this audit

This is an **evidence/documentation-only** intake. Absence of runtime, schema, policy, provider, and routing changes is the intended, correct outcome — not a gap. The audit therefore checks **provenance integrity, allowlist/scope discipline, authority hygiene, and diff hygiene**, not code correctness.

## Objective evidence battery (all PASS)

| # | Check | Command / method | Result |
|---|---|---|---|
| 1 | Base pin | `git rev-parse HEAD` vs `origin/main` | `45b5ee3f…` == `45b5ee3f…` ✅ |
| 2 | Dedicated worktree + branch | `git branch --show-current` | `codex/ur-artifact-intake-001` ✅ |
| 3 | Diff hygiene | `git diff --cached --check` | CLEAN (no whitespace/conflict) ✅ |
| 4 | Allowlist discipline | name-only vs packet allowlist regex | 55 added + 1 modified (`INDEX.md`); **all within allowlist** ✅ |
| 5 | Arch extraction inventory | count `UR-ARCH-001/DELIVERABLES/` | exactly **20** deliverables ✅ |
| 6 | Audit-bundle self-integrity | `shasum -a 256 -c SHA256SUMS.txt` | **16/16 OK** ✅ |
| 7 | Original archive identity | `shasum -a 256` both zips | both match packet-required SHA-256 ✅ |
| 8 | Supervisor adjudication identity | `shasum -a 256` md+json | both match packet-required SHA-256 ✅ |
| 9 | Destination manifest integrity | recompute SHA-256 + size for every `ARTIFACT_MANIFEST.json` entry | **41/41** entries, 0 hash/size problems ✅ |
| 10 | INDEX registration | grep both packet IDs | exactly one row each, no duplicates ✅ |
| 11 | Task-packet JSON parse | `python -m json.tool` ×3 | all parse ✅ |
| 12 | Task-packet schema | `dopemux orchestrator packet validate` ×2 | both `status: PASS`, `errors: none` ✅ |
| 13 | Docs hygiene | `pre-commit run --files …` (8 files) | all hooks Passed; no hook mutated the tree ✅ |
| 14 | Secret scan | heuristic regex over staged text | no secrets/tokens/keys ✅ |

## Authority hygiene (the one subjective invariant) — PASS

Both pointer docs correctly **subordinate imported artifacts to current tracked authority** and point to raw evidence instead of asserting unproven claims as runtime truth:

- `docs/94-architecture/universal-router/ur-arch-001.md` — quotes status verbatim (`ACCEPTED_FOR_UR_TP_001_WITH_AUDIT_CONDITIONS`); explicit "Authority posture" states runtime/config/tests/tracked authority remain higher authority and imported `TRUTH_*` copies are research-tier; author frontmatter hedges provenance (`GPT-5.6 Pro (claimed)`).
- `docs/05-audit-reports/universal-router/ur-audit-001r3.md` — records the audit verdict as `PASS_WITH_RISKS` with "Full independent containment: not proven"; author frontmatter hedges (`Claude Opus via Claude Code (runner-configured, not provider-attested)`); the gate section defers execution/automatic-routing to their separate evidence requirements.

## Soft corroboration — Sonnet clink second look

This is a secondary check, not the hard evidence. The prompt (`review_bundle/INDEPENDENT_AUDITOR_PROMPT.txt`) pre-stated the expected invariants, so a compliant model confirming them is weaker than the objective battery above. It did run real read-only tool calls (118.5s) and agreed with every point. Raw normalized output captured in `review_bundle/CLINK_AUDIT_RAW.json` (exit 0). Verbatim verdict:

> All invariants check out: allowlist compliance is total, hashes/sizes verified byte-for-byte against the manifest, both archives extract identically to their tracked copies, the audit bundle's own SHA256SUMS.txt passes, deliverable count is exactly 20, INDEX.md has exactly one row per new packet, and no secrets are present. Both pointer docs correctly subordinate the imported artifacts to current runtime/tracked authority and point to raw evidence rather than asserting unproven claims as fact.
>
> `{"verdict": "PASS", "findings": [], "risks": [ … provenance-unattested … , … content is proposed/design-tier … ]}`

Because the independent verdict is `PASS` **with recorded non-blocking risks**, the normalized embedded-audit status is `PASS_WITH_RISKS` (per `normalize_pal_clink_audit_output`: `verdict==PASS && risks -> PASS_WITH_RISKS`).

## Findings

- **F-UR-INTAKE-INFO-1** (INFO / ACCEPTED_RISK): Archived `UR-AUDIT-001R3/DELIVERABLES/12_FINAL_AUDIT_VERDICT.json` carries `audit_bundle_sha256: "SEE_SHA256SUMS_TXT_AND_OPERATOR_SUMMARY"` (a placeholder). The real per-file hashes live in the bundle's `SHA256SUMS.txt` (verified 16/16 OK). This is inside an immutable archived artifact and is correctly left **byte-identical** per the archives-immutable invariant — not modified by this intake.
- **F-UR-INTAKE-INFO-2** (INFO / ACCEPTED_RISK): Auditor and artifact provenance are runner-configured, not provider-attested (pointer-doc author fields are self-reported; this audit's own model identity — Sonnet via clink / Opus session — is likewise not provider-attested; UR-OQ-007). Both pointer docs disclose this; acceptable for evidence intake.

## Remaining risks (non-blocking, recorded)

1. Pointer-doc author attribution is self-reported and unattested; both docs disclose this, but downstream consumers must not treat provenance as provider-attested.
2. Archived UR-ARCH-001 deliverables and UR-AUDIT-001R3 findings are PROPOSED/design-tier for a not-yet-built router; pointer docs mark `ACCEPTED_FOR_UR_TP_001_WITH_AUDIT_CONDITIONS` — readers must go through the pointer docs, not treat raw `DELIVERABLES` prose as runtime truth.
3. **PR-scoped PR Steward intake/gate (packet step S4) is NOT_RUN**: no PR exists yet, no `MERGE_READINESS.json`, and this proof's 1-hour TTL (`steward_gate` `ttl_seconds=3600`) means it must be regenerated and re-pinned to the actual PR head SHA before the FINALIZATION gate can pass.

## Gate status (honesty)

- Embedded audit: **PASS_WITH_RISKS** (this report + `PROOF.json`), current to HEAD `45b5ee3f…`.
- `pr-steward intake` / `pr-steward gate` (S4): **NOT_RUN** — requires an open PR, a `MERGE_READINESS.json`, and a fresh proof pinned to the PR head. Re-run at PR time.
