# Task D (cycle 3) implementer report — as delivered 2026-11-08 (sonnet implementer; controller-verified below)

Both findings fixed in the four allowed files; paired test run green (97 passed). `black --check` exits 1 only on lines not touched (left alone as instructed). No commit/stage/stash/push. Interpreter `.venv/bin/python`.

## 1. RED evidence (new tests before each fix)
F1 (original mcp_json.py), 9 failures in tests/unit/test_mcp_config_repair.py:
  test_url_is_repairable_templated_and_literal[http://${HOST:-localhost/path}/sse-False], [...?x...], [...#x...], [${BASE:-http://localhost:3005}/sse-False];
  test_placeholder_in_userinfo_or_host_masks_before_splitting[http://${HOST:-localhost/path}/sse-True], [?x], [#x], [http://${U:-a/b}@localhost:3005/sse-True], [${BASE:-http://localhost:3005}/sse-True]
  (AssertionError: assert True is False / assert False is True). `${BASE:-http://localhost:3005}/sse` fails RED today (confirmed as asked).
  `http://${U:-a/b}@localhost:3005/sse` was wrong only when `_placeholder_in_userinfo_or_host` is called directly; via `_url_is_repairable` the netloc backstop already made it False.
  `http://${HOST:-user@localhost}:3005/sse` and `http://${HOST:-localhost:3005}/sse` already returned False before the fix; kept as regression cases.
F2 (substring test temporarily restored), 4 failures in tests/unit/test_mcp_stdio_proxy.py:
  test_session_terminated_is_exact_code_and_message[32600-Not Session terminated; write already committed-False], [32600-Session terminated.-False], [32600- Session terminated-False];
  test_proxy_does_not_resend_a_lookalike_error_that_may_have_committed — Failed: DID NOT RAISE McpError (the proxy resent and the second send succeeded).
  First version of the end-to-end test used a fixture mode name that never installed the fake transport; renamed to `terminated_lookalike`; the 4-failure run is the corrected one.

## 2. Diff summary
 src/dopemux/mcp/mcp_json.py          | 16 ++++++---
 src/dopemux/mcp/stdio_proxy.py       | 19 +++++++----
 tests/unit/test_mcp_config_repair.py | 34 +++++++++++++++++++
 tests/unit/test_mcp_stdio_proxy.py   | 63 ++++++++++++++++++++++++++++++++++--
 4 files changed, 118 insertions(+), 14 deletions(-)
F1: `_placeholder_in_userinfo_or_host` masks every `_PLACEHOLDER` match to "\x00" over the whole URL, then strips the scheme and splits on / ? #, then the existing userinfo/host logic on the masked authority; docstring says why masking comes first. `_neutralize_placeholders` and the rest of `_url_is_repairable` untouched; the `${}`-in-netloc backstop remains.
F2: `_session_terminated` requires `error.code == 32600 and error.message == "Session terminated"`; its docstring and the module docstring bullet describe exact matching and name `_send_session_terminated_error`. Nothing in `forward()` changed.
Tests: parametrized `test_url_is_repairable_templated_and_literal` extended with the brief's not-repairable and control URLs; new `test_placeholder_in_userinfo_or_host_masks_before_splitting`. Proxy: `test_session_terminated_is_exact_code_and_message` table; end-to-end `test_proxy_does_not_resend_a_lookalike_error_that_may_have_committed` (McpError 32600 + exact message to the runner, `backend.sent == ["tools/call"]`, 1 session, proxy still serving); drift guard `test_sdk_still_answers_a_dead_session_with_the_exact_literal` (reads the SDK source via importlib.util.find_spec(...).origin, skips if not importable, asserts both `message="Session terminated"` and `code=32600`). `_Backend` fixture gained a `sent` list, a `terminated_lookalike` mode, and an optional trailing `sent` parameter on the static `_terminate` (static form kept: two existing tests call it directly).

## 3. GREEN
.venv/bin/python -m pytest tests/unit/test_mcp_config_repair.py tests/unit/test_mcp_stdio_proxy.py -q → 97 passed in 4.44s. Existing resend-once tests pass unchanged.

## 4. Tool outputs
black --check (4 files): would reformat src/dopemux/mcp/mcp_json.py; would reformat tests/unit/test_mcp_config_repair.py; "2 files would be reformatted, 2 files would be left unchanged" (exit 1). Every hunk in black --diff is on an untouched line: mcp_json.py old lines 191, 225, 271, 296, 328, 356, 369 (edit is at 136-160); test_mcp_config_repair.py hunks before ~line 250 (additions start at 374). stdio_proxy.py and test_mcp_stdio_proxy.py black-clean.
isort --check-only (4 files): exit 0. flake8 --select F,E7,E9,W6 on the two modules: exit 0. git diff --stat: as above.

## 5. Deviations / STOP
None hit; only the four files changed. First `sed -i` attempts failed on BSD sed and changed nothing; switched to Python edits. For the F2 RED the substring test was restored temporarily, then the fixed version restored (controller check: `grep -n "error.message ==" src/dopemux/mcp/stdio_proxy.py`). Advisor not called (short mechanical task).

## 6. What an auditor might still raise
Unclosed/malformed placeholders (`${UNCLOSED`, nested `${A${B}}`) are not masked and rely on the unchanged netloc backstop. Empty/no-scheme authorities and IPv6 bracket edge cases not exhaustively tested (only `[${HOST:-::1}]`). `_session_terminated` ignores `error.data`; the exact literal depends on SDK 1.29; the drift guard greps the SDK source rather than exercising the transport. Pre-existing black drift in the two touched files (unrelated).

## Controller verification (2026-11-08)
git status: exactly the four files. Source hunks read and match the above (mask-first; exact equality). Controller run: 97 passed in 3.53s; flake8 F/E7/E9/W6 on the two modules rc=0. `error.message ==` present in stdio_proxy.py. Added-line black/isort gate and per-file lint deltas run at the committed head (cycle2-gates.sh).

# Fix round 1 (same sonnet implementer; from review FINDING 1) — as delivered 2026-11-08
RED before the fix (8 failures: the four new URLs once in each table): `${BASE:-http://localhost:3005}/sse?next=http://remote.example`, `${SCHEME:-http}://localhost:3005/sse`, `http${X:-}://localhost:3005/sse`, `http:${X:-}//localhost:3005/sse` — False expected in the repairable table / True expected in the direct test; "8 failed, 64 passed in 1.11s". The two controls (`http://localhost:3005/sse?next=http://remote.example`, `http://localhost:${PORT:-3005}/sse?u=ws://x`) passed before the fix.
Change: module-level `_LITERAL_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://")`; `_placeholder_in_userinfo_or_host` masks, then `scheme = _LITERAL_SCHEME.match(masked)`; `if scheme is None: return "\x00" in masked`; `authority = masked[scheme.end() :]`; docstring states only a literal leading scheme is stripped and templated/scheme-relative bases fail closed. Drift guard wraps `find_spec` in try/except ModuleNotFoundError → skip. Four added lines over 88 chars wrapped (added-line awk check: none over 88).
GREEN: 109 passed in 3.18s. black --check: "would reformat" mcp_json.py and test_mcp_config_repair.py on pre-existing lines only (hunks at old lines 200/234/280/305/337/365/378 and 64/141/164/229; edits at 119-161 and 374/404); isort exit 0; flake8 F/E7/E9/W6 exit 0; diff --stat 4 files, +149/-14.
Deviations: none. Auditor may still raise: templated URLs with no literal scheme (`${CONPORT_URL}`, `${H}:3005/x`) now return True (fail closed, broader than "placeholder in host slot"); unusual schemes / schemeless templates beyond the listed cases; malformed placeholders rely on the netloc backstop; F2 ignores `error.data`; drift guard greps source.

## Controller verification, round 1 (2026-11-08)
git status: exactly the four files. Hunk read: `_LITERAL_SCHEME` match at start, fail-closed return, slice after the scheme. Controller run: 109 passed; flake8 rc=0; 0 added lines over 88 chars. Diff saved as cycle3-review-D-round1.diff (and cycle3-review-D.diff for the re-review).
