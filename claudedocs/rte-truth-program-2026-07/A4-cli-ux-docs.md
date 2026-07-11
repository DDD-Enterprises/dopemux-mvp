# A4 — RTE CLI/UX & Docs Audit (RTE-TRUTH program)

- **Audit pass**: A4 of RTE-TRUTH
- **Worktree**: `/Users/hue/code/dopemux-mvp/.claude/worktrees/focused-mahavira-5bd29b`
- **HEAD**: `542c17bb4753d3440f73ac09c5e7042fd00cfecb` (branch `claude/rte-audit-improvement-f4beb7`)
- **Method**: static code reading (`src/dopemux/cli.py`, `src/dopemux/commands/{audit,extract,extractor,upgrades}_commands.py`, `src/dopemux/ux/wizard/*`, `services/repo-truth-extractor/run_repscan.py`, `run_extraction_v5.py` prescan sections) + docs grep sweep. No live LLM calls; no `--execute`; one attempted `--help` invocation was not completed (harness classifier outage), so all findings are code-derived. Validation bucket for CLI runtime behavior: **NOT_RUN** (static analysis only).

---

## 1. Entry-surface map

### 1.1 The four surfaces and where commands actually live

| Surface | Definition site | Visibility | Notes |
|---|---|---|---|
| `dopemux rte` | group `rte` at `cli.py:5028`; commands **attached** via `rte.add_command(...)` at `cli.py:5711–5718`, `5730–5741` | visible, canonical | Only `scan` (`cli.py:5034`) and the `promptset` group shell (`cli.py:5730`) are *defined* on `rte`. Everything else is borrowed. |
| `dopemux upgrades` | group in `src/dopemux/commands/upgrades_commands.py:22`; **all core subcommands defined here-adjacent in `cli.py` via `@upgrades.command(...)`**: `list` :5103, `run` :5136, `doctor` :5373, `status` :5412, `preflight` :5438, `validate-live` :5480, `promptset audit` :5604/5610, `trace` :5642 | **live + unhidden** (help overwritten at `cli.py:3258` to say "Legacy compatibility alias") | This is the real definition site. `rte` is the alias in code, inverse of the documented posture. |
| `dopemux audit` (+ top-level `dopemux wizard` alias `cli.py:3317`, and `rte wizard` `cli.py:5718`) | `src/dopemux/commands/audit_commands.py:16` (`audit`), `prescan` :29 (wraps `scripts/doc_audit_prescan.py`), `wizard` :79 (→ `src/dopemux/ux/wizard/runner.py:WizardRunner`), `status` :123 | visible | `audit status` is a *third* status implementation (reads `extraction/repo-truth-extractor/v5/latest_run_id.txt` directly) distinct from `rte status` (delegates `--status` to the v5 runner). |
| `dopemux extract truth-run` | `src/dopemux/commands/extract_commands.py:876` | **hidden** AND hard-disabled: raises `ClickException("Legacy command disabled. Use `dopemux rte run`…")` at :998 before any work | ~380 lines of unreachable code (:1002–1233) remain after the `raise`, including the entire v3→v5 migration path (`--import-v3`), hygiene scan, and `_build_truth_run_command`. |

Other legacy shims: `dopemux repscan` (hidden `LegacyReplacementCommand`, `cli.py:4887` → points at `dopemux rte scan`), `dopemux truth` (`cli.py:5665`, unconditional block with good replacement text), `dopemux extractor` (real group hidden at `cli.py:3266`, then **shadowed** by a `LegacyReplacementCommand` named `extractor` at `cli.py:3268–3282` — the last `add_command` wins, so `extractor prescan/init/validate` are only reachable indirectly via `rte promptset sync|validate`, grafted at `cli.py:5737–5740`).

### 1.2 Per-surface command exposure

