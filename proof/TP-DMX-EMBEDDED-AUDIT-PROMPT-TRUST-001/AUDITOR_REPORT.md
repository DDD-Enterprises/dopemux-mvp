# Embedded Audit Report — AGY + Gemini

- auditor_tool: agy
- requested_model: gemini-3.1-pro-high
- settings_model: Gemini 3.1 Pro (High)
- backend_model_label: Gemini 3.5 Flash (Medium)
- verdict: PASS_WITH_RISKS
- head: 7041f128adbf5883675b4f797ab4bdda3c8faa58
- PR: 1082
- invocation: `agy --model gemini-3.1-pro-high -p <trusted-prompt> --effort high --sandbox --mode plan (settings: model=Gemini 3.1 Pro High, toolPermission=require-permission)`

## Rationale
Inspected the prompt trust boundaries, delimiter neutralization, instruction-like content scanning, and verdict evidence requirements implemented in PR 1082. The design separates untrusted candidate diffs/metadata from trusted instructions, prevents delimiter spoofing via neutralization, and requires concrete evidence (rationale, inspected paths, evidence refs, and scanner acknowledgement) to issue a PASS verdict. All unit tests and schema validations are reported passing by the implementer.

## Findings
- INFO F-DMX-EMBEDDED-AUDIT-PROMPT-TRUST-001: Instruction-like content detected in test fixtures and code

## Remaining risks
- Regex-based scanner is not a complete guarantee against obfuscated or novel prompt-injection attacks; however, the multi-layered defense (delimiter neutralization, prompt repetition, and enforcements on PASS verdicts) mitigates this risk effectively.
- Deterministic scanner matches on benign test fixtures and documentation, which requires auditor review and manual acknowledgement. This is an accepted operational trade-off to ensure safety.
- Instruction-like candidate content was detected by the deterministic scanner (match_count=17); treated as evidence only, not automatic failure.

## Instruction-like content
- detected=True match_count=17
