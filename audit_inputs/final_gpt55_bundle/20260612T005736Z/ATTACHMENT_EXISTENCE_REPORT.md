# Attachment Existence Report

generated_at_utc=2026-06-16T06:15:18Z
run_id=20260612T005736Z
status=COMPLETE_WITH_MISSING_INPUTS

## Required runtime recon

PRESENT: audit_inputs/dcp-runner-recon/GIT_RECON.txt
  - audit_inputs/dcp-runner-recon/GIT_RECON.txt

PRESENT: audit_inputs/dcp-runner-recon/OPEN_CODE_RECON.txt
  - audit_inputs/dcp-runner-recon/OPEN_CODE_RECON.txt

PRESENT: audit_inputs/dcp-runner-recon/GROK_BUILD_RECON.txt
  - audit_inputs/dcp-runner-recon/GROK_BUILD_RECON.txt

PRESENT: audit_inputs/dcp-runner-recon/ENV_PRESENCE_REDACTED.txt
  - audit_inputs/dcp-runner-recon/ENV_PRESENCE_REDACTED.txt

PRESENT: audit_inputs/dcp-runner-recon/DOPMUX_RECON.txt
  - audit_inputs/dcp-runner-recon/DOPMUX_RECON.txt

PRESENT: audit_inputs/dcp-runner-recon/DOPETASK_RECON.txt
  - audit_inputs/dcp-runner-recon/DOPETASK_RECON.txt

PRESENT: audit_inputs/dcp-runner-recon/MCP_RECON.txt
  - audit_inputs/dcp-runner-recon/MCP_RECON.txt

PRESENT: audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt
  - audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt

PRESENT: audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt
  - audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt

PRESENT: audit_inputs/dcp-runner-recon/RECON_SUMMARY.md
  - audit_inputs/dcp-runner-recon/RECON_SUMMARY.md

PRESENT: audit_inputs/dcp-runner-recon/RECON_FINDINGS.json
  - audit_inputs/dcp-runner-recon/RECON_FINDINGS.json

## Required source packet preservation

PRESENT: audit_inputs/gpt55_recon_source/CODEX_RECON_PACKS_SOURCE.md
  - audit_inputs/gpt55_recon_source/CODEX_RECON_PACKS_SOURCE.md

PRESENT: audit_inputs/gpt55_recon_source/CODEX_RECON_PACKS_SOURCE.sha256
  - audit_inputs/gpt55_recon_source/CODEX_RECON_PACKS_SOURCE.sha256

PRESENT: audit_inputs/gpt55_recon_source/CODEX_RECON_PACKS_SOURCE.linecount
  - audit_inputs/gpt55_recon_source/CODEX_RECON_PACKS_SOURCE.linecount

PRESENT: audit_inputs/gpt55_recon_source/README.md
  - audit_inputs/gpt55_recon_source/README.md

## Required orchestration evidence

PRESENT: audit_inputs/multi_model_orchestration_evidence/20260612T003401Z.zip
  - audit_inputs/multi_model_orchestration_evidence/20260612T003401Z.zip

PRESENT: audit_inputs/multi_model_orchestration_evidence/LATEST_RUN_ID.txt
  - audit_inputs/multi_model_orchestration_evidence/LATEST_RUN_ID.txt

PRESENT: audit_inputs/multi_model_orchestration_evidence/*/EVIDENCE_INDEX.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/EVIDENCE_INDEX.md

PRESENT: audit_inputs/multi_model_orchestration_evidence/*/tests/TEST_AND_CI_EVIDENCE.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/tests/TEST_AND_CI_EVIDENCE.md

PRESENT: audit_inputs/multi_model_orchestration_evidence/*/review/DRIFT_CONTRADICTION_LEDGER.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/review/DRIFT_CONTRADICTION_LEDGER.md

PRESENT: audit_inputs/multi_model_orchestration_evidence/*/MISSING_INPUTS_FOR_GPT55_PRO.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/MISSING_INPUTS_FOR_GPT55_PRO.md

## Required Secure MCP evidence

