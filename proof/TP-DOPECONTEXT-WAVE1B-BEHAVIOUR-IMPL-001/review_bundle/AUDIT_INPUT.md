Independent embedded audit for a PR on DDD-Enterprises/dopemux-mvp:
"feat(dope-context): ADR-226 Amendment A5a — Wave 1b behaviour fixes"
(TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007, Wave 1b slice only).

CONTEXT: This lands ADR-226 Amendment A5a -- an operator-approved,
narrowly-scoped set of 3 new exemptions to the DCP-RED-MERGE-SEAM-0001
red-lane path guard (src/dopemux/dcp/red_lane_rules.py FORBIDDEN_PATHS),
plus the content changes those 3 files were gated on:
services/dope-context/tests/test_wave1_behaviour.py (new),
services/dope-context/src/utils/model_tokenizer.py,
services/dope-context/src/utils/token_budget.py.

IMPORTANT SCOPE BOUNDARY: A companion amendment, A5b (two Voyage client
retry-behaviour files: contextualized_embedder.py, voyage_reranker.py) was
explicitly NOT approved by the operator -- it changes live paid Voyage API
billing behaviour and needs a separate cost/runtime authorization tranche.
Confirm these two files are NOT touched anywhere in this diff and remain
hard-blocked by the regex (no lookahead naming either of them was added).

Also confirm the regex uses \Z + re.DOTALL (the hardened matcher from
TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001 / PR #1322, already merged
to main), NOT the literal $ the source ADR document originally displayed --
the operator explicitly required this correction as a condition of approval.

YOUR TASK -- independently verify, using real filesystem access via
--add-dir to the actual worktree:

1. Confirm the diff touches exactly the 8 files listed in
   DIFF_NAME_STATUS.txt and no others -- especially confirm
   contextualized_embedder.py and voyage_reranker.py are untouched.
2. Read src/dopemux/dcp/red_lane_rules.py's dope-context carve-out entry.
   Confirm exactly 3 new negative lookaheads were added
   (tests/test_wave1_behaviour.py, src/utils/model_tokenizer.py,
   src/utils/token_budget.py), all anchored with \Z (not $), and the whole
   pattern compiles with re.DOTALL.
3. Read services/dope-context/src/utils/model_tokenizer.py's
   VoyageTokenCounter. Confirm _cache is now bounded (max_cache_entries
   constructor param, oldest-first eviction when full) and that this
   genuinely prevents unbounded growth. Independently assess whether the
   "no TTL/expiry needed, unlike voyage_embedder.py's response cache"
   reasoning is sound: is a (model, sha256(text)) -> TokenCount mapping
   really a pure function that can never go stale?
4. Read services/dope-context/src/utils/token_budget.py. Confirm
   budget_starvation and degraded_guarantee_applied are now actually
   assigned (previously declared-and-never-set) on the forced-degrade path
   only, and confirm the token_count preference logic: when an item
   carries a positive-int token_count that fits the per-item budget,
   truncation is skipped; otherwise the existing heuristic-based
   truncate_text_to_tokens still runs. Confirm token_count is popped from
   the item before it's returned (both the normal path and the degraded
   path) so it never reaches a caller/client.
5. Read services/dope-context/src/mcp/server.py's diff. Confirm the only
   change is adding a "token_count" key to the docs raw_results dict
   comprehension, sourced from r.payload.get("token_count") -- and ONLY
   when the char-slice (max_content_length) did not truncate the content
   (i.e. None when it did). Assess whether this conditional is correct:
   why would token_count become untrustworthy specifically when the
   char-slice ran?
6. Run the actual test suite yourself and report real results:
   a. `cd /Users/hue/code/dopemux-mvp/.worktrees/adr226-a5a-wave1 &&
      PYTHONPATH=$(pwd)/services/dope-context uv run --frozen pytest -q
      --no-cov services/dope-context/tests/` -- expect 133 passed, 1
      skipped (baseline was 124 passed, 1 skipped before this PR).
   b. `uv run --frozen pytest tests/test_dcp_surface_guard.py
      tests/dcp/test_dcp_0005_red_lane_scanner.py -q` -- expect 76 passed.
7. Read services/dope-context/tests/test_wave1_behaviour.py in full.
   Assess whether each test genuinely exercises the real code path it
   claims to (not a substring/source scan), specifically:
   - test_tokenizer_cache_evicts_oldest_first_when_bound_reached /
     test_tokenizer_cache_hit_does_not_evict (E10)
   - test_budget_starvation_flags_set_on_forced_degrade /
     ..._false_on_ordinary_truncation / ..._false_on_empty_input (E2/E4)
   - test_token_count_preference_skips_unnecessary_truncation /
     test_token_count_never_reaches_the_returned_item /
     ..._stripped_on_the_degraded_path_too (E17)
   - test_fingerprint_payload_unchanged_by_wave1 -- independently
     reproduce the two pinned digest constants yourself:
     `PYTHONPATH=$(pwd)/services/dope-context uv run --frozen python3 -c
     "from src.index_profile import build_code_collection_profile,
     build_docs_collection_profile; print(build_code_collection_profile(
     environ={}).profile_digest); print(build_docs_collection_profile(
     environ={}).profile_digest)"` and confirm they match what the test
     file hardcodes (a78e8e6bf0aa, bc3e80ff1a1b).
8. Independently perform at least one of the three mutation tests yourself
   rather than trusting the PROOF.json's claim: pick one of E10/E2-E4/E17,
   temporarily revert its fix in your own scratch copy, confirm the
   corresponding test fails, and report what you actually observed.
9. Confirm docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md and
   task-packets/dope-context/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007.md's diffs
   accurately describe what landed (A5a approved/A5b hold, Wave 1b
   delivered/Wave 1a open/Wave 1c hold) rather than overclaiming.
10. Confirm no secrets/credentials appear anywhere in the diff.

Return PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR with findings (id,
severity, title, status, body). Be concrete about what you actually
observed and ran.

ADDENDUM (round 2, squashed into one clean commit): a Copilot review pass
on round 1 of this PR found two legitimate issues, both now fixed --
please specifically confirm both:
- server.py: raw_results previously always included a "token_count" key
  even when the value was None (untrustworthy). Now the key is omitted
  entirely when not trustworthy, not set to None.
- token_budget.py: the token_count validation used
  isinstance(exact_count, int), but bool is an int subclass in Python
  (isinstance(True, int) is True), so a payload with token_count=True
  could have been read as count=1 and silently disabled truncation. Now
  bool is explicitly excluded before the isinstance(int) check.

Worktree: /Users/hue/code/dopemux-mvp/.worktrees/adr226-a5a-wave1
Base (origin/main): 33a38119f97611e391aab719151ffadbf541f06c
Head: 564bc6e6390d9c4e173e0fc07344f15aa0520712
