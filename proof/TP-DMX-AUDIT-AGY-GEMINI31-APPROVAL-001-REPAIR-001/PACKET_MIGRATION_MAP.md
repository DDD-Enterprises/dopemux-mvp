# Canonical Task-Packet Schema Migration — Semantic Comparison

**Scope:** `CANONICAL_TASK_PACKET_SCHEMA_MIGRATION` for the two packets in series
`AGY-GEMINI31-APPROVAL-001`.

**Why:** current `main` runs `change-contract-preflight`, which validates changed
`task-packets/*.json` against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.
That spec sets `additionalProperties: false`. The gate **did not exist at the branch's
original base** (`414c7ac7f9`) and was only surfaced by rebasing onto current `main`
(first `cfa4927a88`, then `5d694cc989` under strict branch protection) — which is precisely
why GitHub reporting `MERGEABLE` was not evidence of gate conformance.

**Result:** both packets validate with **0 schema errors / 0 additional-property errors**.

**Rule applied:** no governance requirement silently disappears. The one deliberate
exception is stale false authority — `gemini-3.1-pro-preview` as an *exact selector* — which
is marked **SUPERSEDED/CORRECTED**, never carried forward as active truth.

---

## 1. `TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001.json` (parent)

| OLD CONCEPT | NEW CANONICAL LOCATION | DISPOSITION |
|---|---|---|
| `objective` | `target` | **CORRECTED** — named `gemini-3.1-pro-preview`; now `gemini-3.1-pro-high` |
| `authority.operator_instruction` | `invariants[]` `AUTHORITY:` | PRESERVED |
| `authority.canonical_schema` | `invariants[]` `AUTHORITY:` | PRESERVED |
| `authority.canonical_policy` | `invariants[]` `AUTHORITY:` | PRESERVED |
| `authority.vendor_model_id` | `invariants[]` `AUTHORITY:` | PRESERVED (was already `-high`) |
| `authority.vendor_status: "preview"` | `invariants[]` `AUTHORITY: ... UNKNOWN` | **CORRECTED** — never independently attested; `MODEL_ROUTE.json` records `provider_attested=false`, so doctrine marks it `UNKNOWN` rather than asserting it |
| `scope.in[0]` add to enum | `invariants[]` `SCOPE IN:` + step `S02` | **CORRECTED** (`-preview` → `-high`) |
| `scope.in[1]` document route | `invariants[]` `SCOPE IN:` + step `S03` | **CORRECTED** (`Pro Preview` → `Pro High`) |
| `scope.in[2]` regression coverage | `invariants[]` `SCOPE IN:` + step `S04` | PRESERVED |
| `scope.in[3]` local attestation note | `invariants[]` `SCOPE IN:` | PRESERVED |
| `scope.out[0..4]` (5 exclusions) | `invariants[]` `MUST NOT:` ×5 | PRESERVED |
| `allowed_files` (6 paths) | `commit.allowlist` | PRESERVED — all 6 paths |
| `forbidden_files` (4 paths) | `invariants[]` `MUST NOT modify these paths:` | PRESERVED — all 4 paths |
| `validation` (7 commands) | `steps[].validation` + `commit.verify` | **CORRECTED** — the `agy --model gemini-3.1-pro-preview` command becomes `--model gemini-3.1-pro-high` |
| `proof_requirements` (9 items) | `steps[S05].requirements` | PRESERVED — all 9 |
| `audit.required` / `audit.reason` | `invariants[]` `AUDIT REQUIRED:` | PRESERVED |
| `audit.bootstrap_rule` | `invariants[]` `BOOTSTRAP RULE:` + `steps[S05].requirements` | **CORRECTED** — proves `--model gemini-3.1-pro-high`; the "must not bootstrap its own approval" constraint is preserved verbatim in meaning |
| `rollback` | `invariants[]` `ROLLBACK:` | **CORRECTED** (`-preview` → `-high`) |
| `stop_conditions` (6 items) | `invariants[]` `FAIL CLOSED:` ×6 | PRESERVED — all 6 |
| `repair_packet` | child's `series.parent_tp_id` + child's `depends_on` | PRESERVED — relationship now expressed canonically from the child side |
| `repo_binding.base_branch` | `series.base_branch` | PRESERVED |
| `repo_binding.base_sha` | `invariants[]` `BASE HISTORY:` | **CORRECTED** — illegal `repo_binding` property; original base recorded as history, current binding base is `5d694cc989` |
| `invariants[0]` exact identifier | `invariants[]` `EXACT SELECTOR:` | **CORRECTED** (`-preview` → `-high`; `-preview` retained only in the rejected-alias list) |
| `invariants[1..4]` | `invariants[]` | PRESERVED — proof shape, auth boundary, isolation, bootstrap |

