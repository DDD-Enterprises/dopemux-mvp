# Independent Embedded Audit - PR #1088

**Packet**: `PR-MERGE-STEWARD-1088`
**Repo**: `DDD-Enterprises/dopemux-mvp`
**Audited head**: `df1b67261876dbb57ae1ebe3ed024f007d0bbab8`
**Merge base**: `95264461d2d25b79baa0ded0ecbf6bf6b3343f10`
**Auditor**: Claude Code CLI (Sonnet), independent read-only session
**Verdict**: `PASS_WITH_RISKS`

## Scope

Auditor compared the exact-head diff against
`task-packets/TP-DMX-PAL-MODEL-REFRESH-001.json`. Changed paths and
`commit.allowlist` are set-equal at 24/24, with no extra or missing paths.

## Functional Review

- Responses request logging uses `copy.deepcopy` and replaces every input text
  and image URL in the log copy. Original request parameters remain unchanged.
- OpenRouter no longer registers `x-ai/grok-4` or aliases `grok-4`, `grok4`,
  and `grok`; regression coverage rejects each retired identifier.
- Grok 4.5 uses Responses routing, default reasoning effort `high`, supported
  temperature forwarding, and `store=false` for image requests.
- GPT-5.6 Sol, Terra, and Luna routing and capability behavior remain covered.
- Compose wiring references `${XAI_API_KEY}` rather than a literal credential.
- No secret-shaped API keys were introduced in the diff.

## Validation

- `python -m pytest -q tests/arch/test_pal_model_catalog_contract.py`: 6 passed.
- `pytest -q tests/test_xai_provider.py tests/test_openai_provider.py`: 41 passed.
- Wider changed PAL auto-mode and alias suite: 72 passed.
- Total targeted audit tests: 119 passed.
- Task Packet validation against `dopetask-canonical-spec.json`: PASS.
- `git diff --check <merge-base>..HEAD`: PASS.
- Exact changed-path/allowlist comparison: PASS, 24/24.
- Live provider probes: NOT_RUN; audit prohibited network access.

## Findings

1. **MEDIUM, accepted risk**: `pal-stdio` uses repository-root build context,
   whose existing `.dockerignore` lacks new key/certificate patterns. This is
   pre-existing and needs separate root-context hardening.
2. **MEDIUM, accepted risk**: nested PR Steward proof location conflicts with
   general `report_path` schema pattern. Trusted acceptance intentionally
   overrides this field; schema/convention reconciliation is separate work.
3. **LOW, accepted risk**: standalone PAL has additional model catalog and
   dynamic-selection changes outside this packet. Shared reviewer fixes are
   synchronized, but complete catalog convergence is not claimed.
4. **INFO, accepted risk**: `_extract_usage` records zero when `total_tokens`
   exists but is non-integer instead of summing input and output tokens.

## Proof Refresh

Prior proof targeted `26dd93931` and was stale after functional commit
`476b42002` plus main synchronization. This report and `PROOF.json` target exact
code head `df1b67261`. `fixes_applied` now uses schema-required string entries.
The subsequent proof commit must modify only this PR proof directory.

## Verdict

Functional implementation and reviewer remediations pass exact-head audit.
Carried risks are non-blocking but remain explicit. Verdict: `PASS_WITH_RISKS`.
