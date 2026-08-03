# CCAR-002 Normalization Report

**Packet**: CCAR-002
**Generated**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
**Source commit**: 683b2411ebd9df7ed93ce9aa1871ca08956eb588

## Normalization Summary

- **Base agents**: 9 (all resolving through `src/dopemux/roles/catalog.py`)
- **Personas**: 43 active (covering all `.claude/personas/*.md` non-archive + `.claude/agents/project-manager.md`)
- **Archived personas**: 6 (excluded from automatic authority: `archive/` directory)
- **Reference-only agents**: 6 (`.github/agents/`)
- **Reference-only src personas**: 10 fallback copies (`src/dopemux/personas/`)

## Base Agent Mapping

Each base agent resolves through `src/dopemux/roles/catalog.py`:

| ID | Canonical Role | Mode | May Edit | Stage Lane |
|---|---|---|---|---|
| architect | architect | PLAN | false | strong |
| developer | developer | ACT | true | standard |
| researcher | research | Both | false | cheap_read |
| reviewer | reviewer | PLAN | false | standard |
| quickfix | quickfix | ACT | true | standard |
| debugger | debugger | ACT | true | standard |
| ops | ops | ACT | true | standard |
| plan | plan | PLAN | false | strong |
| act | act | ACT | true | standard |

## Persona Distribution

| Domain | Count |
|---|---|
| architecture | 4 |
| devops | 4 |
| security | 3 |
| performance | 1 |
| quality | 1 |
| engineering | 8 |
| documentation | 6 |
| workflow | 4 |
| advisory | 7 |
| product | 2 |
| general | 2 |

## Covered Personas (43)

All 43 active persona files (excluding `PERSONA_INDEX.md` and `archive/`) are represented in the catalog. No uncovered source files.

## Model-Free Verification

- No model IDs in catalog fields
- Source file `.claude/personas/se-product-manager-advisor.agent.md` contains model references in its source text (`GPT-5`); the catalog record is model-free per invariant

## Authority Prohibitions

All 43 personas have:
- `may_change_tools`: false
- `may_select_model`: false
- `may_grant_write_authority`: false

No persona is `route_eligible`.
No `general-purpose-dopemux` automatic write fallback.

## Generator

- `scripts/commandcode_router/build_normalized_catalog.py` v1.0.0
- Deterministic: `--check` passes after regeneration
- Schema validation: PASS (strict `additionalProperties=false`)
- Source hash verification: PASS (5 categories, all SHA-256 match)

## CCAR-002R R1 portability notes

- Generator version: 1.0.1
- `meta.source_manifest` fixed to repo-relative `proof/CCAR-002/SOURCE_MANIFEST.json`
- Absolute worktree path leakage removed
- Validated repository-root resolution (explicit `--repo-root`, `git rev-parse --show-toplevel`, marker walk)
- Dual-worktree generation produces byte-identical YAML when `generated_at` is fixed
