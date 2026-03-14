# Drift Report

> Documents discrepancies between documentation claims and code implementation.
> Only items verified against source code are listed.

## Severity Levels
- 🟢 **None**: Docs match code exactly
- 🟡 **Minor**: Cosmetic or non-functional difference
- 🔴 **Material**: Behavioral difference that could affect integration

---

## Tool Count and Names
| Check           | Status | Details                                                                |
| --------------- | ------ | ---------------------------------------------------------------------- |
| Tool count      | 🟢 None | README claims 13, code registers 13                                    |
| Tool names      | 🟢 None | All 13 names match between README table and code `ToolDefinition.name` |
| Tool categories | 🟢 None | README groupings match `ToolCategory` enum assignments                 |

## Workflow
| Check       | Status  | Details                                                                                                                                                                                                                                                                                                               |
| ----------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Role names  | 🟢 None  | README: `queue → work → review → terminal`. Code: `Role.QUEUE, WORK, REVIEW, TERMINAL`                                                                                                                                                                                                                                |
| Triggers    | 🟡 Minor | README trigger table lists `start, complete, block, resume, cancel` — omits `hold`. Code treats `hold` as alias for `block` (`RoleTransitionHandler.kt:85,111`). `hold` is mentioned in README body text and in `RoleTransition.VALID_TRIGGERS`. **Impact**: None — `hold` works, just not in README's trigger table. |
| Skip review | 🟢 None  | README describes review skip when no review notes defined. Code: `hasReviewPhase=false` → WORK→TERMINAL                                                                                                                                                                                                               |

## Data Model
| Check                  | Status  | Details                                                                                                                                                                                                                                                                                     |
| ---------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `complexity` default   | 🟡 Minor | README (`description` field of `manage_items`) says "Defaults: complexity=5". V1 migration: `NOT NULL DEFAULT 5`. V2 migration: made nullable. Code model: `complexity: Int? = null`. **V2 is authoritative** — nullable, no default of 5 in current schema. README is stale on this point. |
| `requiresVerification` | 🟢 None  | V2 added correctly, code model has `requiresVerification: Boolean = false` matching `DEFAULT 0`                                                                                                                                                                                             |

## Docker
| Check           | Status  | Details                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DATABASE_PATH` | 🟡 Minor | Dockerfile `runtime-base` stage sets `ENV DATABASE_PATH=/app/data/tasks.db`. Dockerfile `runtime-current` stage overrides to `data/current-tasks.db` (no leading `/`). Code default: `data/current-tasks.db`. The `runtime-current` override aligns with code, but the relative path (no `/app/`) means it resolves relative to WORKDIR (`/app`). **Effective path is the same**: `/app/data/current-tasks.db`. |

## Test Count
| Check                | Status  | Details                                                                                                                                                                                                                                                                            |
| -------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "1,600+ tests" claim | 🟡 Minor | README claims "1,600+ tests". Pass 1 found 35 test files in `:current` module. The claim likely includes `:clockwork` tests (v2, not counted). **Cannot verify** without running `./gradlew test` — test count inside files is unknown. Labeled `DOCS_CLAIM_UNVERIFIED_FROM_CODE`. |

## Architecture
| Check              | Status | Details                                                                                                                                                     |
| ------------------ | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Clean Architecture | 🟢 None | README claims "Clean Architecture (Domain → Application → Infrastructure → Interface)". Confirmed by import analysis: domain has zero outward dependencies. |
| Kotlin version     | 🟢 None | README: "Kotlin 2.2.0". Build plugin confirms.                                                                                                              |
| MCP SDK version    | 🟢 None | README: "MCP SDK 0.8.4". `build.gradle.kts` confirms.                                                                                                       |

## Summary

| Severity   | Count |
| ---------- | ----- |
| 🟢 None     | 10    |
| 🟡 Minor    | 4     |
| 🔴 Material | 0     |

**No material drift found.** Documentation is substantially accurate relative to code.
