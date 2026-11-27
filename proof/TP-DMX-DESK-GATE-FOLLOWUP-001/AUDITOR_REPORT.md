I'll audit TP-DMX-DESK-GATE-FOLLOWUP-001 round 3 as an independent reviewer. First I'll read the audit skill and the packet's verdict contract so the checks stay inside the sealed export.

The audit stays with me: delegating the verdict would break independence. Next I’ll pin the subject and read the packet, contract, and diffs.

The contract matches the independent-audit verdict schema. I’ll pin the SHAs and hashes, then read the diffs and the repair.

Desk tests stay on temp ledgers, and the `0.0.0.0` case raises before a bind. I’ll re-run the four required checks next.

Round 3 is **PASS_WITH_RISKS**. The repair closes the round-2 stall for a FIFO, a symlink to a FIFO, a directory, and a device, and every required check passed. F1 is still present. Acceptance is **NOT_GRANTED**.

## Scope
Independent audit of TP-DMX-DESK-GATE-FOLLOWUP-001, round 3, at the pinned exports. The writer was Claude. This review did not implement or supervise the change. No child reviewer was used: the final-audit route requires this reviewer to re-run the checks and decide. Requested model `grok-4.7`, effort `UNKNOWN`. Observed model `UNKNOWN` (no runtime receipt). Cost `UNKNOWN`. No savings claimed.

`shasum -a 256 -c SHA256SUMS.txt` exited 0. `3de60fa9a` is `3de60fa9a2a7d41c5e4b0faadad11f94bb47d99f`. `84bff89` is `84bff89a3683c9796f91ad4f47157f5462ebcd2c`. Both dopemux diff hashes match the files in `inputs/`. From `28ee38ebf` to `3de60fa9a`, the non-proof paths are only `src/dopemux/claude/dispatch_gate.py` and `tests/unit/test_dispatch_gate.py`. Branch HEAD was not queried, so `observed_head` and `head_match` are null. The export was not modified.

`DISPATCH_DESK_LEDGER` and `DISPATCH_DESK_HOME` were unset. Desk HTTP log lines are `127.0.0.1`. `make_server` raises `ValueError` before binding `0.0.0.0` (`serve.py:106`).

The string `IGNORE PREVIOUS INSTRUCTIONS` is a negative fixture at `test_dispatch_gate.py:236` and `test_native_hooks_workflow.py:479`. It does not address this auditor.

## Checks
| Check | Exit | Bucket |
|---|---|---|
| `shasum -a 256 -c SHA256SUMS.txt` | 0 | PASS |
| Allowed git pins, diff hashes, and `diff --name-only` | 0 | PASS |
| `_PINNED` equals sha256 of `gate.py` and `ledger.py` | 0 | PASS |
| `flake8` on the two dopemux files | 0 | PASS |
| `unittest discover -s tools -p 'test_*.py'` | 0 | PASS |
| pytest of the two named files | 0 | PASS |

Desk discovery ran 72 tests in 3.046s, OK. Pytest ran 54 tests in 3.64s, all passed. Round 2 was 50 tests in 3.36s. The four new tests fit in that 0.28s increase, so they did not consume the 2-second join.

## Repair
`_read_verified` opens with `O_RDONLY | O_NONBLOCK | O_CLOEXEC` (`dispatch_gate.py:100-101`), then `os.fstat` on that descriptor (`dispatch_gate.py:103`). The type check is on the opened inode. `O_NOFOLLOW` is absent, so a symlink is followed and `fstat` sees the target.

A FIFO is not a regular file, so the function returns before `os.read`. The same path applies to a symlink to a FIFO, a directory (`S_ISDIR`), and a character or block device. Those descriptors are not read, so an infinite device cannot fill the buffer. `os.close` is in `finally` (`dispatch_gate.py:111-112`), including on the early return. `os.open` failure raises `OSError`, which returns `None` (`dispatch_gate.py:118-119`).

