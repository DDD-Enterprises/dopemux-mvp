<!--
Packet: TP-DMX-DR04-PR1341-L2-AUDIT-031 (parent macro packet: MACRO-DMX-DR04-PR1341-L2-FINALITY-031)
PR: 1341
Audited sha: d39d06bcb75fa2dcb5fac3de779e45c1cf0b502f
Auditor: AGY 1.2.0
Model requested: gemini-3.8-flash-high
Effort: high
Run window: 2026-09-11T14:51:02Z - 2026-09-11T14:53:46Z
Exit code: 0

The auditor's report text follows verbatim, unedited, below this header.
-->

# Independent L2 Audit — PR #1341 (`dopemux-mvp`)

Audit executed against commit `d39d06bcb75fa2dcb5fac3de779e45c1cf0b502f` (base: `640f0a2b56d795442455b0ecd98cef7c7d22703e`, prior reviewed head: `bc4249eecf4f428528488a7a3d4eeb3420aebfbc`).

---

## 0. Custody & Integrity Verification

1. **Custody Head Check:**
   - Command: `git rev-parse HEAD`
   - Output: `d39d06bcb75fa2dcb5fac3de779e45c1cf0b502f` [Observed]
   - Status: **CONFIRMED**

2. **SHA-256 Hash Recomputation:**
   - Computed via `shasum -a 256` under `claudedocs/exec-012-dr04-amend-030/` [Observed]:
     - `SUPERVISOR_RETURN.json`: `53e24df158979555674087f9c9b304b73a373f64a60f6437ca8bb3e2356803b1` (MATCH)
     - `SUPERVISOR_HANDOFF.md`: `b896c9ba676f65c3380f33d30bcdf1d9fc4e141c06725d9af120bb780d7802e2` (MATCH)
     - `README.md`: `547ea8f0df195dfb5fe575576c3d448be992895657611ba4c799acfc013eee3a` (MATCH)
     - `CHECKPOINT.md`: `5b7503eaab9debe5346895b3e3b816c6f90c8959b198ab89c2f20fe758bf66d9` (MATCH)
     - `evidence/D_APIROUTE_PROBE.json`: `61e22c381a424e756c8ba54ee5ba042f5cab995e891e8898f6a4a28614afadd6` (MATCH)
     - `ERRATA/DEFECT-001-narration-preface-count.json`: `7fe74e8607c70aed7fc4a25227e53001d2060c3573140581df2d69b043b11aa7` (MATCH)
     - `ERRATA/DEFECT-002-unknown-tool-event-contract.json`: `7a8819b88bf8fd2c8b107d857366871d5e2d8b1d7c95d2f4ea4fccc031fb4ee8` (MATCH)
     - `ERRATA/PATH_MAP.json`: `34c044c9848c1a9467e2b87ee67075ea77aafb86b2625e1af01cae55bd7ccbcb` (MATCH)
     - `ERRATA/ROUTE_RECORD.json`: `723c1ab071d806b17929ab62abdbc459f18631a0db5c47fc27d7ffe50d25c4e1` (MATCH)
     - `ERRATA/DISCLOSURE_RECONFIRMATION.md`: `b92cccd80a415c6a7d66dff1810580c08b8b24da6f0fdc6a847fb62e5590f360` (MATCH)
     - `ERRATA/ERRATA.md`: `33343737428a7cc6c50786e99cf3b47def1b5b6b87a56e7122f99af3b7917807` (MATCH)
   - Status: **PASS**

---

## 1. Challenge of Fifteen Points

