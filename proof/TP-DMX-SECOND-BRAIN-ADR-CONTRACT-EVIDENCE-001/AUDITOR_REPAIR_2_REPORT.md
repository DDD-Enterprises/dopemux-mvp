<!--
Verbatim independent audit report, round 2. Produced by an independent
read-only session against frozen head 6e1b4472ba626df2a5d7724e87c5ec77c9c46043
in a throwaway detached worktree. Not edited by the producer.

Filename note: this is the round-2 report. The round-1 report keeps its own
filename, AUDITOR_REPORT.md, and is unedited — the operator directed that it
stay as written, and writing new content to that path would be editing it.
This name is one the embedded-audit schema's report_path pattern accepts.

The runner streams progress lines before the report; they are preserved in
AUDIT_PROMPT_CUSTODY_R2.json rather than here, so this file is the report the
prompt asked for and nothing else.
-->

# VERDICT
PASS

BLOCKERS: 0
MUST_FIX: 0

# WHAT I VERIFIED

**Custody**
- `git rev-parse HEAD` = `6e1b4472ba626df2a5d7724e87c5ec77c9c46043` (matches freeze). Tracked tree clean for product files.
- Round-1 report at `AUDITOR_REPORT.md` left unedited (FAIL, 3 blockers / 5 must-fix on `7955ef33d7`).

**Supersession chain (bytes + history)**
- `a9397e5630` inventory: 97 clauses, sha256 `f073ca2880…` matches receipt; contains `dopeTask` (count 2).
- `3e0d89815c` freeze: **only** proof/inventory/census/receipt/generators — **zero** `schemas/` and **zero** validator paths (`git show --name-only`).
- Live inventory sha256 `b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439` = pin = receipt `new_inventory_sha256`; `clause_total` 160.
- `removed_clause_ids` = `[]`. `modified_clauses` length 86 records value/shape rewrites (e.g. drop `dopeTask` list, drop 4-way fusion order) while keeping clause homes — matches `removal_note`.
- Candidate sha256 `e4b2894615…` matches pin; all 10 contracts `adr_status_at_contract_authoring: PROPOSED`.

**Baseline validation**
- `validate_second_brain_adr_contracts.py`: exit 0, 94 checks, `PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE` + FO01 group PASS.
- `pytest tests/governance/test_second_brain_adr_contracts.py`: 63 passed. Matrix tests use `assert_guard(...)` on **named** checks (A09, A26, A27, A31, B02, S23, …), not mere nonzero exit.
- `validate_change_contract.py --base 6153bd4fb3 --head HEAD`: **single** finding — `proof_schema_fail` on `PROOF.json` embedded_audit (`auditor_tool`/`auditor_model`/`skip_reason` schema clash). No second substantive path/lane failure. Matches producer claim.

**1. Denominator completeness**
- Read full candidate (all 10 ADRs Context / Proposed decision / Consequences).
- All six round-1 MUST_FIX-1 omissions present: C09 policy dimensions; C13 completion receipt; C34 ConPort; C30/C31 Dope-Memory/SB PM; C12 historical/current; C22 open/close/cancel — and present in `operator_mandated_additions_present`.
- Census: 160 INCLUDED; 6 EXCLUDED match operator DO-NOT-INCLUDE (preamble, MA-08, acceptance boilerplate, SB-DEC lists, rejected alternatives as oracle-only, 006 context motivation).
- Attacked judgment calls: package/worker + Mac mini as enablement constraints; rejected CURRENT_DIRECTORY not added to identity set; Obsidian split optional vs never-authority; envelope/receipt names not INTERFACE_REQUIREMENT because names absent from candidate — consistent with text.
- Every inventory `source_fragment` is substring of candidate **and** inside ADR allowed span (Context/Proposed/MA-06/Consequences); 0 fragments only-in-rejected (validator A23 + independent span walk).

**2. Bilateral inventory+contract mutation** (sandbox under `/tmp` only)
- Plain flip `ADR-SB-003-C01` both sides → exit 1, guard **`A09-inventory-matches-frozen-pin`**.
- Same + rewrite pin in **copy** of validator + receipt sha + contract pins → exit 1, guard **`S23-recall-authority-first`** (and A22 if mirror incomplete).
- Full bilateral + full repin on 15 non-S booleans (e.g. regenerable vault, PCP/DCP, crash-safe, quiet UX) → **exit 0**. Residual under the documented honest limit: changing the const pin redefines the denominator; Group S independently pins **37** clause IDs; **85** booleans lack S pins. Not quiet false-green without pin rewrite — pin rewrite is same trust class as editing S constants.

