# Independent L2 audit — PR #1412, dopemux-mvp

You are the **sole final independent auditor**. The implementer was Claude Code. One call; be adversarial and check claims against primary files.

## 0. Custody
`git rev-parse HEAD` must print exactly `a1b4ea9108f09e2b2c8fb9e753d31f2900a20ba6`; otherwise return `NEEDS_SUPERVISOR` / `CUSTODY_MISMATCH`. Base (merge-base with main): `20a4d4b12c68836f70ae1f5c9a6846122f00a136`. Use `git diff 20a4d4b12c68836f70ae1f5c9a6846122f00a136..a1b4ea9108f09e2b2c8fb9e753d31f2900a20ba6`. **Do not create or modify any file in the mounted worktree** (run anything under `/tmp`). If you cannot run tools, set `TOOL_ACCESS=NONE`.

## 1. What this PR is
One commit, two files: `src/dopemux/cli.py` (`native_hooks_register`, `--global` branch: `python3 <hook>` → `shlex.quote(sys.executable) <hook>`) and `tests/unit/test_cli_audit_remediations.py` (new `test_native_hooks_register_global_uses_running_interpreter`).

## 2. Challenge each point — UPHELD / DISPUTED / UNVERIFIABLE with evidence
1. **Correctness.** The `--global` command now uses `sys.executable` and the absolute, shell-quoted path to `src/dopemux/claude/native_hooks.py`; `sys` and `shlex` are imported in `cli.py`. Paths with spaces are quoted safely.
2. **Rationale holds.** A bare `python3` can resolve to an interpreter lacking dopemux deps (`native_hooks.py` imports modules needing `pydantic`; check its import chain). Is `sys.executable` guaranteed to have them when `dopemux` runs? Any case where `sys.executable` is wrong (e.g. pipx/uv tool shims, frozen builds)? Flag as risk if so.
3. **Why not the wrapper.** Verify `.claude/hooks/run_native_hooks.sh` resolves ROOT from `git rev-parse --show-toplevel` of the *current* directory, so it cannot serve hooks registered in `~/.claude/settings.json` for other repos; confirm the non-global branch still writes the wrapper command (unchanged from #1409).
4. **Test is non-vacuous.** The new test isolates HOME, invokes `native-hooks register --global` and asserts `argv[0] == sys.executable`, not `python3`, and that the hook file exists. Would it fail on the base code? Optionally run it: `python -m pytest tests/unit/test_cli_audit_remediations.py -q -p no:cacheprovider`; note this writes nothing into the worktree if run with `-p no:cacheprovider`.
5. **Scope.** Only those two files change; no other behaviour in `native_hooks_register` (settings merge, invalid-JSON fail-closed, target path) is altered. No secrets or machine-specific values added.

## 3. Output format
```
TOOL_ACCESS=<FULL|PARTIAL|NONE>
CUSTODY=<MATCH|MISMATCH>  head=<sha>
VERDICT=<PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR>
POINTS:
  1: <UPHELD|DISPUTED|UNVERIFIABLE> — <evidence>
  ... (1-5)
FINDINGS:
  - id: F-01
    severity: <CRITICAL|HIGH|MEDIUM|LOW|INFO>
    blocking: <true|false>
    title: ...
    body: ...
REMAINING_RISKS:
  - ...
```