| Command | `rte` | `upgrades` | `audit`/`wizard` | `extract` | Defined at |
|---|---|---|---|---|---|
| scan | ✅ (gated `--allow-legacy-v3-scan`) | ❌ | ❌ | ❌ | `cli.py:5034` |
| list | ✅ | ✅ | ❌ | ❌ | `cli.py:5103` |
| run | ✅ | ✅ | (wizard Stage 7 shells out to `upgrades run`) | truth-run blocked | `cli.py:5136` |
| doctor | ✅ | ✅ | ❌ | ❌ | `cli.py:5373` |
| status | ✅ | ✅ | ✅ (independent impl) | ❌ | `cli.py:5412` / `audit_commands.py:123` |
| preflight | ✅ | ✅ | ❌ | ❌ | `cli.py:5438` |
| validate-live | ✅ | ✅ | ❌ | ❌ | `cli.py:5480` |
| trace | ✅ | ✅ | ❌ | ❌ | `cli.py:5642` |
| wizard | ✅ (shared object) | ❌ | ✅ (+ top-level `dopemux wizard`) | ❌ | `audit_commands.py:79` |
| promptset audit | ✅ | ✅ | ❌ | ❌ | `cli.py:5610` |
| promptset sync / validate | ✅ only | ❌ | ❌ | ❌ | grafts of hidden `extractor.commands["init"/"validate"]`, `cli.py:5737–5740` |

**Asymmetries** (MED): `upgrades` lacks `scan`, `wizard`, `promptset sync/validate`; `rte` is the only complete surface — good — but since the definitions live on `upgrades`, any new `@upgrades.command` silently widens the "legacy" surface first.

### 1.3 Definition-site inversion design (rte-canonical, upgrades hidden alias)

Concrete moves, all inside `cli.py` (plus one wizard file):

1. **Move the `rte` group definition** (`cli.py:5028`) above `cli.py:5103` if not already (it is — no move needed).
2. **Rename decorators**: `@upgrades.command("list"|"run"|"doctor"|"status"|"preflight"|"validate-live"|"trace")` → `@rte.command(...)` (7 sites: 5103, 5136, 5373, 5412, 5438, 5480, 5642); `@upgrades.group("promptset")`/`@upgrades_promptset_group.command("audit")` (5604/5610) → define `audit` on the existing `rte_promptset_group` (5730) and delete the duplicate `upgrades_promptset_group`.
3. **Delete** the explicit `rte.add_command(...)` block (5711–5717) — it becomes redundant.
4. **Alias back**: after the definitions, `for name in ("list","run","doctor","status","preflight","validate-live","trace"): upgrades.add_command(rte.commands[name], name)`; `upgrades.add_command(rte_promptset_group, "promptset")`. Click `Command` objects have no parent pointer — multi-group registration is safe and already exercised today (same objects live in `rte`, `upgrades`, and `extractor` simultaneously).
5. **Hide + deprecate**: `upgrades.hidden = True` next to the help overwrite at `cli.py:3260`; add a deprecation warning in the `upgrades` group callback (`upgrades_commands.py:22`) — group callbacks are per-group, so the warning cannot leak into `rte` invocations even though the leaf `Command` objects are shared.
6. **Update the wizard**: `src/dopemux/ux/wizard/extraction.py:32` builds `python -m dopemux.cli upgrades run …` — change to `rte run` (and fix the educational text at :90). If step 5 keeps the alias live this is not breaking, but the canonical surface must not depend on the deprecated one.
7. **Sweep tests/docs** for `upgrades` invocations (R4 worklist, §3).

**Behavior traps**:
- **Shared option decorator** `_pipeline_version_options` (`cli.py:4976`) creates *new* `click.Option` instances per command — no shared-state trap. Safe.
- **Group-level defaults**: neither group has callback params or `context_settings`; no default inheritance to preserve.
- **`upgrades list` v4 special-case** (`cli.py:5115–5132`) reads `promptsets/v4/promptset.yaml` relative to `_resolve_extractor_repo_root(Path.cwd())` — behavior travels with the command object, unchanged.
- **`extractor` shadowing**: `rte promptset sync|validate` reach into the *hidden real* `extractor` group's commands (`cli.py:5737`). Inversion must not delete the `extractor` import even though the top-level name is shadowed by the refusal shim.
- **`_add_extractor_alias_if_missing`** (`cli.py:5706`) appears to have no call sites — dead helper; delete during inversion (LOW).
- **Import-order**: `upgrades` is imported at `cli.py:3257`, `rte` defined at 5028, decorators at 5103+ — module executes top-to-bottom in one file, so renaming decorators needs no reordering.

---

## 2. First-run journey walk

Walked `docs/01-tutorials/extraction-quickstart.md`, `docs/02-how-to/extraction-wizard.md`, `docs/03-reference/extraction-wizard.md` against current code.