PRESENT: docs/03-reference/dcp/chatgpt-mcp-readonly/**
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/docs/03-reference/dcp/chatgpt-mcp-readonly/
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/docs/03-reference/dcp/chatgpt-mcp-readonly/DCP_THREAD_HANDOFF.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/docs/03-reference/dcp/chatgpt-mcp-readonly/ARCHITECTURE.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/docs/03-reference/dcp/chatgpt-mcp-readonly/SECURITY_MODEL.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md

PRESENT: proof/TP-DCP-MCP-RO-0001/**
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/proof/TP-DCP-MCP-RO-0001/
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/proof/TP-DCP-MCP-RO-0001/COMMAND_LOG.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/proof/TP-DCP-MCP-RO-0001/AUDIT.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/proof/TP-DCP-MCP-RO-0001/COMMAND_LOG_SUMMARY.md
  - /Users/hue/code/dopemux-mvp/.worktrees/gpt55-recon-chain/proof/TP-DCP-MCP-RO-0001/AUDITOR_REPORT.md

## Required ECC evidence

PRESENT: audit_inputs/ecc_dopemux_audit/ECC_DOPMUX_AUDIT_EVIDENCE.tgz
  - audit_inputs/ecc_dopemux_audit/ECC_DOPMUX_AUDIT_EVIDENCE.tgz

PRESENT: audit_inputs/ecc_dopemux_audit/ECC_AUDIT_EVIDENCE_INDEX.md
  - audit_inputs/ecc_dopemux_audit/ECC_AUDIT_EVIDENCE_INDEX.md

PRESENT: audit_inputs/ecc_dopemux_audit/ECC_HEAD.txt
  - audit_inputs/ecc_dopemux_audit/ECC_HEAD.txt

PRESENT: audit_inputs/ecc_dopemux_audit/COMMAND_LOG.md
  - audit_inputs/ecc_dopemux_audit/COMMAND_LOG.md

## Required governance docs

MISSING_NON_BLOCKING: RULES.md

PRESENT: PROJECT.md
  - PROJECT.md

PRESENT: ARCHITECTURE.md
  - ARCHITECTURE.md

MISSING_NON_BLOCKING: SYSTEM_BOUNDARIES.md

MISSING_NON_BLOCKING: 04_system-boundaries.md

PRESENT: PM_PLANE.md
  - PM_PLANE.md

PRESENT: SERVICE_CATALOG.md
  - SERVICE_CATALOG.md

MISSING_NON_BLOCKING: TRUTH_*.md

MISSING_NON_BLOCKING: SYSTEM_*.md

PRESENT: AGENTS.md
  - AGENTS.md

MISSING_NON_BLOCKING: PAL_*.md

MISSING_NON_BLOCKING: proof/handoff/**

MISSING_NON_BLOCKING: dopetask-cannonical-spec.json

MISSING_NON_BLOCKING: dopetask-canonical-spec.json

PRESENT: docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
  - docs/03-reference/spec/dopetask/dopetask-canonical-spec.json

## Required model / runner ledgers

MISSING_NON_BLOCKING: MODEL_PROVIDER_CAPABILITY_LEDGER.md

MISSING_NON_BLOCKING: RUNNER_CLI_INTEGRATION_LEDGER.md

MISSING_NON_BLOCKING: OPENROUTER_CODING_MODEL_EXPANSION.md

## Existing DCP synthesis

PRESENT: docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md
  - docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md

PRESENT: docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_GPT55.md
  - docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_GPT55.md

PRESENT: docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md
  - docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md

PRESENT: docs/03-reference/dcp/artifacts/DCP_ADVERSARIAL_ARCHITECTURE_AUDIT.md
  - docs/03-reference/dcp/artifacts/DCP_ADVERSARIAL_ARCHITECTURE_AUDIT.md

PRESENT: docs/03-reference/dcp/artifacts/DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md
  - docs/03-reference/dcp/artifacts/DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md

PRESENT: docs/03-reference/dcp/artifacts/DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md
  - docs/03-reference/dcp/artifacts/DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md

MISSING_NON_BLOCKING: DCP_BUILD_RECON.md

MISSING_NON_BLOCKING: DCP_BUILD_RECON.json

## Attach Order

## Required Risk Callout For GPT-5.5 Pro
