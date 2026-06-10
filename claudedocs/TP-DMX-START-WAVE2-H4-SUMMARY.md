# TP-DMX-START-WAVE2-H4 — Wave 2 Proof Summary

**Branch:** `claude/modest-cartwright-340c04`  
**Base PR:** #842  
**Status:** IMPLEMENTATION_COMPLETE

## Bug fixed

`GAP-H4-BUG`: `config_data` `UnboundLocalError` in `dopemux start --altp` subscription mode.

**Root cause:** In `cli.py`, when `--altp` is passed and routing mode is subscription,
`use_altp` is set to `False` at line 1288. The `if use_altp:` guard at line 1300 is then
`False`, so `config_data` is never assigned. The proxy-startup block then read
`config_data` unconditionally → `UnboundLocalError`.

**Secondary issue (test-only):** The `else:` branch does a local
`from .routing_config import RoutingConfig` that bypasses the module-level mock.
This local import reads the real `~/.dopemux/routing.yaml` (mode=api on the dev machine),
keeping `use_altp=True` in tests and hitting a different failure. Fixed by also patching
`dopemux.routing_config.RoutingConfig.load_default` in both tests.

## Fix applied

| Location | Change |
|---|---|
| `cli.py:1227` | Added `config_data = None` before `if _provider_flags > 0:` |
| `cli.py:1323` | Wrapped proxy-startup block with `if config_data is not None:` |
| `test_start_crit_gaps.py` | Both XFAIL markers removed; added `routing_config.RoutingConfig.load_default` mock; updated docstrings |

## Validation

| Check | Result |
|---|---|
| `compileall` | PASS |
| `pytest TestAltpSubscriptionNoop` | **2 PASS** (was 2 XFAIL) |
| `pytest test_start_crit_gaps.py + test_start_command.py` | 24 PASS |
| XFAIL markers remaining | 0 |
| Wave 1 regressions | None |

## Audit verdict

PASS — `config_data = None` initialization is correct scope; guard is inside the
`_provider_flags > 0` block (correct); all Wave 1 invariants preserved.