### 2.1 Findings — docs vs CLI

| ID | Sev | Finding |
|---|---|---|
| J-1 | **CRIT** | Quickstart Step "What's Next" and Troubleshooting tell users to run `dopemux extract truth-run --phase D` / "re-run with `--resume` flag on truth-run" (`extraction-quickstart.md:165,176`). `truth-run` is hidden and unconditionally raises "Legacy command disabled" (`extract_commands.py:876,998`). First-run user hits a wall following the official tutorial. |
| J-2 | **HIGH** | Entire first-run journey is taught on the non-canonical `dopemux audit wizard` / `dopemux audit prescan` / `dopemux audit status` surface; `dopemux rte` never appears in the tutorial. New users learn the wrong namespace on day one. |
| J-3 | **HIGH** | Quickstart never mentions `DPMX_LIVE_OK=1`. It says `dopemux audit wizard --execute --routing-policy balanced_openrouter` "will show estimated cost … ask confirmation" (`extraction-quickstart.md:127–137`), but live phase execution also requires `DPMX_LIVE_OK=1` (how-to gets this right at `extraction-wizard.md:40,115–117`). A user following only the tutorial gets a consent-gate failure with no foreshadowing — scary surprise at the moment of maximum commitment. |
| J-4 | **HIGH** | Quickstart cost table (`extraction-quickstart.md:89–94`) labels `balanced_openrouter` as "(default)". The wizard's actual default is `cost` (`audit_commands.py:92`); `balanced_openrouter` is the default only for `rte run` v5 (`cli.py:4973,5292`). Cross-surface default confusion documented as fact. |
| J-5 | **MED** | Quickstart Step 1 (`dopemux audit prescan`) runs `scripts/doc_audit_prescan.py` writing to `extraction/prescan/` — a *different* prescan engine than wizard Stage 2, which runs the integrated v5 prescan (`ux/wizard/corpus.py:63–82`) writing under `extraction/repo-truth-extractor/v5/runs/<RUN_ID>/prescan`. Tutorial says the wizard "re-runs the prescan" (`extraction-quickstart.md:85`) — false equivalence; Step 1's artifacts are never consumed by the wizard. |
| J-6 | **MED** | Quickstart suggests `--workers 5` / `--workers 15` (`:143,149`); how-to says keep `--workers 1` for deterministic first runs. No wall-time expectations anywhere in the tutorial (a full 14-phase live run is hours, not minutes) — surprise factor. |
| J-7 | **LOW** | How-to says "The 8 Stages" then correctly notes "nine numbered stages" 0–8 (`extraction-wizard.md:56–58`); quickstart says "8 stages" and lists only 8, omitting Stage 4 Provider Overrides (`extraction-quickstart.md:81–98`). Off-by-one branding throughout. |

### 2.2 Wizard flow audit (`src/dopemux/ux/wizard/`)

9 stages (0–8), preview-default. `runner.py:52–96` executes linearly, aborts on first FAILED stage, always re-renders summary if stage ≥2 was reached.

