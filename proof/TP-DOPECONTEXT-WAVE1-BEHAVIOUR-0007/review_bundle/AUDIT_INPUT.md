# Independent embedded audit — PR #1318 (DDD-Enterprises/dopemux-mvp)

You are the independent auditor. You have read access to the repository worktree at:

`/Users/hue/code/dopemux-mvp/.worktrees/dope-context-wave-reconciliation-001`

Use your file tools to read files there directly. **Do not trust any claim in this prompt.
Verify each one against the files.** Where you cannot verify a claim from the worktree, say
NOT_VERIFIABLE and say why — do not guess, and do not mark something PASS because it sounds
plausible.

## Subject

PR #1318, head `1f6af050aca60a21c10c280756f22358fc3596ec`, base `main` (branched from
`f7f0ed626`). It is **documentation only**. Four files:

1. `claudedocs/dope-context-wave-reconciliation-2026-09-04.md` (new) — a reconciliation record
2. `task-packets/dope-context/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007.md` (new) — a task packet
3. `docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md` — append-only, adds "Amendment A5"
4. `claudedocs/dope-context-retrieval-redesign-2026-09-03.md` — appends a "Revision 3" section
   and edits the frontmatter `status:` line

Reproduce the diff yourself with:
`git -C "/Users/hue/code/dopemux-mvp/.worktrees/dope-context-wave-reconciliation-001" diff --stat f7f0ed626..1f6af050a` and `git -C "/Users/hue/code/dopemux-mvp/.worktrees/dope-context-wave-reconciliation-001" diff f7f0ed626..1f6af050a`.

## The claims to audit

The record makes six findings and one ruling. Verify each **against the repository**, not against
the record's own prose.

**C1 — Two Wave 1 definitions.** The record claims
`claudedocs/dope-context-retrieval-redesign-2026-09-03.md` specifies Wave 1 twice: in its "§7
Implementation plan" section and again in "Revision 2" under the item beginning "7 Waves
(supersedes; file-disjoint)", and that Revision 2's header says the later revision wins. Verify
both locations exist, that the supersession statement exists, and that the two owner-file lists
genuinely differ. The record claims they differ in 6 of 12 files — check that count.

**C2 — `chunker_version` is a collection-identity input.** The record's central ruling depends on
`chunker_version` being a member of `VectorProfile.fingerprint_payload()` in
`services/dope-context/src/index_profile.py`. Verify it, and verify that the value returned by
`fingerprint_payload()` feeds `fingerprint_profiles()` and thence the collection digest/name.
If this is false the whole ruling collapses — check it carefully.

**C3 — The already-done list.** The record and packet claim these are ALREADY closed on this
branch and need no work. Verify each against the named file and line:
 - E3: `services/dope-context/src/rerank/voyage_reranker.py` lines ~29-33, ~180, ~258, and
   `services/dope-context/src/mcp/server.py` lines ~1351-1353 and ~1380-1381
 - E11: `services/dope-context/src/embeddings/voyage_embedder.py` lines ~188-201
 - E21: `voyage_embedder.py` ~78-79 and
   `services/dope-context/src/embeddings/contextualized_embedder.py` ~60-61

**C4 — The still-open list.** Verify each of these is genuinely still a defect:
 - E1: no `max_retries` on the Voyage `AsyncClient` at `voyage_embedder.py:129`,
   `contextualized_embedder.py:109`, `voyage_reranker.py:112`
 - E16: `voyage_embedder.py` ~140-154 — is `await asyncio.sleep(...)` inside
   `async with self._rate_limit_lock`?
 - E10: `services/dope-context/src/utils/model_tokenizer.py` ~57/111/122 — unbounded cache?
 - E2/E4: `services/dope-context/src/utils/token_budget.py` ~35-36 — are `budget_starvation`
   and `degraded_guarantee_applied` declared and NEVER assigned anywhere in that file?
 - C1defect: `server.py` ~981 and ~1073 vs the dataclass default at
   `services/dope-context/src/pipeline/indexing_pipeline.py:48`
 - C6: `indexing_pipeline.py` ~484
 - C13: `server.py` ~1309-1310
 - The A4 residual: `voyage_embedder.py:43` `EmbeddingRequest.truncation: bool = True` while
   the public method defaults at ~278 and ~339 are `False`

