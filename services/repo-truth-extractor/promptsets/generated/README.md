# `promptsets/generated/` — disposable example output (F-48)

**Disposition: disposable, regenerate on demand.** This tree is not CI-gated and
carries no drift guarantee. See `claudedocs/rte-truth-program-2026-07/CONSOLIDATED-FINDINGS.md`
(F-48) and TP-RTE-TRUTH-R4-006 for the finding this file resolves.

## What this is

Output of the `lib/promptgen/sync_engine.run_sync()` pipeline, invoked via:

```
dopemux rte promptset sync --repo . --no-interactive
```

(legacy alias: `dopemux extractor init`, which now redirects to the command
above — see TP-RTE-TRUTH-R4-002).

`run_sync` fingerprints a target repo, auto-detects features, resolves scope,
renders prompt templates from `services/repo-truth-extractor/base_prompts/`,
and generates a `promptset.yaml` + `model_map.yaml` + `artifacts.yaml`
contract set for it. It is a **universal, repo-agnostic promptset
synthesizer** — a separate, less mature system from the hand-curated,
136-step authoritative promptset at `services/repo-truth-extractor/promptsets/v4/`.

## Why disposable, not CI-gated

Evidence gathered for F-48 (2026-07-27):

1. **Zero runtime consumers.** `run_extraction_v5.py` — the actual v5
   extraction pipeline — reads exclusively from `promptsets/v4/`
   (`v4_prompt_root`, `PROMPTSET_RULES.md`, `promptset.yaml` all resolve
   under `promptsets/v4/`). Nothing under `promptsets/generated/` is loaded
   by any runtime code path.
2. **Zero test consumers of the checked-in snapshot.** `tests/test_universal_extractor.py`
   exercises `sync_engine.run_sync` thoroughly, but against synthetic
   fixture repos under pytest's `tmp_path` — never against this checked-in
   `dopemux-mvp-2e346e2084bc/` directory. No test asserts this directory's
   contents are current or byte-identical to a fresh run.
3. **Output directory name is not portable across checkouts.** The
   subdirectory name is `<repo_root.name>-<sha256(str(repo_root))[:12]>`
   (`sync_engine._compute_repo_hash`) — a hash of the *absolute path* of the
   checkout. A fresh regeneration from this worktree produced
   `focused-mahavira-5bd29b-50e2efdfb313/`, a completely different directory
   name than the checked-in `dopemux-mvp-2e346e2084bc/`, even though both
   describe "the same" repo. A CI runner checkout (yet another path) would
   produce a third name. There is no stable target for a "regenerate and
   diff against HEAD" gate without first changing `run_sync` to accept a
   fixed, environment-independent output slug — out of scope here.
4. **Scope mismatch with v4, not staleness alone.** `base_prompts/` contains
   5 templates today, and the checked-in set reflects exactly 5-of-5
   rendered (matches `SYNC_MANIFEST.json` `templates_rendered: 5`,
   `INTEGRITY_REPORT.json` `promptset_steps: 61`/`steps: 61`). `promptsets/v4/promptset.yaml`
   has 136 steps. This isn't "5 of 137 possible templates went stale" — it's
   two systems at very different levels of completeness; comparing them for
   drift isn't meaningful.
5. **Regeneration is dry-run-safe by default.** `run_sync(interactive=False,
   enrich=False)` (i.e. `--no-interactive` without `--enrich`) makes no live
   LLM/provider calls — `detect_features`, `determine_phase_plan`,
   `resolve_scopes`, and `render_promptset` are all local/deterministic.
   Only the optional `--enrich` flag would require live credentials. This
   was verified by actually running the command in this worktree (dry-run,
   no `--enrich`) — it completed offline in ~35s with 0 errors.

Given no consumer depends on this content being current, a CI gate would add
maintenance cost (and false "drift" alarms from #3 above) without protecting
anything real. The correct fix is documentation + a cheap regenerate path,
not a permanent gate.

## Regenerating

```bash
cd /path/to/dopemux-mvp
PYTHONPATH=src python -m dopemux.cli rte promptset sync --repo . --no-interactive
```

This is offline/deterministic (no `--enrich` flag) and safe to run anytime.
Do not pass `--enrich` unless you specifically want (and have credentials
for) an LLM-assisted enrichment pass — that is the only stage that makes
live provider calls.

The `dopemux-mvp-2e346e2084bc/` example checked into this directory reflects
the state of `base_prompts/` and repo feature-detection at the time it was
generated (see its `SYNC_MANIFEST.json`). It is illustrative only — do not
treat it as authoritative extraction-phase coverage (`promptsets/v4/` is
authoritative for that) and do not assume it reflects the current repo.
