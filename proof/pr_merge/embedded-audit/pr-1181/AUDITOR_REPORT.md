# Independent Embedded Audit Report for PR #1181

- **PR Number**: 1181
- **Audited Content Head (C1)**: `96087405e045152a4ffb0681b4b9cb3673c354c2`
- **Auditor tool**: `claude-code-cli`
- **Auditor model**: `sonnet`
- **Implementer**: Grok (xAI)
- **Independence**: different-family
- **Status / Verdict**: `PASS_WITH_RISKS`
- **Packet**: TP-DMX-PORTFOLIO-TOOLTIP-CLOSURE-SALVAGE-002 Tranche B

## Scope observed

- `scripts/audit/pal_clink_runner.py`
- `tests/audit/test_pal_clink_runner.py`

## Summary

Clean, well-tested reimplementation of fail-closed fenced-JSON parsing for PAL clink audit stdout in scripts/audit/pal_clink_runner.py. parse_audit_json_object() correctly accepts only a bare full-output JSON object or exactly one full-output fenced JSON object (whitespace-only outside the fence), and rejects prose wrappers, brace-scraped substrings, multiple fence candidates, arrays/scalars, and malformed JSON by raising json.JSONDecodeError in every rejection path. _verdict_payload_from_output and _unwrap_tool_output_payload were updated to route through this helper, which fixes a real fail-open gap in the prior code: malformed/array/scalar model stdout used to be mapped to status='success' with the raw text as 'content', which is exactly the kind of output that could be misread downstream as a usable result. The new rejection path maps to status='error' with an explicit risks message, and never fabricates a 'verdict' key. Test coverage is thorough: direct-object, single-fence, prose-wrapper, brace-scraping, multi-fence, array/scalar, malformed, and nested-ambiguous-content cases are all exercised, plus an end-to-end test through normalize_pal_clink_audit_output confirming a rejected parse cannot surface as PASS/PASS_WITH_RISKS/READY. Reported local validation (100% pass, exit 0) is consistent with this analysis. No UI/tooltip changes are present in this diff despite the packet name.

## Findings

### F-001: Multiple-fence rejection is incidental, not structurally enforced

- severity: `LOW`
- status: `OPEN`

The fenced-JSON regex uses `\A\s*```(?:json)?...([\s\S]*?)...```\s*\Z` with re.fullmatch. When stdout contains two or more separate fenced blocks, the non-greedy capture group is forced by the \Z anchor to span from the first opening fence to the last closing fence, sweeping the second fence marker into the captured 'JSON' text. This currently produces malformed JSON (because a literal ```json marker breaks JSON syntax), so json.loads() fails and the input is correctly rejected in every constructed test case — but the rejection is a side effect of malformed JSON, not an explicit 'reject if more than one fence block is present' check. A contrived input where the swept-in fence marker happens to sit inside a string value (rather than breaking top-level JSON syntax) is a theoretical way to defeat this, though no such case is demonstrated or tested here.

### F-002: No explicit length guard before regex full-string match on model stdout

- severity: `LOW`
- status: `OPEN`

parse_audit_json_object() runs an unanchored-length regex fullmatch directly against the raw stdout string with no upper bound check. Matching cost here is roughly linear-to-quadratic in the pathological case (e.g., stdout consisting mostly of whitespace with a fence-like prefix), which is unlikely to matter for typical PAL clink audit output sizes but has no explicit size cap given the input originates from a model's own generated text (semi-adversarial by construction).

### F-003: Packet name references tooltip/UI closure work not present in diff

- severity: `INFO`
- status: `OPEN`

The task packet is named TP-DMX-PORTFOLIO-TOOLTIP-CLOSURE-SALVAGE-002, but the actual changed paths (scripts/audit/pal_clink_runner.py, tests/audit/test_pal_clink_runner.py) contain only backend JSON-parsing logic and tests — no tooltip, portfolio, or UI code. Flagging per hard-rule instruction not to claim UI/tooltip changes; this diff makes none.

## Remaining risks

- Multi-fence rejection depends on the swept-in fence marker breaking JSON syntax rather than an explicit single-fence structural check (see F-001).
- No test or guard exists for very large/pathological stdout inputs exercising regex backtracking cost (see F-002).
- Downstream status mapping in tools/auditor_router/pal_clink.normalize_pal_clink_audit_output is exercised by the new tests but is not itself part of this diff and was not independently audited here — its correctness is inferred from the reported test pass, not from reading its source in this review.

## Explicit non-claims

- No UI/tooltip changes.
- No merge or closure of #1171.
- Audit does not authorize merge.
