# 02_MA08_DRIFT_RECHECK — TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002

Fresh MA-08 executed this run against the post-merge main. **No prior MA-08 result is
inherited**, including the segments a previous run already adjudicated.

## The standing rule this run is executing

Verbatim from the candidate document on `main` (`second-brain-adr-candidates.md`,
"Standing drift recheck precondition (MA-08)"):

> before any of these ADRs is accepted, before a slice task packet is authorized, and
> before implementation planning begins, re-run the full-diff drift check from discovery
> base `72af781e42e0702d9047946e0f5a250e7dff0fa5` to the then-current remote main and
> produce a fresh `DRIFT_RECHECK.md`. **An authority or privacy change in that diff blocks
> acceptance; a contained runtime change is recorded and the affected slice re-gated, not
> silently absorbed.**

That sentence is the whole classification test. It is not "any runtime change blocks" —
it is *authority or privacy* that blocks, and contained runtime change that gets recorded.

## Window

```text
discovery base:       72af781e42e0702d9047946e0f5a250e7dff0fa5
MA08_MAIN_SHA:        75b4cfc581786a53445e412bfc8e25a6e0fdb978   (origin/main, resolved this run)
ancestry:             base IS an ancestor of MA08_MAIN_SHA        (git merge-base --is-ancestor, exit 0)
commits in window:    94
files changed:        823
insertions:           144356
deletions:            2636
scope:                FULL DIFF — not limited to Second Brain paths
```

## Three-segment decomposition

```text
segment A  72af781e .. 33d6c353   (22 commits)  adjudicated at ratification's final drift seal
segment B  33d6c353 .. cfa4927a   ( 5 commits)  adjudicated by the prior MA-08 run
segment C  cfa4927a .. 75b4cfc5   (67 commits)  NEW since the prior MA-08 — adjudicated here
                                                22 + 5 + 67 = 94 ✓ (matches the window count)
```

Segments A and B were re-reviewed this run, not inherited. The §11 hard-gate checklist at
the end is evaluated over the **full** window at `MA08_MAIN_SHA`, not over segment C alone.

---

## Segment C — the new material

239 files, 37015 insertions, 1210 deletions. Complete classification; the counts sum to
the file count, so nothing is silently outside the table.

| Class | Count | Where |
|---|---|---|
| Non-Second-Brain proof bundles | 111 | `proof/TP-DMX-{MCP-CAPABILITY-FAIL-CLOSED,EMBEDDED-AUDIT-GROK-ROUTE,AUDIT-AGY-GEMINI31,DOCS-PROHIBITED-PATTERN-MATCHER,TRUST-GATE-FAIL-CLOSED,DEPENDABOT-VULN-REPAIR}-*/**`, `proof/pr_merge/**` |
| Second Brain proof bundles | 49 | `proof/TP-DMX-SECOND-BRAIN-*/**` |
| **Second Brain machine contracts (NEW)** | **20** | `schemas/second_brain/contracts/**` |
| Tests + fixtures (audit / dcp / mcp / ci) | 17 | `tests/**` |
| Task packets | 13 | `task-packets/*.json`, `*.md` |
| Dependency floors / lockfiles | 12 | `uv.lock`, `package-lock.json`, `pnpm-lock.yaml`, `pyproject.toml`, `requirements.txt`, `Dockerfile.frontend` |
| Second Brain authority/candidate docs | 4 | `docs/03-reference/architecture/second-brain/adr-candidates/**` |
| **Runtime source** | **4** | `src/dopemux/dcp/*.py`, `src/dopemux/mcp/*.py` |
| CI / hook config | 2 | `.github/workflows/embedded-audit.yml`, `.pre-commit-config.yaml` |
| Docs (non-Second-Brain) | 2 | `docs/**` |
| Governance / CI scripts | 2 | `scripts/ci/docs_prohibited_patterns.sh`, `scripts/audit/local_audit_acceptance.py` |
| **Embedded-audit proof contract** | **1** | `schemas/proof/embedded_audit.schema.json` |
| **Second Brain contract validator (NEW)** | **1** | `scripts/governance/validate_second_brain_adr_contracts.py` |
| **Second Brain adversarial suite (NEW)** | **1** | `tests/governance/test_second_brain_adr_contracts.py` |
| **TOTAL** | **239** | matches `git diff --name-only \| wc -l` |

### The three zero-lines the prior run could truthfully write, and this one cannot

