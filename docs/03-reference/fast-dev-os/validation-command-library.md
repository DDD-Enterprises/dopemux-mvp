---
id: fast-dev-os-validation-command-library
title: Fast Dev OS — Validation Command Library
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Reusable validation command snippets for Fast Dev OS packets — JSON schema, docs hygiene, git diff, frontmatter, anti-pattern grep, runtime-specific checks. Copy snippets into `commit.verify` arrays and PROOF `validations[]` blocks.
---
# Fast Dev OS — Validation Command Library

## Relationship to governance

This library **operationalizes** [`codex-authority-refresh.md`](../governance/codex-authority-refresh.md) and AGENTS.md §9 proof field requirements; it **does not override** them.

## Lane

**L2** — validation snippets are referenced across all subsequent Fast Dev OS packets. Updates here propagate.

## How to use

1. Pick the snippets relevant to your packet's lane and scope.
2. Copy into your TP's `commit.verify` array (compact command form).
3. Copy into your PROOF's `validations[]` blocks (with `exit_code` and `status` recorded).
4. Run each command; record actual exit codes.
5. For PASS, record `"status": "PASS"`. For FAIL, record `"status": "FAIL"` with stderr. For commands you didn't run, record `"status": "NOT_RUN"` with reason — **never collapse NOT_RUN into PASS**.

## Snippets

### 1. JSON parses (smoke test)

```bash
python -m json.tool <path/to/file.json> >/dev/null
```

For PROOF.json + TP JSON; should always be the first check.

### 2. JSON Schema validation

```bash
python -m jsonschema -i <path/to/TP.json> docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
```

For Task Packets. Output empty = PASS. The CLI is deprecated but still functional; long-term consider `check-jsonschema`.

### 3. Docs frontmatter + content validator

```bash
python scripts/docs_validator.py <path/to/file1.md> [<path/to/file2.md> ...]
```

Silent output = PASS. Validates frontmatter required fields, content structure conventions.

### 4. Frontmatter guard (strict)

```bash
python scripts/docs_frontmatter_guard.py <path/to/file1.md> [...]
```

Output `"All docs have valid frontmatter."` = PASS.

### 5. Docs filename hygiene (kebab-case)

```bash
python3 scripts/check_docs_filename_hygiene.py --check <path/to/file1.md> [...]
```

Output `"docs-filename-hygiene: checked N files, OK"` = PASS. To auto-fix violations, use `--apply` (side effects: file renames, link rewrites, audit JSON updates).

### 6. Root hygiene (no random root files)

```bash
python scripts/check_root_hygiene.py
```

Enforces docs/00-MASTER-INDEX.md and docs/INDEX.md exemptions; rejects new root-level files outside allowlist.

### 7. Doc-lint (full)

```bash
bash scripts/lint-docs.sh
```

Runs full doc lint suite. Use for packets touching many docs.

### 8. Git diff guards

```bash
git diff --check
git diff --cached --check
```

Detects whitespace errors, merge markers, conflict residue. Both should exit 0.

### 9. Allowlist compliance check

```bash
# Compare actual staged paths against TP commit.allowlist
python3 - <<'PY'
import json
from pathlib import Path
import subprocess

tp = json.load(open('task-packets/generated/TP-DMX-...-...json'))
allow = set(tp['commit']['allowlist'])
staged = set(subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True).strip().split('\n'))
extra = staged - allow
missing = allow - staged
print(f'allow={len(allow)} staged={len(staged)} extra={len(extra)} missing={len(missing)}')
if extra:
    print('EXTRA (out of scope):')
    for p in sorted(extra): print(' ', p)
if missing:
    print('MISSING (allowed but not staged):')
    for p in sorted(missing): print(' ', p)
PY
```

### 10. Anti-secret pattern (NEGATIVE match — failure = found secret)

```bash
! grep -nE '(api[_-]?key|secret|token|password|bearer)\s*[:=]' <paths>
```

Exit code 0 = no secrets found. Exit code 1 = secrets found (BLOCKING).

### 11. Anti-user-path pattern (NEGATIVE match — failure = found user path)

```bash
! grep -nE '/Users/[a-z]+/' <paths>
```

Exit code 0 = no user-specific paths. Exit code 1 = user paths found.

### 12. AGENTS.md citation present (POSITIVE match)

```bash
for f in <paths>; do grep -q 'AGENTS\.md' "$f" || echo "MISSING: $f"; done
```

Empty output = all files cite AGENTS.md.

### 13. Lane line present (POSITIVE match)

```bash
grep -l 'Lane' <paths>
```

Should match every path passed.

### 14. Truth-posture statement present (POSITIVE match)

```bash
grep -l 'Never invent paths' <paths>
```

For implementer prompts. Should match every implementer prompt.

### 15. Snapshot metadata present (POSITIVE match)

```bash
grep -l '^snapshot:\| snapshot:' <ledger paths>
```

For snapshot ledgers. Should match every snapshot ledger.

### 16. "Relationship to governance" section present

```bash
grep -l 'Relationship to governance' <paths>
```

For Fast Dev OS docs. Should match every doc.

### 17. Pre-commit hook chain (if .pre-commit-config.yaml present)

```bash
pre-commit run --from-ref origin/main --to-ref HEAD
```

Runs all configured pre-commit hooks. CI runs an equivalent.

### 18. JSON Schema validate template-as-schema (recursive)

For `task-packet-template.json`:

```bash
python -m jsonschema -i docs/03-reference/fast-dev-os/task-packet-template.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
```

The template must itself be schema-valid (strongest check for TP-FDOS-006).

### 19. PROOF.json AGENTS.md §9 field presence check

```bash
python3 - <<'PY'
import json
required = ['tp_path','tp_id','worktree_path','branch','repo_identity_check','slices_completed','files_created','validations','codereview_status','precommit_status','commit_sha','pr_url','residual_risks','unknowns','cleanup_status']
p = json.load(open('proof/<series>/<TP>/PROOF.json'))
missing = [k for k in required if k not in p]
if missing:
    print('MISSING:', missing); raise SystemExit(1)
print('All AGENTS.md §9 fields present')
PY
```

## Conventions

- **Always run JSON parse before JSON schema**: a schema check on broken JSON gives misleading errors.
- **Order from cheapest to most expensive**: parse → schema → grep → docs validators → docs-filename-hygiene → root hygiene → full pre-commit.
- **Record exit codes in PROOF.json**: not just PASS/FAIL — the actual integer matters for audit.
- **Never gloss `NOT_RUN`**: every unrun validation must have a written reason in PROOF.json.

## Cross-references

- AGENTS.md §9 required PROOF fields: [../../../AGENTS.md](../../../AGENTS.md).
- TP template: [`template-task-packet.md`](template-task-packet.md).
- PROOF template: [`templates-proof/proof-bundle-template.json`](templates-proof/proof-bundle-template.json).
- PR body template: [`template-pr-body.md`](template-pr-body.md).
- Governance: [`../governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md).

## Truth posture

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say a validation passed without recording the exit code. Distinguish observed vs inferred vs proposed vs unknown.
