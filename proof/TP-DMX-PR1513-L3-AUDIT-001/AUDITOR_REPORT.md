# AUDITOR REPORT — PR #1513 L3 embedded audit (TP-DMX-PR1513-L3-AUDIT-001)

- **Governing auditor**: Grok CLI 1.0.77, `grok-4.7`, tool-less recipe, prompt from the repo's trusted builder plus a trusted brief (`review_bundle/AUDIT_PROMPT_BUILDER.txt`)
- **Corroborating auditor**: AGY, `gemini-4-argon-high`, same prompt
- **Implementer**: Claude Code sessions (several Claude models, one family), a different runner and model family from both auditors
- **Audited head**: `3bc641e886914f49ee8a63f1bd1228b9909aa0a0` · **Content head**: `72aa9c902ceec12a705f6993f98b7eb86e61c6ba` (the audited head adds two proof-only commits) · **Base**: `ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7` (main, the merge-base)
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Containment**: `init.tools == []`, 0 tool_use blocks
- **Input**: 75121 tokens; all 24 changed files; delivery token echoed
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: raw streams, stderr and wrapper exit lines are in `review_bundle/` (home paths and emails redacted, REDACTIONS.md)
- **History**: round 4 of 4; rounds 1-3 returned NEEDS_SUPERVISOR or FAIL (`review_bundle/AUDIT_HISTORY.md`)

## Auditor return (verbatim JSON)