The previous MA-08 recorded `runtime source files changed: 0` and
`schema/contract files changed: 0` for its new segment. **Both are false for segment C.**
Reusing that template unchanged would have been the lie. The actual counts, enumerated:

```text
runtime source files changed in segment C:   4   (enumerated below)
schema/contract files changed in segment C:  21  (20 new SB contracts + 1 audit contract)
service logic files changed in segment C:    0   (2 services/ files touched are requirements.txt only)
authority-map files changed in segment C:    0
privacy/classification files changed:        0
compose.yml changed in segment C:            0
config/ai/model-routing.policy.yaml changed: 0
docs/90-adr/** changed in segment C:         0
```

### Runtime source — all four, classified from diffs

| File | Change | Subsystem | Effect on the ADR set |
|---|---|---|---|
| `src/dopemux/mcp/gate.py` | Stops treating a `handshake required` transport warning as an excuse to skip required-tool-glob validation (F019). A required glob with no matching discovered tool is now unproven regardless of why the tool list was empty. | MCP discovery gate | Strictly **more** fail-closed. Outside Second Brain scope; confers no authority. NON-MATERIAL. |
| `src/dopemux/mcp/resolver.py` | Resets per-call state in `resolve()`; an env URL override no longer erases `repo_profile` provenance (F018). | MCP instance resolver | Determinism + provenance-authority preservation in *config resolution*, not data authority. NON-MATERIAL. |
| `src/dopemux/dcp/control_snapshot.py` | Readiness now blocks on packet states `UNKNOWN`/`CLAIMED` ("evidence is incomplete or unproven"). | DCP governance tooling | Strictly more fail-closed. DCP gains no write authority. NON-MATERIAL. |
| `src/dopemux/dcp/red_lane_scanner.py` | Malformed/non-object proof JSON now raises a BLOCKER instead of `continue`; missing implementer/auditor identity yields `self_certification_status = UNKNOWN` rather than `NONE`. | DCP governance tooling | Removes a false-negative class: absence of evidence no longer reads as absence of the defect. NON-MATERIAL. |

All four move in the same direction — unproven states stop being reported as proven. None
touches a canonical write path, a memory plane, or a classification model.

### Schema/contract changes — named, not hidden

| Change | Provenance | Classification |
|---|---|---|
| 20 files added under `schemas/second_brain/contracts/**` (10 ADR contracts, 2 meta-schemas, 2 port contracts, 5 data contracts, 1 coverage index) | PR #1227, `TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001`, independently audited PASS | **This is the evidence under evaluation in this phase, not drift.** It is declarative JSON with no runtime consumer: `grep -rl "task-promotion-request\|task_promotion" src/ services/` returns nothing. Adding a contract that describes a proposed decision is not the same as implementing it. |
| `schemas/proof/embedded_audit.schema.json` modified | PR #1228, admits `grok-cli`/`grok-4.5` bidirectionally | Audit-proof vocabulary. Governs how an audit records its own auditor. Touches no Second Brain surface. NON-MATERIAL. |

### Second Brain authority/candidate docs — the two that changed and why

| File | Change | Adjudication |
|---|---|---|
| `second-brain-adr-candidates.md` | `946054a4…` → `e4b28946…`. Ten line-for-line AC#2 replacements, one per ADR. Line count 375 → 375. | The operator's own authorized AC#2 clarification (#1214), independently audited `PASS_ADR_ACCEPTANCE_CONDITION_AMENDMENT`, 0 blockers. Frontmatter, Context, Proposed decision, Consequences, Rejected alternatives, Evidence and traceability all byte-identical; all ten ADRs remain `PROPOSED`; document remains `CANDIDATE`; token `ACCEPTED` absent. **Authorized amendment, not drift.** |
| `fo-01-repair-status.json` | `0e0258e0…` → `bc2decd1…` | FO-01 reconciliation from #1227. Verified this run as a whole projection of `FO01_RESOLUTION_RECEIPT.json` by validator group B (B02 exact, 0 divergent fields, 40 mapped; B11 every field classified). The receipt itself is byte-identical at `d2325fa2…`. **Reconciled, not rewritten.** |
| `ac2-acceptance-condition-amendment.json`, `ADR_CANDIDATE_AMENDMENT_HEAD.json` | added | Machine-readable authority metadata for the amendment above. Record no disposition (`adr_dispositions_recorded: false`, `adr_acceptance_authorized: false`). |

