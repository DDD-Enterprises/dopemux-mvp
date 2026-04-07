---
id: docs-contributing
title: Documentation Contributing Guide
type: reference
owner: '@hu3mann'
date: 2026-03-26
status: active
prelude: Rules for creating, naming, and placing documentation to prevent sprawl and
  duplication.
author: '@hu3mann'
last_review: '2026-03-26'
next_review: '2026-06-24'
---
# Documentation Contributing Guide

## Directory Structure

All docs live under numbered Diataxis sections. **Nothing goes in `docs/` root** except index files.

```
docs/
  00-MASTER-INDEX.md          # Master navigation
  INDEX.md                    # Quick index
  docs_index.yaml             # Machine-readable index
  01-tutorials/               # Learning-oriented walkthroughs
  02-how-to/                  # Problem-solving procedures
  03-reference/               # API docs, specs, command reference
  04-explanation/              # Architecture, deep-dives, concepts
  05-audit-reports/            # Verification matrices, checklists
  06-research/                 # Investigations, explorations
  90-adr/                      # Architecture Decision Records
  91-rfc/                      # Requests for Comments
  92-runbooks/                 # Operational procedures
  archive/                     # Deprecated/historical content
```

## Naming Rules

| Rule | Example | Why |
|------|---------|-----|
| Lowercase kebab-case only | `deployment-guide.md` | Consistency, no case-sensitivity issues |
| No `-2`, `-3` suffixes | Use git for versions | Prevents the duplication mess we cleaned up |
| No spaces in filenames | `multi-llm-routing.md` | Shell compatibility |
| No `(1)` copies | Don't duplicate via OS | OS copy artifacts create junk |
| No `.bak` files | Git is the backup system | Prevents clutter |
| No UPPERCASE filenames | Exception: `INDEX.md`, `CONTRIBUTING.md` | Consistency |

## Placement Rules

| Doc Type | Where | Examples |
|----------|-------|---------|
| Getting started, onboarding | `01-tutorials/` | Installation, first project, profiles |
| How to do X (procedures) | `02-how-to/` | Deployment, Docker setup, troubleshooting |
| API, CLI, specs, config | `03-reference/` | Port registry, command reference, schemas |
| Why/how things work | `04-explanation/` | Architecture, design decisions, deep-dives |
| Audit results, checklists | `05-audit-reports/` | Verification matrices, test reports |
| Research, investigations | `06-research/` | Explorations, analysis reports |
| Architecture decisions | `90-adr/` | ADR-NNN format |
| Proposals | `91-rfc/` | RFC format |
| Ops procedures | `92-runbooks/` | Runbook format |
| Old/deprecated | `archive/` | Anything superseded |

**Do NOT** create new top-level directories. If a doc doesn't fit, it goes in the closest Diataxis section.

## Frontmatter Requirements

Every `.md` file must have YAML frontmatter:

```yaml
---
id: unique-kebab-case-id
title: Human Readable Title
type: tutorial | how-to | reference | explanation | adr | rfc | runbook
owner: "@hu3mann"
date: 2026-03-26
status: active | draft | proposed | deprecated
prelude: One sentence description (max 100 tokens for embedding efficiency).
---
```

## Size Limits

| Limit | Value | Action |
|-------|-------|--------|
| Max files per directory | 200 | Split into subdirectories |
| Max lines per doc | 500 | Split into parts with a hub page |
| Max directory nesting | 3 levels under any Diataxis section | Flatten |

## Archiving

When a doc is superseded:
1. Move it to `archive/` with a descriptive subdirectory
2. Do NOT rename it with a suffix (`-old`, `-v1`, `-deprecated`)
3. Do NOT keep both old and new versions in the active tree
4. Git history preserves all previous versions

## Validation

Run the lint script after doc changes:

```bash
scripts/lint-docs.sh
```

This checks naming, placement, frontmatter, and size limits.
