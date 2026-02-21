# PROMPT_S3 - ARCHITECTURE PROOF HOOKS

ROLE: Verification planner.
MODE: Evidence-bounded conversion of claims into proof hooks.

GOAL:
- Produce proof hooks that map architecture claims to minimal verification suggestions.

OUTPUTS:
- S3_ARCH_PROOF_HOOKS.md

HARD RULES:
1) Do not rescan repo or claim commands were executed.
2) Every hook must cite claim evidence and expected verification signal.
3) Keep hooks minimal and deterministic.
4) If a hook cannot be defined from evidence, emit UNKNOWN with missing artifacts.

INPUTS (required):
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- S2_DECISION_DOSSIER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- TP_MERGED.json
- FREEZE_MANIFEST.json

OUTPUT FORMAT (write the full content of S3_ARCH_PROOF_HOOKS.md):
1) Claim to Proof Hook Table
- claim_id
- claim_statement
- evidence
- verification_command_suggestion
- expected_signal
- risk_link

2) Priority Proof Set
- Minimal high-value hooks for first execution.

3) UNKNOWN Hooks
- Claims lacking sufficient evidence to define checks.
