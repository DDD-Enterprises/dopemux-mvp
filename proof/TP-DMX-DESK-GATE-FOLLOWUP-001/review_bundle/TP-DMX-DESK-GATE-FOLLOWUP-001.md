# TP-DMX-DESK-GATE-FOLLOWUP-001 — PR #1517 private follow-up

**Issued**: 2026-11-22 by the supervisor session (Claude Code desktop, configured model `claude-opus-5-5`; observed model UNKNOWN).
**Authority**: owner approval "item 1, 17 Nov 2026" (chat), scope read back from Codex memory summaries of the Possie conversation ("#1517 merged at `3e31e7af` without the proposed helper identity verification and read-only GO changes"; earlier helper test "covered neither GO with a task ID nor runtime helper verification"). The original Possie text is not available locally. Owner confirmed this scope and route in chat on 2026-11-22: "1 same route" and "Yes, proceed".
**Lane**: L2 (hook dispatch is an authority-boundary surface). One final independent audit.

## Forbidden

Push, merge, PR creation, deployment, any change to live hooks or configuration (`.claude/settings.json`, `.codex/hooks.json`, `run_native_hooks.sh`), any paid route, any upload of private data, exploitation or vulnerability reproduction. `GITHUB_MUTATION=FORBIDDEN`, `MERGE_AUTHORIZED=NO`.

## Baselines

| Repo | Worktree | Branch | Base |
|---|---|---|---|
| dopemux-mvp | `.worktrees/desk-gate-followup-001` | `fix/desk-gate-helper-identity-001` | `0aa2cf3497c59f8c607f92986d01e7b7f2620919` (`origin/main`, contains `3e31e7af`) |
| dispatch-desk | `~/code/dispatch-desk-wt/gate-readonly-go` | `fix/gate-readonly-go` | `456244f0f66ddfb06412ac05a1b4d8b501a16b14` |

## Workstreams (serial)

### S1 — dispatch-desk: GO is read-only

Allowlist: `tools/gate.py`, `tools/test_gate.py`, `README.md` (gate line only).

- A check that returns GO appends nothing to the ledger, with or without `--task`, and does not create a missing ledger file.
- Refusals are unchanged: a pause still appends one `pause_acknowledged` per asker per pause request; a refusal that passes a task id still appends `gate_checked` with `allowed: false`.
- Exit codes and output unchanged.

### S2 — dopemux-mvp: verify the helper before running it

Allowlist: `src/dopemux/claude/dispatch_gate.py`, `tests/unit/test_dispatch_gate.py`.

- Pin SHA-256 of `tools/gate.py` and `tools/ledger.py` as produced by S1's commit.
- Read both files (size-capped), hash the bytes read, and on any mismatch, missing `ledger.py`, oversize or read error return `UNKNOWN` with a fixed message and run nothing.
- Run only the verified bytes: write them into a fresh private temporary directory and execute that copy with `python -I`, so a file swapped after the check is never run. Remove the directory afterwards.
- Gate absent still returns `NOT_INSTALLED` without a subprocess. Fail open, never raise, advisory only, `--require-approval` never passed, no change to `native_hooks.py` or the session-start wording.

## Validation

- dispatch-desk: `python3 -m unittest discover -s tools -p 'test_*.py'`
- dopemux-mvp: `pytest -q tests/unit/test_dispatch_gate.py tests/test_native_hooks_workflow.py`, flake8 on the two changed files, `git diff --name-only` equals the allowlist.
- Synthetic only: temporary ledgers and fake gates. The real `~/.dispatch-desk` is never touched.

## TP_ROUTE

```
TP_ROUTE
workstream=coordinator
runner=claude-code
model=claude-opus-5-5
effort=UNKNOWN
skills=task-packet
why=issuing supervisor session; session model set by the owner; observed model UNKNOWN
```

```
TP_ROUTE
workstream=S1
runner=claude-code
model=claude-sonnet-5-5
effort=medium
skills=NONE
why=owner ruling 2026-11-22: same route as the original #1517 writer counts as the original writer
```

```
TP_ROUTE
workstream=S2
runner=claude-code
model=claude-sonnet-5-5
effort=medium
skills=NONE
why=owner ruling 2026-11-22: same route as the original #1517 writer counts as the original writer
```

```
TP_ROUTE
workstream=final-audit
runner=grok-cli
model=grok-4.7
effort=UNKNOWN
skills=independent-audit
why=different model family from the writer; owner chose Grok on the signed-in plan (2026-11-22); held until both heads freeze
```

`allowed_fallbacks`: none. A failed validation returns to the supervisor.

## Stop conditions

A file outside an allowlist must change; the baseline moved in a way that touches these files; a test would need the real ledger or network; the Grok route asks for payment or an API key.