**Added (not migrated), required by the repaired truth:**

- `HISTORY (SUPERSEDED):` — records that the packet originally named
  `gemini-3.1-pro-preview`, and that REPAIR-001 established it is not offered by AGY.
  Recorded as history, **not** as an active invariant.
- `PAIRING:` and `BACKWARD COMPATIBILITY:` — make the enacted schema conditional and the
  generic-`gemini` guarantee explicit at packet level.

## 2. `TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001.json` (child)

The original was a 5-key skeleton. Per directive it is now a genuine canonical repair packet.

| OLD CONCEPT | NEW CANONICAL LOCATION | DISPOSITION |
|---|---|---|
| `objective` | `target` | PRESERVED and expanded to name the current-main governance contract |
| `allowed_files` (10 paths) | `commit.allowlist` | PRESERVED — all 10 paths |
| `pr_number: 1165` | `pr.title` / `pr.body` / `target` | PRESERVED |
| *(absent)* `repo_binding` | `repo_binding` | ADDED — required; mirrors the parent |
| *(absent)* `series` | `series` | ADDED — binds `parent_tp_id` to the parent, `final_packet: true` |
| *(absent)* `steps` | `steps[R01..R06]` | ADDED — encodes rebase, evidence re-verification, prose reconciliation, packet migration, validation, and audit/proof/Steward closure |
| *(absent)* `commit.message` | `commit.message` | ADDED — required |
| *(absent)* `pr` | `pr` | ADDED — required |

**Governance content carried in from `REPAIR-001.md` stop conditions** (the `.md` is
unchanged and remains the human-readable record):

- "Exact AGY high selector absent" → `FAIL CLOSED:` invariant
- "gemini-3.1-pro-preview remains approved" → `FAIL CLOSED:` invariant (correct as a
  *failure* condition — this was never a stale approval claim)
- "Audit verdict FAIL" → `FAIL CLOSED:` invariant
- "PR Steward not READY" → `FAIL CLOSED:` invariant
- Commit topology C1/C2 → `COMMIT TOPOLOGY:` invariant

## 3. Boundaries explicitly preserved

Every substantive boundary required by the adjudication is present as an invariant in the
child packet: no hosted AGY credential, no workflow credential expansion, no signer-trust
weakening, no PR Steward weakening, no audit-verdict weakening, no #1150 mutation, exact
selector evidence required, no-fallback evidence required, wrong-tool pairing rejected,
generic `gemini` compatibility retained, independent audit bound to the final content head,
PR Steward READY required before merge readiness.

Two further invariants encode constraints discovered during this repair: **no Grok support
in this packet** (that is `TP-DMX-EMBEDDED-AUDIT-GROK-ROUTE-001`, after this lands), and
**base currency** (a stale base plus a `MERGEABLE` badge is not gate conformance).

## 4. Scope statement

This migration changes only the two packet JSON files' structure. It expands **no**
production scope: `commit.allowlist` in both packets is exactly the union of the paths the
pre-existing `allowed_files` already authorised, and no production file outside that set is
touched by this repair.