`docs/03-reference/architecture/second-brain/authority/**` — **zero files changed** in
segment C. The ratification binding, the 32-decision operator ledger, and the traceability
matrix are byte-identical to their values in the prior run's custody record.

### Segment C disposition

```text
NO_NEW_MATERIAL_DRIFT
```

Nothing in segment C changes authority, privacy, or classification. The runtime changes
are four fail-closed hardenings in governance/MCP tooling, all recorded above rather than
absorbed. The Second Brain surface changes are the operator's own authorized amendment and
the contract evidence this phase exists to evaluate.

---

## Segment A — re-review of previously adjudicated drift (not inherited)

Segment A is where the window's real runtime change lives. Re-reviewed this run against the
same subsystem frame; findings agree with the prior run's, and the two claims that carry
architectural weight were re-verified from bytes rather than accepted:

| Change | Subsystem | Effect on the ADR set |
|---|---|---|
| `compose.yml`, `scripts/migration/{provision_conport_project_db,rehome_conport_rows,lock_legacy_conport_archive}.sh`, `import_conport_export.py` (#1188) — the ConPort "project wall": per-project database + per-project LOGIN role, `CONNECT` revoked from `PUBLIC`, ConPort PID-1 supervision | ConPort / project identity | **Re-verified from bytes this run:** no new top-level service block is added to `compose.yml`; the one added top-level name, `conport_supervision_state`, is under `volumes:` (line 45) and is mounted at `/var/lib/conport-supervision` — a supervision-state volume, not a database. The existing postgres-age database is *parameterized*, not multiplied. Directionally reinforces ADR-SB-009 (fail-closed identity, wrong-project denial); establishes no registry and grants no authority, so it neither satisfies nor contradicts the ADR's registry-backed-identity requirement. **CONTAINED, non-contradictory.** |
| `services/dopecon-bridge/{routes,clients}.py`, `services/shared/dopecon_bridge_client/client.py` | dopecon bridge | Adds a `claim_custom_data` proxy for atomic ConPort custom-data claims (re-verified: the added surface is one client method and one route handler). Bridge stays adapter-only; ConPort stays canonical writer. NON-MATERIAL. |
| `services/task-orchestrator/app/services/{workflow_service,workflow_store}.py`, `models/workflow.py` (#1164) | Task Orchestrator | Epic-create idempotency via `uuid5` replay id + fingerprint claim. TO remains sole workflow authority; no PM semantics moved. Consistent with ADR-SB-008. NON-MATERIAL. |
| `src/dopemux/tools/conport_client.py` | ConPort | Honours `CONPORT_URL` instead of a hardcoded base URL. Client wiring only. NON-MATERIAL. |
| `src/dopemux/dcp/red_lane_rules.py`, `docs/90-adr/adr-224-*` (#1193) | DCP | Narrow DCP-RED-MERGE-SEAM-0001 carve-out for two workflow files. Path policy only; DCP read-first posture (SB-DEC-026) untouched. NON-MATERIAL. |
| `AGENTS.md`, `docs/03-reference/governance/evidence-economy.md`, `scripts/governance/validate_change_contract.py` (#1184) | governance process | L0–L3 risk lanes and model-call budgets. Governs process, not system authority. NON-MATERIAL. |
| `config/ai/model-routing.policy.yaml` | routing | **Re-verified:** the added block is `evidence_economy` lane budgets plus an `xai` provider tier whose values are `VERIFY_WITH_VENDOR_DOCS`. Model routing, not data or authority routing, and not provider *eligibility* for a classification domain. NON-MATERIAL. |
| `tools/pr_steward/**`, `config/pr_steward/policy.json` (#1162, #1187, #1191) | PR Steward | Release-gate actor classification and pagination. Outside Second Brain scope. NON-MATERIAL. |
| `config/commandcode/**`, `schemas/commandcode/**`, `.claude/personas/**`, `src/dopemux/personas/**` (#1174–#1176) | agent/persona catalog | Normalized catalog and runtime surface probes. No memory-plane authority. NON-MATERIAL. |
| `docker/mcp-servers-source/conport/**` | ConPort server | Atomic custom-data claim, schema-ensure, info-server port advertisement, supervision tests. Hardening within the existing canonical writer. NON-MATERIAL. |
| `ui-dashboard/**` (#1177) | UI | Tooltip on pending-task start buttons. NON-MATERIAL. |

Segment A disposition, unchanged on re-review: **`MATERIAL_DRIFT_CONTAINED`** — one change
(the ConPort project wall) has genuine architectural adjacency to ADR-SB-009 and is
recorded as contained rather than absorbed. It was already adjudicated at the ratification
seal and again by the prior MA-08. It is not new, and re-review found no reason the
containment no longer holds.

## Segment B — re-review

```text
files changed:                39
non-docs, non-proof files:    2   (uv.lock, docker/…/pal-mcp-server/uv.lock)
runtime source files:         0
schema/contract files:        0
authority-map files:          0
```

Segment B disposition, unchanged on re-review: **`NO_NEW_MATERIAL_DRIFT`**.

---

## §11 hard gates — evaluated over the FULL window at `MA08_MAIN_SHA`

```text
fourth canonical DB created?                            NO   (compose.yml adds one named VOLUME, zero DB services; 41 services at base and at head)
canonical write authority moved off existing owners?    NO
Dope-Memory granted PM/workflow semantics?              NO
ConPort granted task state?                             NO
domain/classification model changed?                    NO   (zero classification/privacy policy paths in the window)
provider eligibility or privacy policy weakened?        NO   (the one routing change adds an xai tier with VERIFY_WITH_VENDOR_DOCS values)
capability-receipt requirement weakened?                NO   (service-capability-receipt exists only as a contract; validator S16 holds "receipt must be current")
DCP granted canonical write authority?                  NO   (both DCP changes are strictly more fail-closed)
task-promotion route enabled?                           NO   (task-promotion-request has zero consumers in src/ or services/)
confidential/restricted spool or indexing enabled?      NO
encryption implementation introduced?                   NO   (remains ABSENT; zero encryption paths in the window)
ADR naming/frontmatter conventions changed?             NO   (docs/90-adr: one file added, two amended, all in segment A; none in segment C)
Second Brain authority records modified post-seal?      NO   (authority/** byte-identical; RATIFICATION_BINDING a23efdc6…, ledger 8e0380eb…, matrix 7ce48101… all unchanged)
```

Two rows in the window are Second Brain surface changes and neither is a hard-gate breach,
because both are the operator's own authorized instruments: the AC#2 clarification (#1214)
and the FO-01 reconciliation plus machine contracts (#1227).

---

## Disposition

```text
segment A  (72af781e..33d6c353):   MATERIAL_DRIFT_CONTAINED   (re-reviewed, not inherited)
segment B  (33d6c353..cfa4927a):   NO_NEW_MATERIAL_DRIFT      (re-reviewed, not inherited)
segment C  (cfa4927a..75b4cfc5):   NO_NEW_MATERIAL_DRIFT      (adjudicated fresh)

MA-08 RESULT: NO_NEW_MATERIAL_DRIFT   -> PHASE B MAY ADVANCE

BLOCKED_NEW_MATERIAL_DRIFT:                    NOT TRIGGERED
MATERIAL_DRIFT_REQUIRES_ARCHITECTURE_REVIEW:   NOT TRIGGERED
BLOCKED_DRIFT_UNVERIFIABLE:                    NOT TRIGGERED
```

### What "NEW" means here, stated so it cannot be read as a dodge

The full window necessarily still contains segment A's contained-but-material ConPort
project wall. That fact does not change and is not being hidden: the full-window
characterisation remains `MATERIAL_DRIFT_CONTAINED`, and it is written into the segment
line above rather than dissolved into the headline. What the operator's advance condition
tests is whether anything **new and un-adjudicated** is material in the authority or
privacy sense. Nothing is. The precedent for this reading is in the repository, not
invented here: the prior MA-08 recorded segment B as `NO_NEW_MATERIAL_DRIFT` inside a
window it characterised as `MATERIAL_DRIFT_CONTAINED`.

The escape hatch is stated rather than assumed away: had this run's re-review found that
segment A's containment no longer holds — for instance, had the project wall since been
extended into a registry that grants identity authority — that would itself be new
material drift and this artifact would read `BLOCKED_NEW_MATERIAL_DRIFT`. It does not.

### Re-gating obligation carried forward

Per the standing rule, a contained runtime change re-gates the affected slice rather than
being absorbed. Carried forward for whoever authorizes implementation:

```text
ADR-SB-009 (Single-Project Safety and Identity Dependencies)
  the ConPort project wall (#1188) is directionally aligned but establishes no
  registry-backed identity. Any ADR-SB-009 implementation slice must re-gate against
  the project wall's actual guarantees rather than assume it satisfies the ADR.
```
