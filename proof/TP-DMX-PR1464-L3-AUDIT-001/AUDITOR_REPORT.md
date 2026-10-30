# AUDITOR REPORT — PR #1464 L3 embedded audit (TP-DMX-PR1464-L3-AUDIT-001)

- **Auditor**: grok 1.0.67 (2fe064390d07) [stable], `grok-4.5` (`--effort high`), operator-approved fallback route; empty tool list, replaced system prompt, sealed cwd holding only the prompt; prompt built by `scripts/audit/pal_clink_runner.py --build-prompt` (proof/** excluded)
- **Implementer**: Claude Code (Anthropic Claude); runner and model family differ from the auditor's.
- **Audited head**: `7908ae81cda75e6dfeffdd1e53a9f7037ff9cd81` · **Base**: `93050d135ffc2592000c1d0edef82b2912935525` (main)
- **Verdict**: **PASS_WITH_RISKS**
- **Observed identity**: grok session `01a1635a-f21c-7d21-a910-361f26fee1db`, `current_model_id=grok-4.5`, `reasoning_effort=high`
- **Containment**: init tools `[]`; tool_use blocks `[]`; system prompt replaced: True; sealed dir before/after `['AUDIT_PROMPT.txt']` / `['AUDIT_PROMPT.txt']`
- **Instruction-like scan**: detected=False, matches=0
- **Superseded attempts**: 1 (AGY 429, no verdict)

## Route approval

Operator chose the Grok route in Claude Code desktop session f10afffd-f9c0-4a2e-86ad-17f8109a3a3a on 2026-10-22 after the operator-approved AGY gemini-4-argon-high route returned HTTP 429 RESOURCE_EXHAUSTED with no verdict. grok-4.5 is the embedded_audit schema's exact Grok value; precedents PR #1420 and #1459.

Residual: Grok still injects home-level instruction files and the skill-name list as context (no secret values); changing that requires editing ~/.grok/config.toml, which was not authorized. MCP servers start but are unreachable because use_tool/search_tool are disallowed.

## Auditor return (verbatim JSON)

```json
{
  "status": "completed",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "severity": "low",
      "id": "F-repair-empty-old-text",
      "path": "scripts/check_docs_filename_hygiene.py",
      "summary": "run_repair calls rewrite_links_and_indices with old_text_by_path={} unlike run_apply, so placement/index rewrites after crash recovery may be weaker or behave differently than a clean --apply."
    },
    {
      "severity": "low",
      "id": "F-diverged-after-mutate",
      "path": "scripts/check_docs_filename_hygiene.py",
      "summary": "If planned vs completed rename sets diverge, run_apply still rewrites refs and overwrites the audit before returning 1, leaving a partially mutated tree with a non-zero exit."
    }
  ],
  "risks": [
    {
      "severity": "medium",
      "id": "R-import-re-uncertain",
      "summary": "New _compile_path_ref_pattern uses re.compile / re.Pattern but the shown import hunks only add hashlib and datetime. If import re was not already present, plain-ref rewrite raises NameError at runtime; new unit tests would catch this if executed."
    },
    {
      "severity": "medium",
      "id": "R-journal-trust",
      "summary": "--repair trusts journal JSONL (paths and sha256). A malicious or wrong journal can drive _safe_move under repo_root; main resolves args.repair via (repo_root / args.repair).resolve(), which accepts absolute paths outside the repo. Operator-trusted CLI surface, not remote."
    },
    {
      "severity": "low",
      "id": "R-toctou",
      "summary": "Preflight _exists_exact then later moves remain TOCTOU under concurrent deletion; journal + --repair mitigate crash windows but not hostile concurrent writers."
    },
    {
      "severity": "low",
      "id": "R-validation-not-run",
      "summary": "Auditor did not execute tests, import the module, or verify CI against head 7908ae81cda75e6dfeffdd1e53a9f7037ff9cd81; correctness of the new apply/repair paths is inferred from diff and test intent only."
    }
  ],
  "rationale": "PR 1464 hardens scripts/check_docs_filename_hygiene.py --apply with fail-closed missing-source preflight, fsync'd JSONL rename journal, sha256-checked --repair, case-exact existence on macOS, whole-token path-ref rewriting (longest-key-first, worktree skip prefixes, strict UTF-8 / byte-preserving writes), and audit retention via keep_previous. Accompanying tests/scripts/test_docs_filename_hygiene_apply.py exercises vanished-source fail-closed behavior, token-boundary rewrites, worktree non-touch, CRLF/BOM/non-UTF-8 preservation, mid-phase crash journal + idempotent repair, and CLI --repair parsing, all under tmp_path. No instruction-like content was reported by the scanner. Residual risks are operational (journal trust, possible missing re import not visible in hunks, repair rewrite asymmetry, validation not executed), not clear remote-exploitation defects in the diff, so PASS_WITH_RISKS rather than PASS or FAIL.",
  "inspected_paths": [
    "scripts/check_docs_filename_hygiene.py",
    "tests/scripts/test_docs_filename_hygiene_apply.py"
  ],
  "evidence_refs": [
    "trusted_audit_target: DDD-Enterprises/dopemux-mvp#1464 @ 7908ae81cda75e6dfeffdd1e53a9f7037ff9cd81 (base 93050d135ffc2592000c1d0edef82b2912935525)",
    "candidate_diff: apply_renames preflight FileNotFoundError; journal planned/temp/final + _append_journal fsync; run_repair sha256 gates; _compile_path_ref_pattern; _rewrite_plain_path_refs bytes/UTF-8 + .worktrees/ skips; write_audit keep_previous",
    "candidate_diff: tests F1 vanished source, F2 whole-token/chained/worktree, F3 CRLF/non-UTF-8, F4 crash journal+repair idempotency + CLI --repair",
    "instruction_like_scan_summary: detected=false match_count=0"
  ],
  "validation_status": "NOT_RUN"
}
```

## Normalization notes

- Findings keep the auditor's id, severity and summary; path/lines go into `body`. `status: OPEN` is set by the proof author: no risk acceptance is claimed (that is the owner's decision).