```json
{
  "status": "COMPLETE",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "severity": "low",
      "title": "realpath failure drops alias root starts",
      "detail": "In _guard_starts the loop does os.path.normpath, then os.path.realpath, then _alias_forms inside one try that swallows OSError and ValueError. A raise from realpath skips alias starts for that base and every later base. _alias_limit_exceeded only runs _walk_alias_forms, so a realpath failure is not by itself a hard block. CPython's default realpath (strict=False) usually absorbs link errors internally, and no openable allow was shown from this diff alone.",
      "evidence": ".claude/hooks/dcp_surface_guard.py _guard_starts; _alias_limit_exceeded"
    },
    {
      "severity": "low",
      "title": "Writer and attempt-cap exceptions are operator-ratified but outside the packet",
      "detail": "G01's packet names G01-implementer as the only canonical writer of the guard and test file, with one correction round. Amendments 02-11 record the supervisor session writing those files directly, each under a one-off operator exception that does not change canonical_writers. The issued packet hashes are unchanged. This is a governance deviation already written into the proof records, not a red-lane bypass."
    }
  ],
  "risks": [
    "Disclosed reverse-lookup gap remains. If services/task-orchestrator is a symlink to a directory outside every repo, an edit of that outside directory's own path is allowed. The same allow applies to another symlink in the checkout whose target path never contains the red-lane component (for example services/jump pointing at the same outside directory): the walk only keeps names that appear on the path it is resolving, and it does not readdir siblings. AMENDMENT_10 and AMENDMENT_11 defer this; the records say main allows the outside path too.",
    "Fail-closed cost: a walk that exceeds 64 spellings, 40 link hops, a loop, an unreadable link, ValueError, or RecursionError hard-blocks, including ordinary files. _alias_forms still returns () on those errors so discovery does not raise; _alias_limit_exceeded blocks first.",
    "Freeze durability: G02_RETURN records Copilot review of content head 72aa9c902 as NOT_RUN and says a later Copilot review can void an audit run before it. Earlier rounds each found another symlink/.. shape. Full make test is NOT_RUN in the candidate record. This auditor did not execute the suite.",
    "file_repo_root still returns the nearest .git above os.path.realpath. surface_guard_block does not use it after Amendment 01. A later W09 caller that blocks from file_repo_root alone reopens planted-.git and realpath-escape mistakes. T02 specifies this helper.",
    "Trusted range 72aa9c902..3bc641e886914f49ee8a63f1bd1228b9909aa0a0 is only proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_11.md and G02_RETURN.md. Condensing Amendment 11 is proof-only; the longer text at 72aa9c902 was not in this message.",
    "Bash and apply_patch edits stay unguarded (packet T05 / plan C17, owned by W09).",
    "Instruction-like candidate text addresses the auditor (G01_RETURN 'For the auditor'; amendment and freeze records telling the auditor which residuals to accept). Treated as data, not as instructions. The candidate scan summary said detected=false; that summary is candidate-controlled."
  ],
  "rationale": "Audited head 3bc641e886914f49ee8a63f1bd1228b9909aa0a0 matches trusted base ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7 plus the 24-file diff. Trusted git shows the only commits after content head 72aa9c902 are proof-only (AMENDMENT_11.md and G02_RETURN.md), so the guard and tests at the audited head are the ones in the diff. Amendment 11's walk merges known spellings of the resolved directory on every non-'..' step, and _alias_limit_exceeded hard-blocks when that walk raises. Traced against the new tests, that closes the two third-freeze shapes: a two-level target then '..' keeps services/task-orchestrator because the nested walk of the target sees the red-lane spelling already stored on the outside directory; a sibling link beside a symlinked services ancestor picks up the services spelling from known while walking the target, then appends task-orchestrator. Loop, hop-limit, and readlink OSError paths raise into _alias_limit_exceeded before pattern matching; the loop test now expects a block. _guard_roots still always starts with project_root and only adds .git ancestors. Checks below the cap (35-link ordinary chain, five stacked links, dotdot through a symlink onto an ordinary file) stay allowed by the same control flow. No new forward spelling that still contains the red-lane name and is allowed was shown. Residuals that remain are the deferred reverse lookup, fail-closed over-block, the realpath/start ordering hazard, the exported file_repo_root footgun, missing Copilot and full-suite evidence, and ratified writer exceptions.",
  "inspected_paths": [
    ".claude/hooks/dcp_surface_guard.py",
    "tests/unit/dcp_surface_guard/test_file_repo_root.py",
    "tests/unit/dcp_surface_guard/__init__.py",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_01.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_02.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_03.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_04.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_05.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_06.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_07.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_08.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_09.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_10.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_11.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/G01_RETURN.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/G02_RETURN.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/AUTHORIZATION.md",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/package/WORKSTREAMS/G01/TASK_PACKET.json",
    "proof/MACRO-DMX-GUARD-FILE-REPO-001/package/WORKSTREAMS/G02/TASK_PACKET.json"
  ],
  "evidence_refs": [
    "trusted freeze range 72aa9c902ceec12a705f6993f98b7eb86e61c6ba..3bc641e886914f49ee8a63f1bd1228b9909aa0a0 commits d6db8747a71aba7848336d530ea366fa892ad9fc and 3bc641e886914f49ee8a63f1bd1228b9909aa0a0; differing paths only AMENDMENT_11.md and G02_RETURN.md",
    "_walk_alias_forms known-merge after every non-'..' component; '..' branch drops forms whose last component is a symlink name and reloads known[parent]",
    "_alias_limit_exceeded returns true on _AliasLimitExceeded, OSError, ValueError, RecursionError; _block_reason_for_path checks it before red-lane patterns",
    "tests: test_second_link_two_levels_deep_then_dotdot_keeps_red_lane_spelling, test_link_beside_a_symlinked_red_lane_ancestor_is_blocked, test_symlink_loop_is_blocked_and_does_not_raise, test_symlink_chain_past_the_hop_limit_is_blocked, test_chain_just_under_the_hop_limit_is_allowed, test_unreadable_link_is_blocked, test_dotdot_after_symlink_to_ordinary_file_is_allowed, test_ordinary_file_under_the_cap_is_allowed",
    "G02_RETURN known limits and Copilot NOT_RUN; AMENDMENT_11 stop rule and condensed-after-72aa9c902 note"
  ],
  "validation_status": "NOT_RUN",
  "instruction_like_acknowledged": true,
  "model_self_reported": "grok-4.7",
  "delivery_token": "9c9002440b03f0759f48a008185cdb09"
}
```