| ID | Sev | Finding |
|---|---|---|
| W-1 | **CRIT** | **Execute-mode phase commands are built with a nonexistent flag.** `extraction.py:48–49` appends `--prescan-dir <dir> --skip-prescan` to `dopemux upgrades run`. `upgrades run` (`cli.py:5136–5228`) has `--skip-prescan` and `--prescan-import-dir` but **no `--prescan-dir`**, and no `ignore_unknown_options` context settings — Click will reject every phase invocation with "No such option: --prescan-dir" whenever Stage 2 succeeded (it always sets `state.prescan_dir`, `corpus.py:133`). Net: wizard `--execute` is statically broken for all 14 phases. (The v5 runner itself has `--prescan-dir` at `run_extraction_v5.py:22782` — the wrapper simply never forwards it.) Fix: use `--prescan-import-dir` or add `--prescan-dir` passthrough to `rte run`. NOT_RUN caveat: verified by option-list inspection, not execution. |
| W-2 | **HIGH** | Wizard never sets or checks `DPMX_LIVE_OK`; it forwards the ambient env (`extraction.py:146–150`). With `--execute` but no `DPMX_LIVE_OK=1`, all phases will fail at the runner's consent gate *after* the operator has answered 14 confirmation prompts. The wizard should preflight the consent posture in Stage 0. |
| W-3 | **MED** | `audit wizard --routing-policy` is free-text (`audit_commands.py:90–95`, no `click.Choice`), while `rte run` validates against 8 choices (`cli.py:4962–4971`). A typo (`--routing-policy qualty`) survives until subprocess failure deep in Stage 7. Stage 5 can silently correct it only if the user interacts with the picker. |
| W-4 | **LOW** | Dead conditional: `preflight.py:47` — `StageStatus.COMPLETED if all_ok else StageStatus.COMPLETED`. Stage 0 can never report the warning state it computes. |
| W-5 | **LOW** | Dead code: `preflight.py:123` filters failures to `l == "Repository root"`, but both repo-root failure paths already early-returned (:69, :72). The filter can never match. |
| W-6 | **LOW** | Stage-numbering drift in module docstrings: `extraction.py:1` says "Stage 6", `cost_profiles.py:1` says "Stage 4" — both off-by-one vs `runner.py` (Extraction=7, Cost Profile=5). Cosmetic but confuses maintainers. |
| W-7 | **MED** | No dead stages found; all 9 stage functions are real and wired. However Stage 7 in preview mode returns SKIPPED after printing the static phase list — the "estimated cost before proceeding" promised by the quickstart (`:135`) lives in Stage 5 (`cost_profiles.py:335–336`, `estimate_cost`) using static per-policy ladders (`ROUTING_LADDERS`, `cost_profiles.py:20`); these are hand-maintained and not derived from the v5 pricing surface (`lib/pricing_surface.py`) — estimate drift risk. |
| W-8 | **MED** | Wizard reflects the 14-phase list (`stages.py:56`) including S, but `rte scan`/repscan phase choices (`cli.py:5040`) list only 14 minus S (A…Z, no S). Profiles/flags surface current v5 policy names correctly (8 policies match `_ROUTING_POLICY_CHOICES`). |

---

## 3. Docs sweep inventory (`dopemux upgrades` mentions)

Grep at HEAD: **41 files, 87 mentions** under `docs/`. Classification (R4 worklist):

### 3.1 needs-rewrite-to-rte (active docs presenting `upgrades` as an executable path) — 8 files

| File | Mentions | Action for R4 |
|---|---|---|
| `docs/03-reference/extraction/pipeline-phases.md` | 2 (`:46,:50` — runnable `dopemux upgrades run …` examples) | Replace with `dopemux rte run …` |
| `docs/03-reference/extraction/doctor-reprocess.md` | 1 (`:26` runnable `dopemux upgrades doctor …`) | Replace with `dopemux rte doctor` |
| `docs/03-reference/extraction-wizard.md` | 1 (`:197` — describes wizard delegation) | Rewrite to `rte run` **after** W-1 fix lands (keep in lockstep with `extraction.py`) |
| `docs/02-how-to/extraction-wizard.md` | 1 (`:128` — same delegation text) | Same as above |
| `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md` | 5 | Rewrite command examples to `rte` |
| `docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md` | 4 | Rewrite examples; keep one alias note |
| `docs/04-explanation/architecture/dopemux-architecture.md` | 1 | Rewrite |
| `docs/03-reference/governance/docs-vs-repo-diff.md` | 1 | Rewrite (or mark as diff-artifact if it is quoting repo state — UNKNOWN, verify during R4) |

### 3.2 legitimate-alias-notes (already canonical: mention `upgrades` only to say it is the legacy alias) — 4 files, keep as-is

- `docs/02-how-to/extraction/batch-quickstart.md:24`
- `docs/02-how-to/extraction/repo-truth-extractor-user-guide.md:23`
- `docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:20`
- `docs/03-reference/extraction/pipeline-reliability.md:31`

(After the §1.3 inversion + hiding, optionally reword "legacy compatibility alias" → "hidden deprecated alias".)

### 3.3 legitimate-historical (ADRs, audit reports, archives — do NOT rewrite) — 18 files

