---
id: developer-onboarding
title: Developer Onboarding
type: how-to
owner: '@hu3mann'
author: codex
date: '2026-05-18'
last_review: '2026-05-18'
next_review: '2026-08-16'
prelude: Repo-grounded onboarding path for Dopemux contributors working under Task Packet discipline.
---
# Developer Onboarding

This guide is for contributors making repo changes in Dopemux. It is
documentation-only for packet `TP-DMX-DOCS-FORGE-002-README-QUICKSTART`; runtime
code, service code, compose, dependencies, and tests are outside this packet's
edit scope.

## 1. Preflight The Checkout

```bash
git rev-parse --show-toplevel
git remote -v
git status -sb
git branch --show-current
test -f pyproject.toml
test -f AGENTS.md
```

Read the active repo instructions first:

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,220p' docs/03-reference/governance/rules.md
```

Use a dedicated `worktree` or dedicated branch for non-trivial work. Preserve
unrelated dirty files; do not reset or overwrite user work.

## 2. Install Dependencies

```bash
uv sync --frozen --extra dev
```

For service-oriented checks, Docker must be available:

```bash
docker compose version
docker network inspect dopemux-network >/dev/null 2>&1 \
  || docker network create dopemux-network
```

## 3. Know The Authority Order

Use this order when docs, code, and generated artifacts disagree:

1. Active Task Packet for the current work slice.
2. Runtime code, config, compose wiring, tests, and active entrypoints.
3. Current truth/reference docs.
4. Historical, generated, archived, uploaded, exploratory, or design docs.
5. Assumptions, marked explicitly as `UNKNOWN` or `NEEDS_REPO_VERIFICATION`.

Task Packet scope controls allowed files and validations. It does not make an
unsupported runtime claim true.

## 4. Preserve Split Authority

Do not collapse Dopemux into one system:

- `dopemux` owns operator control and startup coordination.
- `dopetask` owns execution after handoff through `scripts/dopetask`.
- Leantime owns passive PM metadata and project/ticket snapshots.
- task-orchestrator owns workflow-significant transitions and blockers.
- ConPort owns structured decisions, progress, project context, and custom data.
- dope-memory owns historical chronicle receipts.
- dope-context owns derived code/docs retrieval.
- dopecon-bridge owns proxying, routing, compatibility, and event transport.
- ADHD Engine owns operator-support and cognitive-state surfaces.
- Repo Truth Extractor owns extraction/audit artifacts, not runtime truth.
- Agent authority is `UNKNOWN` unless a packet verifies a specific runtime path.

## 5. Documentation Validation

For documentation-heavy work, start with changed files, then run the broader
commands required by the active packet:

```bash
python scripts/docs_validator.py README.md QUICK_START.md docs/01-tutorials/quickstart.md docs/02-how-to/developer-onboarding.md
python scripts/docs_frontmatter_guard.py docs/01-tutorials/quickstart.md docs/02-how-to/developer-onboarding.md docs/INDEX.md docs/00-MASTER-INDEX.md
python scripts/check_root_hygiene.py
git diff --check
```

Packet 002 also requires:

```bash
bash scripts/lint-docs.sh
python scripts/docs_validator.py
python scripts/docs_frontmatter_guard.py
```

If full-repo validators fail on files outside the packet allowlist, record the
exit code, file paths, and residual risk instead of silently expanding scope.

## 6. Runtime Validation

Do not claim live runtime behavior unless you actually run it:

```bash
docker compose -f compose.yml up -d --build
docker compose -f compose.yml ps
curl -fsS http://localhost:3016/health
curl -fsS http://localhost:3004/health
curl -fsS http://localhost:8000/health
```

When runtime checks are not run, mark them `NOT_RUN`. When behavior is plausible
from code but not exercised, mark it `NEEDS_REPO_VERIFICATION`.

## 7. Common Traps

- Treating dopecon-bridge as PM, workflow, decision, or memory authority.
- Treating dope-context retrieval output as source truth.
- Treating dope-memory as all memory or current PM state.
- Treating Repo Truth Extractor artifacts as stronger than runtime code.
- Treating `scripts/taskx` as a separate execution engine instead of a shim.
- Closing runtime drift from docs-only evidence.
- Editing outside the Task Packet allowlist.

## 8. Before Commit

```bash
git status -sb
git diff --stat
git diff --check
pre-commit run --files <changed-files>
```

Proof for packet work should include files changed, validations with exit
codes, known failures, `UNKNOWN`s, residual risks, commit SHA, PR URL, and
rollback plan.
