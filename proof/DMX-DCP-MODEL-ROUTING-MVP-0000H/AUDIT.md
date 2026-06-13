# DMX-DCP-MODEL-ROUTING-MVP-0000H — AUDIT.md

**Auditor**: opencode (grok-4.3) — embedded self-audit (stronger auditor recommended)
**Date**: 2026-06-09
**Target**: 0001 Routing Domain Model design

## Attack Points Reviewed

1. **Dirty worktree and branch divergence**
   - Current branch is diverged from `origin/main` by 3 commits behind + new modifications
   - 0000C proved clean `origin/main` baseline exists
   - **Risk**: Designing from dirty branch instead of clean main

2. **Red-lane workflow conflict**
   - `.github/workflows/gemini-review.yml` remains modified in worktree
   - DCP test_16 continues to fail
   - **Risk**: 0001 may inherit red-lane violation

3. **PAL listmodels contradiction**
   - Still `BLOCKED_OR_UNAVAILABLE`
   - No progress since 0000B
   - **Risk**: Model slot design may be based on config, not callable models

4. **LiteLLM unhealthy status**
   - Confirmed unhealthy in 0000B
   - No health recovery evidence
   - **Risk**: Routing assumes healthy proxy that is currently unhealthy

5. **Stale alias contract**
   - `claude-opus-4-6` missing
   - Repair available but not applied
   - **Risk**: Alias drift between repo and runtime

6. **OpenCode backend confidence**
   - Version 1.16.2 captured
   - No routing config or write-control proof
   - **Risk**: Over-trusting unproven backend

7. **model-routing policy promotion risk**
   - File exists on clean main (0000C)
   - Still missing on current branch
   - **Risk**: Treating advisory policy as runtime authority

8. **MCP/slash/workflow safety classification**
   - Not yet expanded (0000G not run)
   - **Risk**: Router may trust unsafe surfaces

9. **Agent authority assumptions**
   - 63 agent/persona surfaces remain `UNKNOWN` runtime authority
   - **Risk**: Assuming agent authority that does not exist

10. **Proof-family flattening**
    - Multiple proof families exist with different shapes
    - **Risk**: 0001 may invent unified proof contract

11. **Self-certifying audit loops**
    - This audit is embedded (opencode/grok-4.3)
    - Stronger independent auditor (Opus/GPT-5.5) recommended
    - **Risk**: Circular validation

12. **Forbidden PR merge/batch seams**
    - Still present in red-lane ledger
    - **Risk**: 0001 may accidentally route through forbidden seams

## Preliminary Verdict

**VERDICT**: `PASS_WITH_RISKS`

**BLOCKERS**:
- U-01 (policy file missing on implementation branch)
- U-03 (LiteLLM unhealthy)
- U-09 (PAL model inventory unavailable)
- Red-lane conflict on `gemini-review.yml`

**MUST_FIX_BEFORE_0001**:
- Reconcile `config/ai/model-routing.policy.yaml` to implementation branch
- Resolve or document `gemini-review.yml` red-lane violation
- Obtain PAL model list or explicitly mark as unavailable

**MUST_CARRY_AS_STOP_CONDITIONS**:
- Dirty worktree
- Branch divergence from clean main
- LiteLLM unhealthy
- Stale alias contract
- No independent audit yet

**SAFEST_NEXT_PACKET**: 0000D (worktree reconciliation) + 0000H with stronger auditor (Claude Opus or GPT-5.5 Pro)