**3. Closed sets**
- All **19** `SET_EQUALS` clauses: drop member and add `INVENTED_MEMBER_XYZ` under full repin → **every** case exit 1 with **`A26-closed-sets-bidirectional`** (plus S/A33 where applicable). No escape found. Round-1 PURGE / UX Review shrink hole closed.

**4. Invented authority**
- `grep -rn dopeTask schemas/second_brain/contracts/` → **no matches**.
- `AUTHORITY_TARGET` values observed: `Dope-Memory`, `Leantime`, `Task Orchestrator` only — all in candidate. A27 + INVENTED_AUTHORITY_TOKENS regression guard present. Round-1 BLOCKER 2 closed.

**5. Invented typed surface (Layer B)**
- Spool/custody: invented op catalogues removed; thin assertions grounded via `x-grounding` + A31.
- OpenLoop: only `due_at` + eight PM denials; no invented lifecycle fields.
- ServiceCapabilityReceipt: only `current: const true` (CURRENT/STALE gone).
- ProjectIdentityEnvelope: registry/writer/switch/deny/capture bounds; type **name** is repo naming (judgment call documented); obligations match candidate phrases.
- Injected `cloud_offload` / extra props covered by matrix tests → A31.

**6. Label-only pseudo-contracts**
- No `REQUIRE`/`FORBID`/`MUST_NOT_EXIST` opaque token shapes remain.
- Only `INTERFACE_REQUIREMENT`/`MUST_EXIST` for five candidate-named types that A29/A30 require as files.
- A25 rule-shape gate green; `clause_grounding_error` empty on all 160.

**7. FO-01 lock**
- Mutate `independent_verification.nonblocking_observations` → B02 fails.
- Mutate `authority.architecture_accepted_as_law` → B03 fails.
- Exhaustive leaf scan: **17** escapes — all under `NARRATIVE_POINTERS` / `NARRATIVE_PREFIXES` / classified prose (gate_field_semantics, notes, still_forbidden strings). Receipt projection (40 maps) + PINNED + B11 classification hold for load-bearing fields. Round-1 FO-01 partial lock closed for receipt-derived surface.

**Round-1 class disposition**
| Round-1 | Round-2 evidence |
|--------|------------------|
| B1 bilateral false-green | Plain bilateral fails A09; load-bearing subset fails under repin via S/A26 |
| B2 dopeTask | Absent; A27 |
| B3 set shrink | All 19 SET_EQUALS fail shrink+widen under repin |
| MF1 incomplete denominator | 160-clause census; mandated rows present + S-checked |
| MF2 invented Layer B | Ops/enums stripped; A31 |
| MF3 4-way fusion order | Now authority-first boolean only; S23 |
| MF4 label-only rules | Shapes restricted; A25 |
| MF5 FO-01 field drift | B02 full projection + B03 + B11 |

# FINDINGS
none

**Residual observations (not MUST_FIX)**
- `DENOMINATOR_CENSUS_WORKSHEET.json` marks 25 clauses `UNCHANGED` that `DENOMINATOR_REFREEZE_RECEIPT.json` correctly lists as `modified` (shape renames REQUIRE→BOOLEAN/CONSTANT etc.). Receipt/inventory authority; census bookkeeping drift only.
- Under intentional rewrite of `FROZEN_INVENTORY_SHA256` + receipt pin + contracts, non-S booleans can still flip while validator exits 0 — same class as rewriting Group S literals; documented in validator header. Quiet bilateral without pin change does **not**.

# WHAT I COULD NOT VERIFY
- Live pre-commit hook execution on this host (VALIDATION claims re-run; change-contract alone re-executed here and matches single embedded-audit cause).
- Whether operator ruling text cryptographically binds to inventory bytes beyond “verbatim string length > 500 + HUMAN_OPERATOR” (A11 is presence/size, not content hash of ruling↔inventory).
- Provider-side attestation that this process is independent of the producer (process/worktree independence only).
- Denial fixtures / runtime conformance (correctly NOT_IMPLEMENTED / NOT_RUN; out of packet scope).