### Point 1: Record-Tier Immutability
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Executed `git diff --name-only bc4249ee d39d06bcb -- claudedocs/exec-012-dr04-amend-030/route_d claudedocs/exec-012-dr04-amend-030/shared_contracts`. Result: empty (0 changed files).
  - Executed `git diff --name-only bc4249ee d39d06bcb -- claudedocs/exec-012-dr04-amend-030/evidence`. Result: only `evidence/D_APIROUTE_PROBE.json`.
  - Detailed diff of [evidence/D_APIROUTE_PROBE.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/evidence/D_APIROUTE_PROBE.json#L40-L52) shows only narrative/analytical fields (`material_finding` and `served_model_attestation`) were edited to withdraw unsupported inferences; measured counters and probe run parameters were not altered. The record/claim boundary is strictly enforced.

### Point 2: Corrected Spend Ledger
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Primary source totals in [SUPERVISOR_RETURN.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/SUPERVISOR_RETURN.json#L149-L173), [evidence/D_DISPATCH_RESULT.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/evidence/D_DISPATCH_RESULT.json#L47-L77), [evidence/D_DISPATCH_RESULT_ATTEMPT_02.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/evidence/D_DISPATCH_RESULT_ATTEMPT_02.json#L34-L39), [evidence/D_DISPATCH_RESULT_ATTEMPT_03.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/evidence/D_DISPATCH_RESULT_ATTEMPT_03.json#L48-L54):
    - Input tokens: $224,907 + 58,065 + 489,388 = 772,360$.
    - Output tokens: $1,595 + 392 + 3,937 = 5,924$.
    - Route D cost at assumed $\$10/\$50$ per M:
      - Attempt 1: $224,907 \times \$10/\text{M} + 1,595 \times \$50/\text{M} = \$2.3288 \rightarrow \$2.33$. The prior $\$2.22$ was unsupported by the record.
      - Attempt 2: $58,065 \times \$10/\text{M} + 392 \times \$50/\text{M} = \$0.60025 \rightarrow \$0.60$.
      - Attempt 3: $489,388 \times \$10/\text{M} + 3,937 \times \$50/\text{M} = \$5.09073 \rightarrow \$5.09$.
      - Route D Subtotal: $\$2.33 + \$0.60 + \$5.09 = \$8.02$.
    - API-route probe: 10,902 in / 21 out $= \$0.11007 \rightarrow \$0.11$. Correctly isolated outside `token_totals`.
    - Total estimated spend: $\$8.02 + \$0.11 = \$8.13$. Remaining against $\$10.00$ ceiling: $\$1.87$. The prior $\$8.28$ headline is withdrawn.
    - Residual uncertainty: earlier $\sim 8,235$-token cost-floor probe ($\sim \$0.08$) explicitly noted as uncounted in `SUPERVISOR_RETURN.json` line 167; $\$8.13$ is documented as an estimated cost floor.

### Point 3: Model Identity Separation
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Both [SUPERVISOR_RETURN.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/SUPERVISOR_RETURN.json#L113-L119) and [evidence/D_APIROUTE_PROBE.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/evidence/D_APIROUTE_PROBE.json#L47-L52) define four distinct fields: `requested_model="gpt-6-astra"`, `catalog_availability="OBSERVED_PRESENT"`, `served_model="UNKNOWN"`, and `provider_fallback="UNKNOWN"`.
  - Trailing inference that catalog availability proved absence of fallback is explicitly withdrawn in both files and indexed in [ERRATA/ERRATA.md](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/ERRATA/ERRATA.md#L56-L66) (E2).
  - Grep across all bundle files reveals no residual assertion claiming served model identity is known.

### Point 4: Mutation Accounting
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - [SUPERVISOR_HANDOFF.md](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/SUPERVISOR_HANDOFF.md#L151-L157) splits mutations into benchmark/audited-original mutations (0) vs operator-authorized publication mutations (1 repo, 1 GitHub).
  - Matches [SUPERVISOR_RETURN.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/SUPERVISOR_RETURN.json#L17-L33) `GATES_AND_MUTATIONS` (`repository_mutations_made: 1`, `github_mutations_made: 1`).
  - Supersession of packet gate `GITHUB_MUTATION_AUTHORIZED=NO` by operator instruction on 2026-09-10 is disclosed prominently in `SUPERVISOR_RETURN.json` line 19, `SUPERVISOR_HANDOFF.md` line 155, and `ERRATA/ERRATA.md` item E3.

### Point 5: Turn Accounting
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Directory inspection of `route_d/attempt_*/loop_state/`:
    - `attempt_01/loop_state/`: `codex_01.json`, `codex_02.json`, `codex_03.json` (3 turns).
    - `attempt_02/loop_state/`: `codex_01.json` (1 turn).
    - `attempt_03/loop_state/`: `codex_01.json` through `codex_06.json` (6 turns).
    - Sum: $3 + 1 + 6 = 10$ live codex turns.
  - Receipt count: 2 in attempt 1 (`turn_01_receipt.json`, `turn_02_receipt.json`), 1 in attempt 2, 6 in attempt 3. Total: 9 receipts.
  - Attempt 1 turn 3 wrote no receipt due to `CODEX_COMPLETION_AMBIGUOUS` exception before persist; usage (85,082 in, 558 out) is explicitly sourced to [evidence/D_DISPATCH_RESULT.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/evidence/D_DISPATCH_RESULT.json#L64-L68) `SPEND.turn_03` (parsed from `turn_03_native.json`), not estimated or inferred.

### Point 6: Scan-Scope Correction
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - 245 files = working tree at `/private/tmp/DMX-DR04-EXEC-012-AMEND-030` prior to reaping.
  - 75 files = pre-publication scan of staged subset before `SUPERVISOR_RETURN.json` was written.
  - 76 files = actual committed file count at `bc4249ee` (verified via `git ls-tree -r bc4249ee -- claudedocs/exec-012-dr04-amend-030 | wc -l`).
  - Explanation in [ERRATA/ERRATA.md](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/ERRATA/ERRATA.md#L103-L109) (E6) and `SUPERVISOR_RETURN.json` line 177 is consistent, clear, and accounts for all counts without evasion.

### Point 7: Provenance / Path Map
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Records retain their true historical working-tree paths (`W01/...`). Rewriting records would misrepresent execution history.
  - [ERRATA/PATH_MAP.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/ERRATA/PATH_MAP.json#L8-L23) maps all 7 `W01/...` citations to `shared_contracts/...` and explicitly catalogues 5 cited-but-uncommitted paths (`W02/...`, `research_loop.py`, `RUN_ROUTE_A_FROM_TERMINAL.command`, `W07/`), noting their working-tree disposition.

### Point 8: DEFECT-001 (Narration Preface Count)
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Inspected [shared_contracts/message_arity.py](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/shared_contracts/message_arity.py#L63): `return conforming[0], len(kept), len(kept) - 1`. If conforming item is not last, suffix narration is mislabelled as preface.
  - Preservation rationalized: `message_arity.py` is a record of code in force during attempt 3; modifying it in an evidence bundle would falsify the run conditions.
  - Receipt verification: Inspected all 6 receipts in attempt 3 and the 1 receipt in attempt 2; all 7 report `narration_preface_count=0` and `agent_message_count=1`. Attempt 1 turn 3 had the structure `[prose preface, valid JSON]` (prefix order where `len(kept)-1=1` is correct) and wrote no receipt. **Zero committed receipts carry a wrong value.**

### Point 9: DEFECT-002 (Unknown Tool Event Contract)
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Inspected [shared_contracts/W01_TOOL_EVENT_CLASSIFIER.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/shared_contracts/W01_TOOL_EVENT_CLASSIFIER.json#L132-L142): `verdict_contract` defines branches for `on_any_forbidden_event` and `on_zero_forbidden_events`, leaving unknown types unhandled despite declaring `FAIL_CLOSED_ALLOWLIST`.
  - Preserved unapplied because the artifact is sealed under the 028 manifest; patching it in the evidence bundle would corrupt contract integrity.
  - [ERRATA/DEFECT-002-unknown-tool-event-contract.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/ERRATA/DEFECT-002-unknown-tool-event-contract.json#L20-L24) honestly records that across all 10 live turns only allowlisted types (`thread.started`, `turn.started`, `item.completed`, `turn.completed`, `agent_message`, `reasoning`) appeared, and admits implementation behaviour for unknown types remains **UNKNOWN** from bundle artifacts alone.

### Point 10: Public Disclosure
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Parsed all receipts via script: exactly 9 receipts contain the raw `/v1/models` JSON response in `stderr`.
  - Each receipt contains exactly 136 model identifiers with `owned_by` and `shutdown_date`.
  - Inspected `evidence/D_APIROUTE_PROBE.stderr_summary.txt`: truncated at 227 bytes; carries no model list.
  - Scripted regex scan across `claudedocs/exec-012-dr04-amend-030/` confirms zero live credentials.

### Point 11: Operator Risk Acceptance
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - [ERRATA/DISCLOSURE_RECONFIRMATION.md](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/ERRATA/DISCLOSURE_RECONFIRMATION.md#L107-L136): Operator risk acceptance granted 2026-09-11 by repository owner (`DDD-Enterprises`), with explicit settings (`DISCLOSURE_DECISION=RECONFIRM_PUBLICATION_UNMODIFIED`, `REDACTION_AUTHORIZED=NO`, `HISTORY_REWRITE_AUTHORIZED=NO`, `CLOSE_PR_AUTHORIZED=NO`).
  - Analysis of removal options is technically accurate: `refs/pull/1341/head` is an independent Git ref on a public GitHub repository. Closing PR #1341 or force-pushing branch history does not delete pull refs or eradicate cached/forked commit objects without GitHub Support purge.

### Point 12: `POLICY_COMPLIANT=NO`
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - [SUPERVISOR_RETURN.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/SUPERVISOR_RETURN.json#L29), [ERRATA/ERRATA.md](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/ERRATA/ERRATA.md#L133-L135), and [ERRATA/DISCLOSURE_RECONFIRMATION.md](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/ERRATA/DISCLOSURE_RECONFIRMATION.md#L109-L113) uniformly declare `POLICY_COMPLIANT=NO`, `POLICY_EXCEPTION_REQUIRED=YES`, `SECURITY_RISK_OWNER=OPERATOR`.
  - Artifacts strictly frame disclosure as a bounded operator policy exception and explicitly forbid downstream auditors from reporting it as compliance.

### Point 13: Primary Route-D Finding
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - Inspected all 6 turns of Attempt 3:
    - Turns 1, 3, 5: `web_search` actions.
    - Turns 2, 4, 6: `web_fetch` actions.
    - Total: 3 `web_search` + 3 `web_fetch` $= 6$ retrieval slots spent.
  - Frozen harness limits: `limits.codex = 6`. In `research_loop.py`, each turn executes either a retrieval action or emits `final`.
  - Model was provided the retrieval allowance (3 + 3) in `request_payload`, but the 6-turn codex ceiling was never disclosed to the model.
  - Consuming the full retrieval allowance exhausted all codex turns, leaving 0 turns to emit `final`.
  - Finding is correctly identified as a structural defect in the route retrieval budget rather than model failure.

### Point 14: Accurate Representation Without Overclaiming
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - PR states `MACRO_STATUS="PARTIAL_RETURN_TO_SUPERVISOR"`.
  - `FOUR_ROUTE_COMPARISON` is explicitly `NO` (only Route B produced a research artifact; Route A never ran; Route C remains blocked; Route D produced no report).
  - Route A is explicitly reported as `BLOCKED_TOPOLOGY_NEVER_REACHED_A_PROVIDER` (0 calls, $\$0.00$ spend). No success or completion claims are made.

### Point 15: Authority Boundaries
- **Status:** **UPHELD**
- **Evidence:** [Observed]
  - [SUPERVISOR_RETURN.json](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/SUPERVISOR_RETURN.json#L20-L21) records `ADOPTION_AUTHORIZED="NO. Nothing adopted."` and `ACTIVATION_AUTHORIZED="NO. Nothing activated."`.
  - [README.md](file:///Users/hue/code/dopemux-mvp/.worktrees/exec012-evidence/claudedocs/exec-012-dr04-amend-030/README.md#L37-L38) confirms work was performed on a revertible copy with no activation.
  - Bundle claims no merge, adoption, or activation authority, leaving all policy and budget actions under `OPEN_ITEMS_FOR_THE_SUPERVISOR`.

---

## 2. Risk Enumeration

1. **Public Disclosure of Account Model Catalog:**
   - Nine turn receipts embed raw `/v1/models` JSON carrying 136 model identifiers in a public repository.
   - **Status:** **OPERATOR-ACCEPTED** (`OPERATOR_RISK_ACCEPTANCE=YES`, documented in `ERRATA/DISCLOSURE_RECONFIRMATION.md`).
2. **Latent Prefix Narration Indexing Defect (DEFECT-001):**
   - `shared_contracts/message_arity.py` mislabels suffix narration as preface.
   - **Status:** **OPERATOR-ACCEPTED / RECORDED UNAPPLIED** (no committed receipts affected; deferred to successor working surface).
3. **Underspecified Tool Event Classifier Fail-Closed Contract (DEFECT-002):**
   - `shared_contracts/W01_TOOL_EVENT_CLASSIFIER.json` lacks explicit verdict branch for unknown types.
   - **Status:** **OPERATOR-ACCEPTED / RECORDED UNAPPLIED** (unexercised in runs; deferred to -031 classifier revision).
4. **Estimated Spend Floor Uncertainty:**
   - Pre-benchmark $\sim 8,235$-token cost-floor probe ($\sim \$0.08$) uncounted in token totals.
   - **Status:** **OPERATOR-ACCEPTED / DOCUMENTED** ($8.13 reported as floor against $\$10.00$ ceiling).

---

```
MODEL_REQUESTED=gemini-3.8-flash-high
MODEL_RESPONSE_CLAIMED=Gemini 3.8 Flash (High)
MODEL_PROVIDER_ATTESTED=UNKNOWN
EFFORT_REQUESTED=high
EFFORT_OBSERVED=high (extended chain-of-thought observed)
HASH_RECOMPUTATION=PASS
CUSTODY_HEAD_CONFIRMED=yes
POINTS_UPHELD=15 of 15
POINTS_DISPUTED=0
POINTS_UNVERIFIABLE=0
NOVEL_UNACCEPTED_RISKS=none
VERDICT=PASS_WITH_RISKS
```