- ADRs: `docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint{,-2,-3}.md` (4 each ×3), `adr-218-repo-truth-extractor-hard-cutover-namespace{,-2,-3}.md` (1 each ×3). *Note: triplicated ADR files are themselves a hygiene smell — flag to R4 as dedupe-candidates, but content stays historical.*
- Audit reports: `docs/05-audit-reports/rte-canonical-entrypoint-implementation-2026-04-23.md` (3), `rte-production-certification-audit-20260414.md` (4); `docs/audit/rte-opus-uiux-claude-design-audit/{recommendations,findings-ledger,ux-risk-ledger,claude-design-compatibility}.md` + `FINDINGS_LEDGER.json` (11 total).
- Archives: `docs/archive/claudedocs/audit-2026-05-22/operator-quickstart.md` (1), `docs/archive/root-relocated/user-journey.md` (1), `docs/archive/unclassified-top-level/repo-truth/truth-{canonicals,interfaces}.md` (7).

### 3.4 regenerate-not-edit (generated truth/constraint snapshots) — 10 files

`docs/03-reference/truth/truth-{canonicals(2),data-events(1),gaps(2),interfaces(3),scope(1),systems(2)}.md` (11 mentions) and `docs/research/mcp-customization/dopemux-constraints/{SYSTEM_RepoTruthExtractor(5),TRUTH_INTERFACES(3),TRUTH_CANONICALS(1),TRUTH_DATA_EVENTS(1),ARCHITECTURE(1)}.md`. These are RTE output snapshots; hand-editing forks them from their generator. R4 action: **do not hand-rewrite** — refresh via a new extraction run post-inversion, or annotate as stale snapshots. (Whether `docs/03-reference/truth/` is currently hand-maintained: UNKNOWN — verify frontmatter/provenance during R4.)

### 3.5 delete-candidates — 1 file

- `docs/04-explanation/root-relocated/user-journey.md` (1) — duplicate of the archived copy in `docs/archive/root-relocated/user-journey.md`; UNKNOWN which is canonical — R4 to pick one and delete the other.

**R4 execution order**: 3.1 rows (8 files, mechanical `upgrades`→`rte` in runnable examples) → 3.2 rewording (optional) → 3.5 dedupe → 3.4 regeneration decision. Estimated ~20 mention-edits total; the other ~67 mentions are correctly left alone.

---

## 4. v5-native scan spec

### 4.1 What `run_repscan.py` (512L) actually does

1. **Consent gate**: refuses without `--allow-legacy-v3-scan` (`run_repscan.py:329–330`, message :73–77). Mirrored by the Click wrapper (`cli.py:5078–5084`), which forwards the flag (defense in depth, :5085–5098).
2. **Stage 0/1 scanning** (`_scan_and_classify`, :256–279): `build_stage0_artifacts` (`lib/promptgen/fingerprint.py:339`) — repo fingerprint, build surface, entrypoint candidates, dependency-graph hints, honoring `--promptgen-max-files/include-globs/exclude-globs`.
3. **Archetype classification**: `classify_archetypes` (`lib/promptgen/archetype_classify.py`) → `ARCHETYPES.json`.
4. **Deterministic profile selection**: `select_profile` (`lib/promptgen/profile_select.py`) against `lib/promptgen/profiles/` → `PROFILE_SELECTION.json`.
5. **PromptPack v1 compile / v2 adjust** (`compile_promptpack_v1`, `adjust_promptpack_v2`; v2 requires an existing `COVERAGE_REPORT.json` + `*_QA.json` from a prior run, :410–425), `--promptgen auto` post-run v2 suggestion (:485–508), fingerprint receipt `RUN_PROMPTPACK_FINGERPRINT.json` (:191–223), phase contract map (:341).
6. **Delegation to v3**: runs `run_extraction_v3.py` with `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` env override (:236–248, :475–481). Writes into `extraction/repo-truth-extractor/v3/runs/`.

### 4.2 What v5 already covers

- **Scanning/classification**: v5's **integrated Stage-0 prescan** (`run_extraction_v5.py:8111–8220` `run_integrated_prescan_stage`; engine `lib/prescan/engine.py`, 801L, with corpus_walker, classifier, duplicate_detector, cost_estimator, dependency_graph, code_prescan, git_enricher, batch_planner, token_counter) — strictly richer than repscan's Stage 0/1. Already runs inside every `rte run` (skippable via `--skip-prescan`, importable via `--prescan-import-dir` with staleness validation :8223–8259). The wizard already drives it standalone in-process (`ux/wizard/corpus.py:63–82`).
- **Prompt resolution**: v5 consumes *promptsets* (`rte_promptset.prompt_root`, `run_extraction_v5.py:22772–22800` `--promptset-root`), not PromptPack v1/v2. `grep archetype run_extraction_v5.py` = 0 hits — archetype/profile/PromptPack are **v3-contract-only** concepts; their remaining consumers are `run_repscan.py` and tests. Promptset generation/validation already has a surface: `rte promptset sync|validate` (grafted `extractor init`/`validate`, `cli.py:5737–5740`) built on `lib/promptgen/{scope_resolver,sync_engine,contract_generator,template_renderer}`.