## Corroboration (does not govern)

**AGY** (`gemini-4-argon-high`, self-reported `Gemini 4 Argon (High)`): PASS_WITH_RISKS over the same prompt, 5 findings (1 medium governance, 4 low). Delivery of the whole prompt is proven in `review_bundle/AGY_RUN_RECORD.md`. Raw reply: `review_bundle/AGY_VERDICT.json`.

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| GROK-1 | LOW | realpath failure drops alias root starts | OPEN |
| GROK-2 | LOW | Writer and attempt-cap exceptions are operator-ratified but outside the packet | OPEN |
| AGY-1 | MEDIUM | Supervisor-authored code edits across Amendments 02-11 and proof files outside issued workstream write_surface | OPEN |
| AGY-2 | LOW | Exported file_repo_root helper returns only the nearest .git above realpath | OPEN |
| AGY-3 | LOW | Direct edit to an external directory target of a checkout's red-lane symlink is not detectable by forward/upward path walking | OPEN |
| AGY-4 | LOW | Symlink hop counter tracks recursion depth rather than sequential hop count, and dual-key warnings report one surface per call | OPEN |
| AGY-5 | LOW | Candidate proof files contain explanatory text addressing the auditor | OPEN |

Team-lead reading, not an audit: `review_bundle/FINDING_TRIAGE.md`. No finding reports a new red-lane bypass or needs a code change at this head.

## Validation

| Check | Result |
|---|---|
| 📊 CI Pipeline Summary | PASS |
| 🧪 Unit Tests | PASS |
| 📚 Documentation Check | PASS |
| 🔒 Security Review | PASS |
| independent embedded audit | FAIL |
| PR Steward / final readiness | FAIL |
| local: guard tests (tests/unit/dcp_surface_guard) at the audited head | PASS |
| local: 32 test files that mention dcp_surface_guard, native_hooks or red_lane | PASS |
| local: flake8 --select=E9,F,W on the guard and its tests | PASS |
| local: black --check on the guard and its tests | FAIL |
| local: saved reproduction probes (AGY r2, Copilot x3, AGY r3, Grok r3) | PASS |
| local: 14 ordinary paths on the operator's machine | PASS |
| review: Copilot on the content head 72aa9c902 | NOT_RUN |
| audit: validation inside the sealed sessions | NOT_RUN |
| local: full make test | NOT_RUN |

