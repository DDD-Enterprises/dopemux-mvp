# Independent formal audit — CCAR-002R-A2, PR #1176

**Auditor**: Claude Opus 5 (claude-code-cli), read-only, plan mode
**Date**: 2026-08-03
**Head audited**: `c8181389864bfc099bc24f7d689716057c3c8573`
**Base**: `899082ae74155b2412a2ce862376438c1d33d13e`
**Nature**: proof-only, non-merging. No file was modified by this audit.

## Context

PR #1176 adds a normalized agent/persona catalog builder plus generated artifact,
tests, and proof bookkeeping. An R2 signed embedded audit (Claude Sonnet,
PASS_WITH_RISKS) is bound to the older head `41bc6207` and is now stale. Repair
packet CCAR-002R-A2 landed four fix commits on top. This audit verifies those
fixes at the exact current head and decides whether the subsequent R4 step
(sign + commit the canonical embedded-audit proof) may proceed.

## Ground truth re-derived

| Check | Result |
|---|---|
| `git log -1 --format=%H` | `c8181389864bfc099bc24f7d689716057c3c8573` ✅ matches |
| `git diff --stat base..HEAD` | 29 files, 4686 insertions, **0 deletions** ✅ |
| `git diff --name-status base..HEAD` | all 29 entries status `A` (pure addition) |
| Working tree at start | clean except 2 untracked `.claude/.*-cache.json` (hook caches, not PR content) |

## Scope verification (items 1–10)

### 1. A2 fixes present — VERIFIED
- `proof/CCAR-002/SOURCE_MANIFEST.json`: no `worktree` key (absolute path removed).
- `proof/CCAR-002/NORMALIZATION_REPORT.md`: `**Generated**: 2026-08-03T07:37:00Z` — real value, no `$(date …)` literal.
- `test_generation_idempotent`: `--check` now runs against the committed catalog *before* any regeneration.
- `_scan_model_ids`: `(?:…)` non-capturing + `finditer(...).group(0)`.

### 2. Timestamp/catalog sync — VERIFIED
- Report `**Generated**` = `2026-08-03T07:37:00Z`
- Catalog `meta.generated_at` = `2026-08-03T07:37:00Z`
- `meta.source_commit` = `683b2411…` = manifest `base_commit`, a real ancestor of HEAD.
- `build_normalized_catalog.py --check --repo-root .` → exit 0, `CHECK_PASS`.
- ⚠️ `--check` calls `normalize_generated_at()` on both sides, so it **structurally cannot**
  detect `generated_at` drift. Sync was confirmed by direct byte comparison, not by `--check`.

### 3. Tests leave worktree clean — VERIFIED
- `pytest tests/commandcode_router/test_normalized_catalog.py` → **26 passed**, 0 failed, 0 skipped.
- catalog sha256 `ad69d42e8c68…` identical before and after.
- `git status --short` and `git diff --stat` clean afterward.

### 4. Scanner + regression coverage — VERIFIED
Direct exercise of `_scan_model_ids`: `claude-sonnet-4.5`→`['claude-sonnet-4.5']`,
`Claude Opus 4.1`, `claude haiku 3`, `gpt-5.4-mini`, `gemini-3-pro`, `grok-4`,
`CLAUDE-SONNET-5` all return the full token; `no model here`→`[]`. No truncation.
`TestScanModelIds` (2 tests) genuinely collected and passing.

### 5. Stale "Claude" references — VERIFIED CLEAN
Every surviving mention is either a `.claude/` path or a correct historical statement
(the Sonnet R1 audit that did happen, REVIEW-001 rationale, `author: Claude Sonnet`).
The frontmatter prelude now names the OpenRouter route, not "Claude audit return".

### 6. PROOF.json historical wording — VERIFIED (with nit)
`remaining_risks` is anchored to named SHAs (`b096551dfa`, `fd7afbe295`) and explicitly
explains why an "exact current head" claim cannot survive its own edit. Residual
self-referential phrases: "(fixed in this commit)", "reworded here".

### 7. Scope creep — NONE
`41bc6207..HEAD` = 5 commits, 23 files, all within: builder, its tests, the catalog,
`proof/CCAR-002/**`, `proof/pr_merge/embedded-audit/pr-1176/**`, `task-packets/CCAR-002R-A2.*`.

### 8. Source surfaces untouched — VERIFIED
No path under `.claude/agents/**`, `.claude/personas/**`, `.github/agents/**`,
`src/dopemux/personas/**` appears anywhere in the base→HEAD diff.

### 9. No runtime activation — VERIFIED
Repo-wide grep for `normalized_agent_persona_catalog` / `build_normalized_catalog`
finds zero importers or consumers outside the audited directories. No hooks,
`.mcp.json`, workflows, `src/`, or routing files in the diff. Catalog is inert data.

### 10. Independent invariant re-derivation
9 base agents, 43 personas; `may_change_tools` / `may_select_model` /
`may_grant_write_authority` / `route_eligible` all `False` for all 43; zero
model-ID tokens in the catalog text.

## Findings

| # | Sev | Title |
|---|---|---|
| 1 | MEDIUM | `test_generation_idempotent` still writes the committed catalog; `finally`-restore is best-effort |
| 2 | LOW | `--check` normalizes `generated_at`, so it cannot detect the exact drift class A2 was repairing |
| 3 | LOW | `PROOF.json` attributes the round-2 FAIL to kimi-k3, contradicting `COMMAND_LOG.md` |
| 4 | LOW | `NORMALIZATION_REPORT.md` "Generator … v1.0.0" stale vs `meta.generator_version: 1.0.1` |
| 5 | INFO | `reference_only_src_personas: 11` counts `__init__.py`; report says 10 |
| 6 | INFO | pr-1176 canonical PROOF/sig bound to `41bc6207`; must be regenerated + re-signed at R4 |
| 7 | INFO | `AUDIT_INSTRUCTION.md` is committed instruction-like content with an all-`true` JSON template |
| 8 | INFO | No CI/pre-commit rule references the catalog; drift gating rides on the pytest suite |

No BLOCKING findings.

## Verdict

**PASS_WITH_RISKS** — R4 authorized. Merge is not authorized by this audit.
