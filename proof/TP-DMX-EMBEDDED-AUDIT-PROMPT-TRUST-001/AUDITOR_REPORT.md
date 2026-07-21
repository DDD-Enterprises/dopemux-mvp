# Embedded Audit Report — Claude Code CLI (Sonnet)

- auditor_tool: claude-code-cli
- auditor_model: sonnet
- verdict: PASS_WITH_RISKS
- head: df21b1a7509d0405c3382f3d6b047124227ed510
- PR: 1082
- invocation: `claude --print --safe-mode --no-session-persistence --tools "" --strict-mcp-config --model sonnet < trusted-prompt-full.md`
- duration: ~176s
- tools: disabled (`--tools ""` + `--strict-mcp-config`)

## Rationale
Reviewed the prompt-trust hardening change for PR #1082 (df21b1a7 vs bfc1b3bd) via full diffs plus the complete tools/auditor_router/pal_clink.py.FULL reference. The workflow now builds the auditor prompt through scripts/audit/pal_clink_runner.py --build-prompt, which delimits candidate metadata/diff between unique BEGIN/END markers, neutralizes candidate attempts to forge those exact delimiter tokens via _neutralize_delimiter_lookalikes (verified against the adversarial forged-delimiter test), repeats trusted instructions after the untrusted region, and enforces a required-evidence gate: normalize_pal_clink_audit_output._passing_verdict_evidence_errors now demotes PASS/PASS_WITH_RISKS payloads lacking nonempty rationale, inspected_paths/empty-diff evidence, evidence_refs, validation_status, or (when the deterministic scanner detected instruction-like content) an acknowledgement, to NEEDS_SUPERVISOR rather than SKIPPED. The deterministic scanner (scan_instruction_like_content) stores only path/line/category/sha256 of matched text, never raw candidate strings, verified by test_raw_matched_text_not_copied_into_proof and mirrored in embedded_audit.schema.json's instruction_like_content object (matches allow only category+text_sha256 required, additionalProperties false). Schema changes are additive/optional and do not weaken existing required fields. Codex-forbidden and tools/MCP-disabled invariants are unchanged in the workflow. I could not execute tests myself (tools disabled per this audit's own constraints), so I cross-checked the implementer's claimed pytest/schema validation against the actual test bodies added in tests/audit/test_run_embedded_audit.py (evidence-gate, scanner, neutralization, and emitter-preservation tests) rather than trusting the claim outright; the test logic matches the implementation's behavior as read.

## Findings
- **MEDIUM** `PROMPT-TRUST-01`: Scanner fails open in the workflow bootstrap fallback path (OPEN)
  - In .github/workflows/embedded-audit.yml, when scripts/audit/pal_clink_runner.py is absent, the fallback branch hardcodes INSTRUCTION_LIKE_CONTENT.json to {"detected":false,"match_count":0,...} even though the fallback prompt still embeds raw candidate metadata/diff between delimiters. This means the deterministic-scanner evidence gate silently reports no detection in that code path, even though in
- **LOW** `PROMPT-TRUST-02`: Scanner does not inspect deleted (-) diff lines that are still rendered to the model (OPEN)
  - scan_instruction_like_content only scans '+' (added) lines and metadata text; '-' lines are explicitly skipped ('Deleted lines are still candidate-controlled historically... Skip.'). However, build_trusted_audit_prompt embeds the full unified diff text (including '-' lines) verbatim in the untrusted section for the model to read. Instruction-like content placed only in removed/context lines would 

## Remaining risks
- Instruction-like candidate content was detected by the deterministic scanner in this packet's own review payload/fixtures (categories: FAKE_AUDIT_RESULT, FORCED_VERDICT_REQUEST, IGNORE_OR_OVERRIDE_INSTRUCTION, OUTPUT_CONTRACT_OVERRIDE, ROLE_OR_SYSTEM_PROMPT_CLAIM, SUPPRESS_FINDINGS_REQUEST; match_count=27, all inside the delimited/neutralized untrusted region). Treated as evidence of shape only, per the trusted contract, not as proof of malicious intent or automatic failure; acknowledged here.
- Scanner fails open (reports detected=false) in the no-runner bootstrap fallback workflow path even though raw candidate text is still embedded in the prompt (see PROMPT-TRUST-01). Delimiter/neutralization protections still hold in that path, but the evidence-gate signal is degraded.
- Scanner does not scan deleted diff lines, so instruction-like text placed only in removed/context lines is invisible to the evidence-gate acknowledgement mechanism even though it still reaches the model inside the untrusted region (see PROMPT-TRUST-02).
- tools/auditor_router/pal_clink.py.FULL was supplied as reference context alongside the diff but is not listed in changed_files and is not a file this audit can confirm will actually be committed to the repository; I relied on it only as a full-file cross-check of the diff hunks against tools/auditor_router/pal_clink.py, not as independent evidence of a separate change.
- The exact trusted delimiter string values were rendered redacted/neutralized in the material provided to me (e.g. '[REDACTED_DELIMITER:BEGIN TRUS…]'), so I cannot independently verify from this transcript alone that all seven DELIM_* constants are mutually unique, non-guessable strings as claimed by the module docstring — I can only verify the neutralization mechanism operates correctly on whatever the real values are, which the adversarial forged-delimiter test demonstrates.
- Passing-verdict evidence thresholds are soft (24-character rationale minimum, several alternate accepted key names for rationale/evidence/validation), which is a reasonable defense-in-depth floor but not a strong guarantee against a low-effort but technically-passing rationale from a future auditor run.
- Validation was not independently executed by this audit (tools and code execution are disabled per this audit's own trusted contract); pytest/schema-validation results are implementer-reported claims that I cross-checked against test source code logic but did not run.

## Instruction-like content
- detected=True match_count=27

## Notes
- First claude-audit route attempt used `--permission-mode plan` and asked A/B; re-ran without plan mode.
- Full gate source provided as text-only (tools intentionally empty).
- Prior AGY+Gemini local audit also PASS_WITH_RISKS.
