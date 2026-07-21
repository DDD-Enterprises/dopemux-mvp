# Embedded Audit Report — AGY + Gemini (post-repair)

- auditor_tool: agy
- auditor_model: gemini
- verdict: PASS_WITH_RISKS
- audited_code_sha: 245b598bf90cab02bf91cc03709be55d4e952074
- PR: 1082
- invocation: agy --model gemini-3.1-pro-high -p <trusted-prompt> --effort high --sandbox --mode plan (settings Gemini 3.1 Pro High, require-permission)

## Rationale
(see review_bundle/AGY_GEMINI_REPAIR_RAW.json)

## Findings
- None open

## Remaining risks
- Instruction-like candidate content was detected in the candidate diff (detected=true, match_count=19). This is acknowledged and verified to be benign, as the matched lines are contained entirely within the test fixtures (e.g. tests/audit/fixtures/prompt_trust/adversarial_candidate.diff) added to validate the new scanner and prompt trust boundary implementation.
