# DMX-DCP-MODEL-ROUTING-MVP-0000F — RUNNER_DRY_RUN_MATRIX.md

## Runner Dry-Run Matrix (Captured 2026-06-09)

| Runner | Installed | Invokable | Dry-run support | Write control | JSON output | Model capture | Diff capture | Safe for DCP v1? | Notes |
|--------|-----------|-----------|-----------------|---------------|-------------|---------------|--------------|------------------|-------|
| **opencode** | YES (1.16.2) | YES | Partial (TUI + run) | Unknown | Unknown | Yes (this session) | No | **Backend-only** | Must remain backend-only until write controls proven |
| **claude** | YES (2.1.153) | YES | Plan mode | Yes (delegated) | Partial | Yes | Yes | Adapter | Strong for plan/audit |
| **codex** | YES (0.130.0) | YES | Unknown | Unknown | Unknown | Unknown | Unknown | Adapter | Strong candidate if dry-run proven |
| **gemini** | YES (0.45.2) | YES | Unknown | Unknown | Unknown | Unknown | Unknown | Adapter | Telemetry-heavy audit only |
| **aider** | YES (0.86.1) | YES | `/ask` mode | Yes (with approval) | No | Partial | Yes | Adapter | Cheap repo scan only |
| **gh** | YES | YES | Read-only | No | Partial | N/A | N/A | Validation-only | Read-only CI surface |
| **Copilot** | YES (VS Code) | YES | Unknown | Delegated | Unknown | Unknown | Unknown | Adapter | Cloud-hosted |
| **Jules** | YES | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | **Unsafe until proven** | No runtime proof |
| **AGY / Antigravity** | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | **Unsafe until proven** | No runtime proof |

## Summary for 0001

**Backend-only**: opencode (until write controls proven)
**Safe adapters**: claude, codex, gemini, aider, gh
**Unsafe until proven**: Jules, AGY/Antigravity
**Validation-only**: shell/test runner, gh (read-only)

**Recommendation**: 0001 must not treat any runner as implementation-safe without explicit dry-run + write-control proof.
