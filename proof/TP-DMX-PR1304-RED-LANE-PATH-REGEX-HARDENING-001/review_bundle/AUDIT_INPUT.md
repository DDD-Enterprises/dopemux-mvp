Independent embedded audit for PR #1322 on DDD-Enterprises/dopemux-mvp:
"fix(dcp): harden red-lane FORBIDDEN_PATHS anchoring against control
characters" (TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001).

This touches a SECURITY-RELEVANT enforcement surface: the
DCP-RED-MERGE-SEAM-0001 red-lane path guard (src/dopemux/dcp/red_lane_rules.py
FORBIDDEN_PATHS + .claude/hooks/dcp_surface_guard.py surface_guard_block).
This guard hard-blocks Edit/Write/NotebookEdit calls to a fixed list of
protected paths. It is being changed ahead of a planned follow-up (ADR-226
Amendment A5a) that will add three new exemption entries to the same
regex list -- so precision here matters more than usual.

CLAIM BEING MADE: Python's `$` regex anchor matches immediately before a
*trailing* newline (not strictly end-of-string), and `.` never crosses a
newline without re.DOTALL. The claim is that this combination could make an
`^`-anchored, `.*$`-tailed FORBIDDEN_PATHS entry silently fail to match at
all when file_path contains an embedded/trailing control character --
falling through to "not blocked" -- or make a negative-lookahead exemption
falsely treat a control-character-suffixed string as equivalent to the real
exempted filename. The fix: replace `$` with `\Z` everywhere in
FORBIDDEN_PATHS and add `re.DOTALL` to every pattern containing `.*`, PLUS
an independent, unconditional control-character fail-closed check in
surface_guard_block itself (defense in depth).

YOUR TASK -- verify or refute this claim and audit the actual diff, using
real filesystem/tool access via --add-dir to the actual worktree:

1. Read the actual diff (see DIFF_NAME_STATUS.txt and the worktree itself)
   and confirm it touches ONLY the three files listed -- no product/service
   code, no other red-lane entries beyond anchor precision, no widening of
   any FORBIDDEN_PATHS pattern's matched-path SET for ordinary
   (control-character-free) input.
2. Independently verify the regex claim yourself: write a small Python
   repro (you have real tool access) that demonstrates, against the
   PRE-change pattern style (`$` + no DOTALL), a file_path string that
   fails to match a `.*$`-tailed forbidden pattern at all due to an
   embedded non-trailing newline, and confirm the POST-change pattern
   (`\Z` + `re.DOTALL`) correctly matches (blocks) that same string. Report
   your actual repro output, not just agreement with the claim.
3. Confirm the new control-character check in dcp_surface_guard.py
   (_has_control_chars / the block in surface_guard_block) is
   unconditional, checked before pattern matching, and cannot be
   accidentally bypassed by a normalization step that runs before it.
4. Confirm the fix does not change behavior for any ordinary path with no
   control characters -- spot check several of the existing carved-out and
   still-blocked dope-context paths mentally against both old and new
   patterns.
5. Run the actual test suite yourself and report the real results:
   `cd /Users/hue/code/dopemux-mvp/.worktrees/red-lane-hardening-1304 &&
   uv run --frozen pytest tests/test_dcp_surface_guard.py
   tests/dcp/test_dcp_0005_red_lane_scanner.py -v`
6. Scan for anything security-sensitive beyond the stated scope: does this
   diff weaken any existing block, widen any carve-out, or introduce a new
   bypass class of its own (e.g. does the control-character check itself
   have a gap -- Unicode line separators, other bypass-relevant characters
   outside the ASCII 0x00-0x1F/0x7F range)?
7. Confirm no secrets/credentials appear anywhere in the diff.

Return PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR with findings (id,
severity, title, status, body). Be concrete about what you actually
observed and ran -- this is a security-relevant enforcement change and
deserves genuine adversarial scrutiny, not a rubber stamp.

ADDENDUM (round 2, squashed into one clean commit): a first Copilot review
pass on this PR correctly found that the original newline-regression tests
only exercised the new control-character short-circuit in
surface_guard_block (which returns before ever evaluating FORBIDDEN_PATHS),
so they never actually proved the \Z + re.DOTALL anchoring fix on its own.
Fixed by adding a `_matches_forbidden_pattern()` helper that imports
FORBIDDEN_PATHS directly and asserts pattern.search() on the newline-bearing
strings, bypassing the guard entirely, plus a sanity check that ordinary
exempt paths still don't match. Please specifically confirm this addresses
Copilot's finding -- that the regex-level fix is now independently proven,
not just the defense-in-depth control-character layer.

Worktree: /Users/hue/code/dopemux-mvp/.worktrees/red-lane-hardening-1304
Base (origin/main): 8910fd64c38e438b1cfbf9a77c6217511d8c7374
Head (PR #1322): 892b856d33574fa2b76a9d21f96c7edc4b032d99
