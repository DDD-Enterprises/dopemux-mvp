# Independent Final Tier-1 Audit C3: TP-DMX-MD-R7-HOOKS-VALIDATOR-001

| Field | Value |
|---|---|
| Auditor identity | claude-code-cli:sonnet (requested). Observed model ID is `claude-sonnet-5-5` as reported by the runtime, with no independent receipt, so the observed identity is UNKNOWN. |
| Target commit | `6451fb02fbddcef7d38228792426412789f929c1` (HEAD matches; 1 commit above base `52591ccf4`) |
| Base | `52591ccf403523bce6a4684179ea74ebe889cbde` |
| **Audit decision** | **PASS_WITH_RISKS** |
| Findings | 0 blocking, 2 Medium, 3 Low |

## Findings summary

| ID | Severity | Description |
|---|---|---|
| C3-F01 | Medium | `run_native_hooks.sh` overwrites `CLAUDE_PROJECT_DIR` with `git rev-parse --show-toplevel` of the current directory, ignoring the value the harness passes in. I ran the wrapper from a different git repo with `CLAUDE_PROJECT_DIR` pointing at the real project. It failed with exit 2 ("can't open file …/src/dopemux/claude/native_hooks.py"). The old command used `$CLAUDE_PROJECT_DIR` directly and did not have this problem. In Claude Code, exit 2 on `PreToolUse` blocks the tool call, though I did not test that. Suggested fix: `ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"`. |
| C3-F02 | Medium | `.codex/hooks.json` does not use `run_native_hooks.sh`. It has zero references to it and inlines a 10-event copy of the old logic (`ROOT` from git, `.venv/bin/python` or `python3`). The inlined copy has no `PYTHONPATH` site-packages injection and has the same cwd defect as C3-F01, which I reproduced with exit 2. The wrapper's header says it is a "shared dispatcher … across Claude Code and Codex", which is not true. The two copies can now drift, and no test covers `hooks.json`. |
| C3-F03 | Low | `native_hooks_register` in `cli.py`: only the non-global path now uses the wrapper. `--global` still registers a bare `python3 <abs path>`, so the "no pydantic" failure remains for global registration. The only existing test touching this function (`test_native_hooks_register_refuses_invalid_settings_json`) covers invalid-JSON refusal, not the new command string. |
| C3-F04 | Low | VSH-002 is strict by design, but there is no grandfathering. I validated tracked legacy packets under `proof/pr_merge/embedded-audit/`. `pr-1062` passed the schema at base and fails at head (`report_path` points at `PROOF.json`). `pr-1076` fails on the same check. `pr-1089` already failed at base for other schema errors, so that one is not a regression. At least 10 tracked packets sit in this directory. Any future PR that touches them will now fail, so this is intended but needs a migration or exemption policy. |
| C3-F05 | Low | VSH-001 gaps. (a) `find-principals` output is reduced with `head -n 1`, so only the first principal is verified when several match. (b) stderr is suppressed with `2>/dev/null || true`, which hides diagnostics. (c) `config/audit/embedded-audit-allowed-signers` is a path relative to the current directory, with no `cd` to the repo root (consistent with the relative `PROOF_DIR`, but undocumented). (d) The tests cover stale-`.sig` removal and an unallowed signer. They do not cover an empty or uncreated `.sig` or a missing allowed-signers file. The post-sign `verify` is a self-consistency check, not an independent one. |

## Verified items

**Task 1, scope: PASS.** `git diff --name-status` lists exactly the 10 allowlisted files: 6 modified or added source files plus the packet and 2 new tests. Nothing else changed. The diff is 585 insertions and 26 deletions.

**Task 2, exclusion invariant: PASS.** `git ls-tree -r <head>` contains no `TP-DMX-MD-BINARY-001`, `TP-DMX-MD-UI-A11Y-001` or `TP-DMX-MD-UI-CLIPBOARD-001`.

