# AUDITOR REPORT — PR #1412 L2 embedded audit (TP-DMX-PR1412-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.2.15, `gemini-3.1-pro-high`, `--sandbox --mode plan`, worktree mounted; instructed not to write files
- **Implementer**: Claude Code (Anthropic Claude) — different runner and model family
- **Audited head**: `a1b4ea9108f09e2b2c8fb9e753d31f2900a20ba6` · **Base**: `20a4d4b12c68836f70ae1f5c9a6846122f00a136` (main after #1389)
- **Verdict**: **PASS_WITH_RISKS**
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json`; prompt `review_bundle/AUDIT_INPUT.md`

## Auditor return (verbatim)

```
TOOL_ACCESS=FULL
CUSTODY=MATCH  head=a1b4ea9108f09e2b2c8fb9e753d31f2900a20ba6
VERDICT=PASS_WITH_RISKS
POINTS:
  1: UPHELD — Checked `src/dopemux/cli.py`. The global branch now assigns `cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(hook_script))}"`. Both `sys` and `shlex` are successfully imported at the top of the file (lines 14, 18).
  2: UPHELD — Inspected `src/dopemux/claude/native_hooks.py` and found it imports from `dopemux.workflow`, meaning it indeed relies on the project's dependencies like `pydantic`. A bare `python3` in an arbitrary directory would fail. `sys.executable` ensures we use the environment dopemux is currently running from (which has the dependencies installed). However, a risk exists for frozen builds.
  3: UPHELD — Reviewed `.claude/hooks/run_native_hooks.sh` and confirmed it dynamically resolves `ROOT` via `git rev-parse --show-toplevel 2>/dev/null || pwd`. If registered globally, this would attempt to execute hooks relative to whatever repository Claude Code is currently inspecting, missing the dopemux source. The diff verifies the non-global branch still uses the wrapper.
  4: UPHELD — The new test `test_native_hooks_register_global_uses_running_interpreter` correctly isolates `HOME`, invokes the CLI with `--global`, and asserts `argv[0] == sys.executable` while explicitly verifying it does not start with `"python3 "`. This test would definitively fail on the base code.
  5: UPHELD — Reviewed the diff. Changes are strictly confined to the `cmd` string modification in `cli.py` for `is_global == True` and the addition of the new test function in `test_cli_audit_remediations.py`. No other behaviors were altered, and no machine-specific hardcoded values were introduced.
FINDINGS:
  - id: F-01
    severity: LOW
    blocking: false
    title: Risk of sys.executable in frozen builds
    body: While `sys.executable` works flawlessly in virtual environments and shim-based runners like `pipx` or `uv tool`, if dopemux is ever distributed as a compiled/frozen binary (e.g. via PyInstaller), `sys.executable` will point to the bootloader binary rather than a standard Python interpreter capable of running `native_hooks.py`.
REMAINING_RISKS:
  - Future distribution of dopemux as a frozen executable could break global hooks due to `sys.executable` resolution returning the bootloader instead of a python runtime.
```