The read asks for at most `_MAX_HELPER_BYTES + 1` (256 KiB + 1). The loop continues while the buffer is non-empty and still within the cap, stops on a zero-length read, and rejects a longer buffer (`dispatch_gate.py:105-114`). An empty regular file produces an empty first read, skips the loop, and fails the hash. A symlink to a regular file whose bytes match the pin still verifies: `test_symlink_to_regular_verified_file_still_runs` passed and returned `GO`.

`None` becomes `UNKNOWN` with `gate identity unverified` before `_run` (`dispatch_gate.py:134-136`). `resolve_gate` still returns `NOT_INSTALLED` when `gate.py` is not a regular file (`dispatch_gate.py:91`, `132-133`). The FIFO `gate.py` test passed with `NOT_INSTALLED`. The FIFO `ledger.py` and symlink-to-FIFO tests passed with `UNKNOWN` and no argv file.

The new tests call `check()` on a daemon thread and `join(2.0)` (`test_dispatch_gate.py:331-345`). On a timeout they open the FIFO with `O_RDWR | O_NONBLOCK`, close that descriptor, join one more second, and fail. This run reached the assertions, so the thread had stored a result and the unblock branch did not run. The success path joins the thread to completion. The read descriptor is closed in `finally`. Directory and device behavior is from this static review. Those two paths are not in the suite. No separate exploit was run.

## S1 and the rest of S2
Dispatch-desk is the same pin as round 2. A GO result writes nothing and does not create a ledger (`gate.py:50`, `ledger.py:50-51`). A pause still appends one `pause_acknowledged` per asker (`gate.py:46-47`). A refusal with a task id appends `gate_checked` with `allowed` false (`gate.py:50-51`). Valid-id exits remain 0, 3, and 4.

The temp copy, `python -I`, and the absence of `--require-approval` are unchanged (`dispatch_gate.py:140-170`). `native_hooks.py` is outside both diffs. Session text still depends on `result.state` only (`native_hooks.py:401-414`). `safe_path` and `mkdtemp` mode were not re-measured. Those code paths are unchanged since round 2.

Round-2 conclusions stand, except the FIFO stall. That remaining risk is narrowed below.

## Findings
F1, low, `dispatch-desk/tools/gate.py:31`. A project id outside `ledger.ID` (`ledger.py:37`), with no task, raises `LedgerError` and the CLI exits 2 (`gate.py:67-69`). The previous body returned GO on that path. Ids the ledger accepts still use exits 0, 3, and 4. The hook maps exit 2 to `UNKNOWN` and still allows work (`dispatch_gate.py:46`, `native_hooks.py:403-404`). The owner had already accepted this finding.

## Unblock
None. The hang repair needs no further code change. Accepting F1 and the residual risks remains the operator's decision.