**Gap analysis**: the only repscan capability with no v5 equivalent is PromptPack v1/v2 generation — and v5 cannot consume PromptPacks anyway. Nothing worth porting except "run the scan standalone".

### 4.3 Recommendation: **(a) v5-native `rte scan`** — a standalone prescan producer

Rejecting (b) (absorb into `rte run` presets): the prescan already *is* inside `rte run`; absorbing "scan" adds nothing there, and it would leave no way to (i) produce/inspect prescan intelligence offline before committing to a run, (ii) generate importable artifacts for `--prescan-import-dir` (the existing wiring designed for exactly this), (iii) scan without creating run-shaped state. The operator value of "scan" is *read-only reconnaissance*; folding it into `run` destroys that.

**Spec — `dopemux rte scan` (v5-native)**:

- **Semantics**: offline, deterministic, zero-LLM by default. Runs `lib/prescan.engine.PrescanEngine` (same call path as `run_integrated_prescan_stage`) against the repo, writing canonical prescan artifacts. No consent gate needed for the default lane (no spend). Removes `--allow-legacy-v3-scan`, the repscan delegation, and drops PromptPack v1/v2 (retire with v3; keep `run_repscan.py` untouched in the v3 graveyard lane).
- **Flags**:
  - `--run-id TEXT` (default timestamp) — artifact directory naming.
  - `--out PATH` (default `extraction/repo-truth-extractor/v5/runs/<RUN_ID>/prescan`) — allows scanning into a portable directory for later `rte run --prescan-import-dir`.
  - `--max-files INT`, `--include-glob` / `--exclude-glob` (repeatable) — map to `lib/prescan/models.PrescanConfig`.
  - `--online` + `--allow-online-llm` (both required together, plus `DPMX_LIVE_OK=1`) — authorizes the optional Grok/LLM prescan passes (`prescan_online`), keeping the existing v5 consent posture.
  - `--allow-scope-reduction` — maps `prescan_allow_scope_reduction`.
  - `--json` — machine-readable summary to stdout.
- **Outputs**: `corpus_manifest.json`, `prescan_intelligence.json`, `batch_plan.json`, `prescan_routing_plan.json`, `prescan_provider_readiness.json`, receipt (`prescan_stage_receipt.json`) — identical contract to integrated Stage 0, so `rte run --prescan-import-dir <out> --skip-prescan` consumes it with the existing staleness validation. Human summary: authority-class table + top-N cost estimate reusing the wizard's render helpers (`ux/wizard/display.py`).
- **Wiring**: implement in `src/dopemux/commands/` (post-inversion, defined on `rte`), in-process import of the v5 runner module exactly as `ux/wizard/corpus.py:_load_v5_runner_module` does today (no subprocess); then refactor wizard Stage 2 to call the same helper (one prescan code path for wizard + CLI). Print the follow-on command (`dopemux rte run --prescan-import-dir … --skip-prescan --dry-run`) on success — ADHD-friendly next step.
- **Retirement**: `rte scan --allow-legacy-v3-scan` path deleted; hidden `repscan` shim retargeted text stays; `run_repscan.py` remains only as v3-lane archaeology.

---

## 5. Help/UX defect ledger