**Task 3, VSH-001: PASS_WITH_RISKS.** `scripts/audit/sign_local_audit_proof.sh`:
- The stale `.sig` is removed with `rm -f` before signing.
- The `[ -s ]` non-empty check runs after signing.
- `find-principals` runs against the allowed-signers file and fails closed when it returns nothing.
- `ssh-keygen -Y verify` runs with the namespace, and `set -euo pipefail` is in force.
- The "signed:" message is only reached after all checks pass.
- Risks are in C3-F05.

**Task 4, VSH-002: PASS_WITH_RISKS.** `scripts/governance/validate_change_contract.py`:
- The `proof/pr_merge/` branch that copied the schema and popped `report_path.pattern` is gone, so the canonical schema applies to all paths. The schema pattern is `^proof/[^/]+/AUDITOR(_REPAIR(_[0-9]+)?)?_REPORT\.md$`.
- The removal is covered by `test_report_path_pattern_not_softened_for_pr_merge_path`.
- Empirically, pr-1062 passes at base and fails at head (C3-F04).

**Task 5, hook dispatch: PARTIAL.**
- `.claude/settings.json`: all 11 events now call `sh "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/run_native_hooks.sh"`. Each event appears exactly once and no `python3 …native_hooks` references remain.
- `.claude/hooks/run_native_hooks.sh`: added with mode 100755. It picks `.venv/bin/python`, falls back to `python3`, fails with a message when neither exists, and injects site-packages.
- `.claude/claude.md` is consistent with the change.
- `cli.py`: the non-global path uses the wrapper. The global path does not (C3-F03).
- `.codex/hooks.json` does not go through the wrapper (C3-F02). It has 10 events and no `PostToolUseFailure`. Whether Codex supports that event is UNKNOWN.

**Task 6, tests: PASS.**
- Command: `.venv/bin/pytest tests/audit/test_sign_local_audit_proof.py tests/governance/test_change_contract_proof_schema.py tests/governance/test_validate_change_contract.py tests/unit/test_cli_audit_remediations.py`
- Result: 59 passed in 3.22s, 0 failed. HEAD was confirmed as the candidate commit before the run.

## Validation buckets

| Check | State |
|---|---|
| Scope allowlist | PASS |
| Exclusion invariant | PASS |
| VSH-001 static review | PASS_WITH_RISKS |
| VSH-002 static review | PASS_WITH_RISKS |
| Hook wrapper cwd behaviour (foreign git repo) | FAIL, exit 2 (C3-F01, C3-F02) |
| 4 specified test files | PASS (59/59) |
| Hook wrapper run from the project cwd | NOT_RUN |
| Full test suite, lint, mypy | NOT_RUN |
| Live Claude Code or Codex hook execution | NOT_RUN |
| `ssh-keygen` end-to-end signing outside the tests | NOT_RUN |

## Residual risks

1. **Hook robustness (C3-F01 and C3-F02).** Hooks can fail with exit 2 when the session cwd is outside the project's git root. The change fixes the missing-dependency failure but introduces a new cwd-dependent failure.
2. **Dual dispatch paths.** The Codex inline copy and the shell wrapper can drift, and there is no test for the wrapper or `hooks.json`.
3. **Global registration** still has the bare-`python3` weakness.
4. **Legacy proof packets** under `proof/pr_merge/embedded-audit/` will fail schema validation whenever they are touched.
5. **Working tree outside the audited commit.** It also has untracked `proof/TP-DMX-MD-R7-HOOKS-VALIDATOR-001/` and two modified `.claude/*cache.json` files. I did not audit these. They are not in `6451fb02f`.
6. **Independence.** No advisor or secondary model was consulted. This audit relied on deterministic local checks and my own inspection.

**Recommendation:** C3-F01 and C3-F02 are cheap to fix, so I'd correct them before relying on this for the hook-reliability goal. Neither blocks the contract-level hardening goals (VSH-001 and VSH-002), which are met. This audit carries no merge authority; PR Steward and the operator decide that.