**C5 — The E17 asymmetry.** The record claims docs payloads already carry a real token count
(`services/dope-context/src/pipeline/docs_pipeline.py` ~208 writes `token_count`, sourced from
`services/dope-context/src/preprocessing/document_processor.py` ~507/541) while code payloads
carry none (`indexing_pipeline.py` writes no token key). Verify both halves.

**C6 — The proposed A5 regex.** ADR-226's new Amendment A5 specifies five added negative
lookaheads to the carve-out entry in `src/dopemux/dcp/red_lane_rules.py`. Verify:
 (a) the amendment's quoted "current" regex matches what is actually in
     `src/dopemux/dcp/red_lane_rules.py` today;
 (b) `red_lane_rules.py` is **UNCHANGED** by this PR — the amendment must be proposal-only.
     This is a hard requirement; if the regex was applied, that is a BLOCKER.
 (c) the amendment's status block says `AMENDMENT_STATUS=PROPOSED` with no operator approval.
 (d) With the five lookaheads added, work out whether these are exempt or blocked, and say if
     the amendment's own "Invariants preserved" section gets any of them wrong:
     exempt-expected: `services/dope-context/tests/test_wave1_behaviour.py`,
     `.../src/utils/model_tokenizer.py`, `.../src/utils/token_budget.py`,
     `.../src/embeddings/contextualized_embedder.py`, `.../src/rerank/voyage_reranker.py`;
     blocked-expected: `.../src/utils/workspace.py`, `.../src/utils/metrics_tracker.py`,
     `.../tests/conftest.py`, `.../src/search/hybrid_search.py`,
     `.../src/preprocessing/code_chunker.py`, `.../src/utils/model_tokenizer.py.bak`,
     and the traversal form `services/dope-context/src/utils/../utils/model_tokenizer.py`.

**C7 — Scope discipline.** Verify the PR changes NOTHING under `services/dope-context/` and
NOTHING in `src/dopemux/dcp/`. Any such change is a BLOCKER.

**C8 — Internal consistency.** The record, the packet and Amendment A5 must agree with each
other on: the number of new exemptions (5), which files are in A5a vs A5b, which files are
already exempt and under which amendment (base carve-out / A2 / A3 / A4), and the already-done
vs still-open split. Report any disagreement between the three documents.

**C9 — Overclaiming.** Flag any place where these documents assert something as verified that
they do not actually establish, or state a status more favourable than the evidence supports.
The repository convention is that PASS / FAIL / NOT_RUN are distinct and NOT_RUN is never
collapsed into PASS.

## Known limitation, stated up front

The record's finding "R-6" claims the guard is absent from a *different* checkout
(`/Users/hue/code/dopemux-mvp` on branch `pr-92`) that is outside your mounted directory. You
cannot verify that from this worktree. Mark it NOT_VERIFIABLE rather than PASS or FAIL, and say
so. Do check the narrower sub-claim you CAN see: that this worktree DOES contain
`.claude/hooks/dcp_surface_guard.py` and `src/dopemux/dcp/red_lane_rules.py`.

## Required output

Return **only** a single JSON object, no prose before or after:

```json
{
  "verdict": "PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR",
  "blocking_count": 0,
  "claims": [
    {"id": "C1", "result": "VERIFIED | REFUTED | PARTIAL | NOT_VERIFIABLE", "evidence": "file:line and what you actually read", "note": ""}
  ],
  "findings": [
    {"id": "F-001", "severity": "BLOCKER | HIGH | MEDIUM | LOW | INFO", "title": "", "body": "", "file": "", "line": 0}
  ],
  "remaining_risks": [""],
  "summary": "two or three sentences"
}
```

`verdict` must be FAIL if any BLOCKER is present. Be adversarial: a documentation PR that
misstates the code it reasons about is worse than one that says less.