```json
{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "TP-DMX-DESK-GATE-FOLLOWUP-001",
    "repo": "dopemux-mvp+dispatch-desk",
    "pinned_sha": "dopemux-mvp 3de60fa9a2a7d41c5e4b0faadad11f94bb47d99f; dispatch-desk 84bff89a3683c9796f91ad4f47157f5462ebcd2c",
    "observed_head": null,
    "head_match": null,
    "base": "dopemux-mvp 0aa2cf3497c59f8c607f92986d01e7b7f2620919; dispatch-desk 456244f0f66ddfb06412ac05a1b4d8b501a16b14",
    "file_hashes": {
      "inputs/PRIOR_AUDIT_R2.txt": "526f78ed499cc4e85e1db194e3561483a7311cf1cbadbf9a681ce2afb85bffa2",
      "inputs/TASK_PACKET.md": "a49a75b1cfb91cafcec069a9edcbfe08c9275e376dd9d012398831993da85b9c",
      "inputs/VERDICT_CONTRACT.md": "e32b5edc158f6f01472ef36bb224fb472c9fcdb135b816a44c1622833ee0db0b",
      "inputs/dispatch-desk.diff": "78dadd8723d289983cd54ebcb792c67b90b8d30c80e2bc36b83ec4aeef780bd4",
      "inputs/dopemux-mvp.diff": "895897061665bd3344c93305160c9ba9ce22aeda11784e3fda6a2a7b67bce655",
      "inputs/dopemux-mvp.repair-since-round2.diff": "4f6b502285fee0f8ca95050b35097d100a328080f84d1d04de42d14dfc264cd4",
      "dopemux-mvp/src/dopemux/claude/dispatch_gate.py": "473265629904cc9ebf7ebf7951a24d886f445b2baf06e94bb6c39b41795c6a59",
      "dopemux-mvp/tests/unit/test_dispatch_gate.py": "f45f6f89f838cf66f57904fcf4e4214b500b968d0f903700291fc63f9e5b7d38",
      "dispatch-desk/tools/gate.py": "d6d13111779ab4058f86a4afdce4ca21c309136039ee89df43c08ebfe41dd386",
      "dispatch-desk/tools/ledger.py": "2fec110186e6dfded71001cec2eb74e2aff84f1011623d4a812fe19c961c65fd",
      "dispatch-desk/tools/test_gate.py": "e3dab337a884746aa67d30db7addeb1407f95dfd2a53511ba27c6d2d9c86ede4"
    }
  },
  "auditor": {
    "runner": "grok-cli",
    "model_requested": "grok-4.7",
    "model_observed": "UNKNOWN",
    "effort": "UNKNOWN",
    "independent_of_implementer": true
  },
  "checks": [
    {
      "id": "pin-shasums",
      "command_or_method": "shasum -a 256 -c SHA256SUMS.txt",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "All eleven listed files OK."
    },
    {
      "id": "git-pin",
      "command_or_method": "git rev-parse 3de60fa9a; git rev-parse 84bff89; git diff 0aa2cf349 3de60fa9a -- src tests | shasum -a 256; git diff 28ee38ebf 3de60fa9a -- src tests | shasum -a 256; git diff --name-only 28ee38ebf 3de60fa9a",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "3de60fa9a resolved to 3de60fa9a2a7d41c5e4b0faadad11f94bb47d99f. 84bff89 resolved to 84bff89a3683c9796f91ad4f47157f5462ebcd2c. Full src/tests diff hash 895897061665bd3344c93305160c9ba9ce22aeda11784e3fda6a2a7b67bce655 matches inputs/dopemux-mvp.diff. Repair diff hash 4f6b502285fee0f8ca95050b35097d100a328080f84d1d04de42d14dfc264cd4 matches inputs/dopemux-mvp.repair-since-round2.diff. Name-only lists the two allowlisted dopemux files plus paths under proof/."
    },
    {
      "id": "pin-helpers",
      "command_or_method": "sha256 of dispatch-desk/tools/gate.py and ledger.py compared with _PINNED in dispatch_gate.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "gate.py d6d13111779ab4058f86a4afdce4ca21c309136039ee89df43c08ebfe41dd386 and ledger.py 2fec110186e6dfded71001cec2eb74e2aff84f1011623d4a812fe19c961c65fd both match."
    },
    {
      "id": "flake8",
      "command_or_method": "/Users/hue/code/dopemux-mvp/.venv/bin/flake8 dopemux-mvp/src/dopemux/claude/dispatch_gate.py dopemux-mvp/tests/unit/test_dispatch_gate.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "PYTHONDONTWRITEBYTECODE=1. No flake8 output."
    },
    {
      "id": "desk-discover-exact",
      "command_or_method": "cd dispatch-desk && python3 -m unittest discover -s tools -p 'test_*.py'",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "PYTHONDONTWRITEBYTECODE=1. DISPATCH_DESK_LEDGER and DISPATCH_DESK_HOME unset. Ran 72 tests in 3.046s, OK. HTTP log lines are 127.0.0.1. Gate tests pass a temporary ledger path."
    },
    {
      "id": "pytest-exact",
      "command_or_method": "cd dopemux-mvp && PYTHONPATH=$PWD/src /Users/hue/code/dopemux-mvp/.venv/bin/python -m pytest -q tests/unit/test_dispatch_gate.py tests/test_native_hooks_workflow.py -p no:cacheprovider",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "PYTHONDONTWRITEBYTECODE=1. 54 passed in 3.64s. Round 2 was 50 passed in 3.36s. The four new tests are inside that 0.28s increase."
    },
    {
      "id": "allowlist",
      "command_or_method": "diff headers in inputs/dispatch-desk.diff and inputs/dopemux-mvp.diff, plus git diff --name-only 28ee38ebf 3de60fa9a",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "dispatch-desk diff: tools/gate.py, tools/test_gate.py. dopemux src/tests diff: src/dopemux/claude/dispatch_gate.py, tests/unit/test_dispatch_gate.py. Since 28ee38ebf the other changed paths are under proof/. native_hooks.py is absent from both diffs."
    },
    {
      "id": "s1-readonly-go",
      "command_or_method": "Read gate.py check() and ledger.read(); unittest discovery includes test_gate.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "GO returns before append when the ledger is missing or unreadable (gate.py:37-38, ledger.py:50-51). gate_checked runs only when task is set and code != GO (gate.py:50-51). Pause acknowledgement remains (gate.py:46-47). CLI LedgerError exits 2 (gate.py:67-69). The malformed-project delta is F1."
    },
    {
      "id": "s2-verify-before-exec",
      "command_or_method": "Read dispatch_gate.py check(), _run(), and native_hooks.py _desk_gate_context; exact pytest",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Identity failure returns UNKNOWN before _run (dispatch_gate.py:134-136). Absent gate returns NOT_INSTALLED (dispatch_gate.py:132-133). Executed path is the temp copy under python -I (dispatch_gate.py:140-170). --require-approval is absent from argv. Hook text uses result.state only (native_hooks.py:401-414)."
    },
    {
      "id": "repair-nonblock-read",
      "command_or_method": "Read _read_verified (dispatch_gate.py:94-120) and the new tests (test_dispatch_gate.py:331-389); exact pytest",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "open uses O_RDONLY|O_NONBLOCK|O_CLOEXEC. S_ISREG is os.fstat of that fd. Non-regular fds return before read and close in finally. The read loop caps at _MAX_HELPER_BYTES+1 and stops on a zero-length read. FIFO ledger.py, FIFO gate.py, symlink-to-FIFO, and symlink-to-regular-file tests passed inside the 54. Directory and device behavior is static review of the same branch."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "low",
      "location": "dispatch-desk/tools/gate.py:31",
      "summary": "A project id outside the ledger ID pattern, with no task, now exits 2. The previous check returned GO and wrote nothing.",
      "evidence": "gate.py:31-34 raises LedgerError before the read when project or task fails ledger.ID (ledger.py:37). main() maps that to exit 2 (gate.py:67-69). Ids the ledger accepts still use exits 0, 3, and 4 (test_gate.py:105-111). The hook maps exit 2 to UNKNOWN and still allows work (dispatch_gate.py:46, native_hooks.py:403-404). Desk sources are unchanged since round 2."
    }
  ],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [],
  "remaining_risks": [
    "Same-uid replacement of the temp copy is possible after the write and before python -I reads gate.py and imports ledger (dispatch_gate.py:140-146). This path is unchanged since round 2. mkdtemp mode was not re-measured this round.",
    "shutil.rmtree(tmp, ignore_errors=True) can leave the temp directory (dispatch_gate.py:148). subprocess.run's timeout does not reap the child (dispatch_gate.py:169-170).",
    "No test executes the pinned gate.py and ledger.py bytes through the temp-copy path. The temp-copy test runs a fake gate.",
    "os.open and a regular-file os.read have no deadline. After a successful open, a non-regular descriptor is closed without a read. A kernel stall inside open, or inside read of an inode fstat classifies as regular, can still stall check() before UNKNOWN."
  ],
  "unknowns": [],
  "skip_reason": null,
  "unblock": [],
  "acceptance": "NOT_GRANTED"
}
```