| ID | Sev | Defect |
|---|---|---|
| U-1 | **CRIT** | (= W-1) Wizard→`upgrades run` uses nonexistent `--prescan-dir`; execute lane statically broken. `ux/wizard/extraction.py:49` vs `cli.py:5224–5227`. |
| U-2 | **HIGH** | Canonical/alias inversion: all core commands defined on `upgrades` (unhidden), `rte` is the attach-site alias (§1). `upgrades` group help in `upgrades_commands.py:22` still says "Ritual Advancement: Universal Repo-Truth-Extractor commands" and is only papered over by the reassignment at `cli.py:3258` — anything importing the group before `cli.py` runs sees the wrong story. |
| U-3 | **HIGH** | Worker-flag inconsistency: `audit wizard --workers/-w` default **1** (`audit_commands.py:97`); `rte run --partition-workers` default **1** (`cli.py:5150`); dead `extract truth-run --workers/-w` default **10** (`extract_commands.py:889`); blocked `truth --workers` default 1 (`cli.py:5674`). Same concept, three names, two defaults. Standardize on `--workers/-w` with `--partition-workers` kept as hidden alias. |
| U-4 | **HIGH** | Routing-policy divergence: `rte run` Choice of 8, default `balanced_openrouter` (v5) / `cost` (legacy) resolved dynamically (`cli.py:4962–4973,5292–5296`); `audit wizard` free-text default `cost` (`audit_commands.py:90`); blocked `truth` Choice of only 4 (`cli.py:5679`); wizard static `ROUTING_LADDERS`/`estimate_cost` (`ux/wizard/cost_profiles.py`) hand-maintained separately from the runner's pricing surface — estimates can silently drift from real routing. |
| U-5 | **MED** | Three uncoordinated `status` implementations: `rte status` (runner `--status`), `audit status` (reads `latest_run_id.txt` + dir sizes, `audit_commands.py:123–159`), and `extractor status` (hidden). Different output, different failure modes; `audit status` silently ignores `--run-id` (doesn't accept one). |
| U-6 | **MED** | `rte trace` (`cli.py:5642–5662`): `--dry-run` is an `is_flag` with `default=True` — a flag that is always on and cannot be negated except by `--execute`; help text doesn't say `--execute` performs live LLM calls under the same consent posture. Also duplicates `rte run --dry-run` semantics; deprecation candidate. |
| U-7 | **MED** | `rte promptset audit` raises "Promptset audit is implemented for v4 only" (`cli.py:5639`) — accurate but a dead end: no pointer to what to do for v5 (`rte promptset validate`). `rte list` silently changes behavior for v4 (runs a promptset audit first, `cli.py:5115–5132`) with no help-text mention. |
| U-8 | **MED** | `rte scan` phase choices omit `S` (`cli.py:5041`) while wizard/`rte run` treat S as a real phase (`ux/wizard/stages.py:56`); inherited from v3 phase set — confusing until scan is replaced (§4). |
| U-9 | **LOW** | Hidden `--engine-version` legacy alias (`cli.py:4977–4983`) still routes to v3 with only a warning (`cli.py:5001–5006`) — intended, but the warning is the only guard; consider requiring `--allow-legacy-v3` parity. |
| U-10 | **LOW** | Error-message quality on blocked surfaces is generally good (`truth` :5697–5703 lists exact replacements; `LegacyReplacementCommand` :96–100 maps subcommand→replacement). Weak spot: `repscan --help` prints only "Legacy command disabled. Use `dopemux rte scan` instead." (`cli.py:82–85`) while `rte scan` is *itself* blocked by default — the referral chain ends in a second refusal (until §4 lands). Missing-keys errors surface only from the runner subprocess (`_run_extractor_runner` wraps as generic "runner failed with exit code N", `extractor_commands.py:498–501`) — exit-code laundering hides the actionable stderr line for bad run-id / missing keys. |
| U-11 | **LOW** | ~380 lines of unreachable code after the `raise` in `truth_run` (`extract_commands.py:1002–1382` incl. `_build_truth_run_command`, `_find_runner`) — delete or extract the v3→v5 import logic if still wanted. |

---

## Validation

- **PASS**: static cross-checks (option lists vs wizard command builder; docs grep counts 41 files / 87 mentions reproduced twice; definition sites confirmed by line).
- **NOT_RUN**: live `--help` render, wizard execution, any runner invocation (harness classifier outage mid-audit; W-1/U-1 confirmed by option-declaration inspection only — residual risk: an unseen Click passthrough could soften it, but `upgrades run` declares no `ignore_unknown_options`).
- **UNKNOWN**: provenance of `docs/03-reference/truth/*` (hand-maintained vs generated) — R4 to verify; canonical copy of `user-journey.md` pair (§3.5); whether `docs-vs-repo-diff.md` quotes repo state or prescribes commands.
