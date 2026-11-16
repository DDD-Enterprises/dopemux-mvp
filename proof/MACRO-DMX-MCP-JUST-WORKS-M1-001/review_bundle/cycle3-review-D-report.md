# Task D review (cycle 3) — round 0 verdict: NEEDS_FIXES (opus reviewer, read-only; as delivered 2026-11-08)

Subject: HEAD d4e021126 + the uncommitted diff (sha256 576b71aa…765d, byte-identical to cycle3-review-D.diff); exactly the 4 allowed files. Reviewer changed nothing (status and diff sha identical before/after).
Commands: paired tests 97 passed in 4.37s rc=0; flake8 F/E7/E9/W6 on the two modules rc=0; diff --stat 4 files, +118/-14.
RED verified independently: HEAD src + the new tests extracted via git archive → 13 failed (9 F1 + 4 F2), 45 passed; the lookalike end-to-end test failed "DID NOT RAISE McpError" on the old code; old module import confirmed. Tests are not tautological.

## FINDING 1 — medium — src/dopemux/mcp/mcp_json.py:148-149 — F1 not fully closed
Masking now happens first, but `masked.split("://", 1)[-1]` strips at the FIRST `://` anywhere. When a placeholder covers the scheme and `//` (the brief's own `${BASE:-…}` shape), any later literal `://` in the path/query/fragment, or a literal `://` right after a scheme placeholder, becomes the start of the authority; the placeholder never lands in the host slot → False. The netloc backstop does not catch it (`_neutralize_placeholders` yields a clean `http://localhost:3005/…`) → repairable → the planner replaces the operator's URL (mcp_json.py:276, :298-300, :320-325). Same harm as the original F1.
Probe on the worktree code (hostph = `_placeholder_in_userinfo_or_host`), all hostph=False repairable=True (HEAD gives the same, so not new with this diff):
  ${BASE:-http://localhost:3005}/sse?next=http://remote.example · ${BASE:-http://localhost:3005}/sse?next=http://localhost:3005 · ${BASE:-http://localhost:3005}/proxy/http://localhost:3005/sse · ${BASE:-http://localhost:3005}/sse#http://localhost · ${BASE:-http://localhost:3005/sse}?u=ws://localhost:1 · ${SCHEME:-http}://localhost:3005/sse · ${S:-http://localhost:3005/x?}://evil.example:3005/sse · http${X:-}://localhost:3005/sse · http:${X:-}//localhost:3005/sse · http:/${X:-}/localhost:3005/sse
Exact fix (verified by the reviewer on a scratch copy: every row above → hostph=True repairable=False; 97 passed; catalog URLs unchanged):
    _LITERAL_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://")
    masked = _PLACEHOLDER.sub("\x00", url)
    scheme = _LITERAL_SCHEME.match(masked)
    if scheme is None:
        # No literal scheme:// at the start: a placeholder supplies the scheme, the // or the whole base,
        # so a later :// in the path, query or fragment is not the authority.
        return "\x00" in masked
    authority = masked[scheme.end():]
Docstring must say only a literal scheme at the very start is stripped.
Behaviour changes (templated URLs without a literal leading scheme now fail closed): `//localhost:${PORT:-3005}/sse` True→False; `' http://localhost:${PORT:-3005}/sse'` (leading space) True→False; `localhost:3005/${P}` and `${CONPORT_URL}` hostph→True (repairable already False). Every url/url_template in mcp_catalog.yaml and src/dopemux/mcp/default_catalog.yaml starts with a literal `http://` → no catalog URL affected.
Tests to add (each fails on the current worktree code): not repairable: `${BASE:-http://localhost:3005}/sse?next=http://remote.example`, `${SCHEME:-http}://localhost:3005/sse`, `http${X:-}://localhost:3005/sse`, `http:${X:-}//localhost:3005/sse`; hostph True for the same four.

## F2 — closed, no finding
Exact code+message; literal matches SDK 1.29.0 streamable_http.py:519 (only occurrence; sent from the 404 branch :350-355); forward() unchanged (hunks = module docstring line 20 and helper 193-204); other 32600 messages raised to the runner; end-to-end asserts backend.sent == ["tools/call"] and one session; docstrings name `_send_session_terminated_error`.

## Smaller observations (not findings)
Drift-guard skip: find_spec on a missing top-level package raises ModuleNotFoundError (pytest.skip covers only a missing submodule); the test module's own `from mcp import …` fails collection first anyway; mcp>=1.28.1,<2 is a core dependency. Four added comment/docstring lines in the tests are 91-93 chars (E501 outside the brief's selection; black does not reflow comments). Whole-file black "would reformat" the two older files on pre-existing lines only; added-line gate result UNKNOWN (not run by the reviewer).

## What an independent auditor might still raise
1 placeholders before the authority (= FINDING 1 until fixed); 2 in-band spoofable signal: a backend emitting the exact literal after processing gets one resend (no emitter found in src/services/docker; task-orchestrator source not in repo → UNKNOWN; `error.data is None` would narrow, not close; full fix = watch the HTTP 404 at the transport layer); 3 "404 means never processed" rests on the server/SDK rule (a proxy/LB 404 after forwarding breaks it); 4 drift guard reads source text, not the same ErrorData call/404 path; .pyc-only install → origin .pyc → read error, not skip; 5 shell operators other than `:-` (`:=`, `:?`, `:+`, unclosed, nested) unmasked, rely on the `${}` hostname check — every probe came out not repairable; 6 odd port placeholders (`${}`, `${PORT:-1/x}`, `${P:-3005/}${HOST:=evil}`) judged repairable with literal localhost host; 7 templates, not resolved values, are checked (accepted design); 8 `http://[::1]${X}:3005/sse` hostph=False (still not repairable: ::1 not in _LOCAL_HOSTS).

Routing: single reviewer claude-opus-5-5 (effort UNKNOWN), no children, advisor called once. Scratch evidence under the session scratchpad (red_old/, fixprobe/, probe_f1*.py, apply_fix.py).

# Round 1 re-review — APPROVED (same opus reviewer, read-only; as delivered 2026-11-08)
Subject: HEAD d4e021126 + uncommitted diff sha256 ba93b7ab6a169b4e419bc76fed0582b86dc26e0f6e4392d34badd8019d47fa8b (= cycle3-review-D-round1.diff, cmp SAME); exactly the 4 files; worktree unchanged by the reviewer. Custody: the round-0 subject hashed 576b71aa54f4ca9749ac9d323276a52008da48b269512c5c906098539f64765d (cycle3-review-D.diff was later overwritten with the round-1 bytes; both hashes recorded here and in the ledger).
Delta vs round 0: mcp_json.py = the reviewer's prototype verbatim (black spacing) + docstring; stdio_proxy.py byte-identical to round 0 (F2 verdict carries over); tests: the four URLs in both tables, two controls, wrapped comments, try/except ModuleNotFoundError in the drift guard.
(1) Probe re-run: every FINDING 1 row now hostph=True repairable=False (six `${BASE:-…}` variants with a later `://`, `${SCHEME:-http}://…`, `${S:-…?}://evil…`, `http${X:-}://`, `http:${X:-}//`, `http:/${X:-}/`); the three catalog URLs stay repairable=True; the other 32 probe rows unchanged.
(2) Adversarial set (45 URLs, probe_f1_r1.py): all host-moving forms fail closed (placeholder covering `//` or the authority start, mixed-case schemes, invalid scheme, `http://` inside a userinfo default, port placeholder before `@`, backslash forms, leading space/tab/NUL). hostph=False but still not repairable: extra-slash forms (`http:///…`, `http:////…`, `http://http://…`) and unrecognised operators (`:=`). repairable=True only with a literal local host and the placeholder after the port separator or in the path/query (incl. `git+ssh://localhost:${P:-22}/x`). No URL found where a placeholder supplies or moves the host with repairable=True.
(3) Controls hostph=False repairable=True; disclosed behaviour changes confirmed (`//localhost:${PORT:-3005}/sse`, leading-space URL, `localhost:3005/${P}`, `${CONPORT_URL}` → not repairable).
RED re-verified by the reviewer: round-1 tests against a copy with the round-0 `masked.split("://", 1)[-1]` line restored → 8 failed (exactly the 4 new URLs in each table), 101 passed. Drift guard: find_spec raising → SKIPPED; None → SKIPPED; real → PASSED.
(4) Outputs: paired pytest 109 passed in 2.68s rc=0; flake8 F/E7/E9/W6 rc=0; diff --stat 4 files +149/-14; no added line > 88 chars; black: stdio_proxy.py + its test unchanged, the other two files' hunks do not overlap the changed lines.
Docstring nit (non-blocking): mcp_json.py:134 and :138-139 under-describe the no-literal-scheme branch (returns True for `localhost:3005/${P}` although the placeholder is in the path); suggested wording "…not considered here when the URL starts with a literal `scheme://`".
Auditor may still raise: Python vs WHATWG parsing of extra slashes (fail-closed today); the scheme itself is never checked (`git+ssh://` passes the host check); port-adjacent placeholders (`:3005${P}`) repairable by design; templates, not values, are checked; F2 in-band spoof (exact literal after processing → one resend; `error.data` ignored; 404 = never processed is an assumption); drift guard reads source text.
Routing: single reviewer claude-opus-5-5 (effort UNKNOWN), no children, advisor once.