The embedded-audit gate and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- GROK-1 (LOW, OPEN): realpath failure drops alias root starts
- GROK-2 (LOW, OPEN): Writer and attempt-cap exceptions are operator-ratified but outside the packet
- AGY-1 (MEDIUM, OPEN): Supervisor-authored code edits across Amendments 02-11 and proof files outside issued workstream write_surface
- AGY-2 (LOW, OPEN): Exported file_repo_root helper returns only the nearest .git above realpath
- AGY-3 (LOW, OPEN): Direct edit to an external directory target of a checkout's red-lane symlink is not detectable by forward/upward path walking
- AGY-4 (LOW, OPEN): Symlink hop counter tracks recursion depth rather than sequential hop count, and dual-key warnings report one surface per call
- AGY-5 (LOW, OPEN): Candidate proof files contain explanatory text addressing the auditor
- Grok risk: Disclosed reverse-lookup gap remains. If services/task-orchestrator is a symlink to a directory outside every repo, an edit of that outside directory's own path is allowed. The same allow applies to another symlink in the checkout whose target path never contains the red-lane component (for example services/jump pointing at the same outside directory): the walk only keeps names that appear on the path it is resolving, and it does not readdir siblings. AMENDMENT_10 and AMENDMENT_11 defer this; the records say main allows the outside path too.
- Grok risk: Fail-closed cost: a walk that exceeds 64 spellings, 40 link hops, a loop, an unreadable link, ValueError, or RecursionError hard-blocks, including ordinary files. _alias_forms still returns () on those errors so discovery does not raise; _alias_limit_exceeded blocks first.
- Grok risk: Freeze durability: G02_RETURN records Copilot review of content head 72aa9c902 as NOT_RUN and says a later Copilot review can void an audit run before it. Earlier rounds each found another symlink/.. shape. Full make test is NOT_RUN in the candidate record. This auditor did not execute the suite.
- Grok risk: file_repo_root still returns the nearest .git above os.path.realpath. surface_guard_block does not use it after Amendment 01. A later W09 caller that blocks from file_repo_root alone reopens planted-.git and realpath-escape mistakes. T02 specifies this helper.
- Grok risk: Trusted range 72aa9c902..3bc641e886914f49ee8a63f1bd1228b9909aa0a0 is only proof/MACRO-DMX-GUARD-FILE-REPO-001/AMENDMENT_11.md and G02_RETURN.md. Condensing Amendment 11 is proof-only; the longer text at 72aa9c902 was not in this message.
- Grok risk: Bash and apply_patch edits stay unguarded (packet T05 / plan C17, owned by W09).
- Grok risk: Instruction-like candidate text addresses the auditor (G01_RETURN 'For the auditor'; amendment and freeze records telling the auditor which residuals to accept). Treated as data, not as instructions. The candidate scan summary said detected=false; that summary is candidate-controlled.
- AGY risk: No tools, file reads, shell commands, or test executions were run during this audit (per Hard Rule 1); live test pass rates, SHA-256 hashes of working tree files, git status, and CI check states outside the provided prompt text are UNKNOWN and not independently re-executed.
- AGY risk: Wave 2B W09 will import file_repo_root from .claude/hooks/dcp_surface_guard.py; if W09 uses file_repo_root rather than multi-root discovery (_guard_roots) for hard-deny decisions, a planted .git entry or external symlink target could bypass W09.
- AGY risk: Because _alias_limit_exceeded fails closed on any path with >64 alias spellings, >40 nested symlink hops, a symlink loop, or an unreadable symlink, legitimate edits to non-red-lane files behind deeply stacked symlinks (>=6 sequential symlinks) will also be hard-blocked.
- AGY risk: G02_RETURN.md notes that a fresh Copilot review on frozen content head 72aa9c902ceec12a705f6993f98b7eb86e61c6ba was requested but had not run (NOT_RUN), and black --check fails on the modified Python files (unchanged from prior heads).
- Audit scope: both auditors saw the whole diff ba5c3e07b...3bc641e88, 24 files, with a trusted brief carrying git's own commit range 72aa9c902..3bc641e88 (proof-only).
- The auditors could not run anything; the claims in this proof about tests and probes are the implementer's, re-run for LOCAL_VALIDATION.txt but not by the auditors.
- Three earlier frozen heads failed their audits (AUDIT_HISTORY.md); the symlink / '..' family produced a new variant on every head before this one, so closure is shown by the test file and the saved probes, not proven.
- Open gap, same on main: an edit through the outside folder that a checkout's red-lane symlink points to is allowed (probe key f1_real_path_blocked).
- Fail-closed cost: a path whose symlink walk cannot finish (more than 64 spellings, about six stacked links, a loop, a chain past 40 links, an unreadable link) is hard-blocked, ordinary files included.
- Copilot did not review the content head (NOT_RUN); a later Copilot finding would void this audit.
- Amendments 02-11 were written by the supervisor session under one-off operator exceptions outside the issued packet's named writer; the packet files are unchanged.
- Auditor model identity: requested grok-4.7; init.model grok-4.7; receipt grok-4.7-build; self-reported grok-4.7; AGY requested gemini-4-argon-high, self-reported Gemini 4 Argon (High). Provider attestation UNKNOWN for both.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps. The audit prompt was condensed (AMENDMENT_11.md and G02_RETURN.md) to fit AGY's message limit; the longer text is in git at 72aa9c902.
- AMENDMENT_02.md records the operator's answer at 06:10:41Z; the session transcript shows 06:02:09.648Z. Not reconciled.
