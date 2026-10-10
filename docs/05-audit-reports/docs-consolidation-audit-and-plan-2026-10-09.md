---
id: docs-consolidation-audit-and-plan-2026-10-09
title: Documentation Consolidation Audit and Plan (2026-10-09)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-10-09'
last_review: '2026-10-09'
next_review: '2027-01-09'
prelude: Whole-repository documentation audit with measured baseline and an eight-wave consolidation, removal, and reorganization plan. Deterministic acceptance checks per wave; no repo mutation performed by the audit itself.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Audit complete, plan awaiting operator authorization

# Documentation Consolidation Audit and Plan

**Operator rule (2026-10-10)**: nothing leaves the repository. Archived and out-of-date material is needed for archaeology, so no file is deleted or exported. "Remove", "retire", and "move out" below always mean a `git mv` into `docs/archive/<wave>/<original path>` with a manifest row, so the active tree gets clean while every byte stays tracked and searchable in this repo. Deletion and external export are deferred decisions, recorded in the manifest as candidates only.

**Authority**: this is an audit report and proposal. It mutates nothing. Every wave below needs its own Task Packet and, where marked, explicit operator authority ([AGENTS.md](../../AGENTS.md) §5, §9). Runtime code, schemas, and `proof/` outrank anything here.

**Baseline artifacts** (deterministic, regenerable):
- `reports/docs-hygiene/consolidation-baseline-2026-10-09.json` — tracked-markdown census, 1,147 exact-duplicate groups, 2,435 broken relative links (code fences skipped).
- `reports/docs-hygiene/suffix-variants-2026-10-09.json` — classification of the 328 `name-N.md` variant files.

## 1. Headline findings

| Metric | Baseline | Target after plan | Achieved 2026-10-10 (branch `docs/consolidation-w0-w1`) |
|---|---|---|---|
| Git-tracked `*.md` files (whole repo) | 7,897 | 7,897 (nothing deleted or exported; files move within the repo) | 7,898 (plus this plan); nothing deleted |
| Active docs outside `docs/archive/` | 1,678 | ≈ 1,000 (W3 −300; W4 −275; W6 −110 all relocated into `docs/archive/`) | 1,155 |
| `docs/archive/` files | 2,163 (plus 694 quarantined under `04-explanation/history/`) | ≈ 3,550 in one tree, manifest-indexed, frozen | 3,456 files, 3,455 manifest rows (2,035 `keep`, 1,420 `delete-later` candidates), frozen by hook |
| `docs/` tracked files, all types | 4,539 md / 143 MB | 4,539 md / ≈ 55 MB (evidence blobs move to `reports/`, nothing else leaves `docs/`) | 4,483 md / 89 MB (the 43 MB duplicate evidence copy stays in the archive by rule) |
| `docs/` top-level directories | 33 | 13 after W7 (Diataxis 01–06, 90–92, `archive`, plus pinned `ops`, `pr_prep`, `pr_merge`; 14 while `planes/` awaits its rename) | 14 directories: the 13 planned plus `94-architecture` (kept) and `instructions/` holding one tracked YAML; `planes/` rename completed |
| Exact byte-duplicate groups (repo-wide md) | 1,147 (2,007 redundant copies) | 0 in the active tree; archive duplicates listed in the manifest as candidates | 35 in the active tree, all explained: 19 test-pinned `pr_prep`/`pr_merge` compat copies, 10 inside the `06-research/mcp-customization` data pack, 5 ADR variant pairs left for the ADR owner |
| `name-N.md` suffix variants in active docs | 328 | 0 | 4 (the `adr-201`/`adr-202` pairs, deferred to the ADR owner); `pr_prep`/`pr_merge` excluded as pinned |
| Broken relative links (repo-wide md) | 2,435 | < 50 outside `docs/archive/`; archive links stay as-is and stay gate-excluded | 116 in active docs plus root markdown (108 point at targets that exist nowhere in the repo, 8 ambiguous); list in `reports/docs-hygiene/w7-broken-links-2026-10-10.json` |
| Active docs with `next_review` overdue | ≈ 95 % | field retired or cadence enforced | unchanged; decision recorded in W7: keep the field, no CI cadence (see below) |
| Docs gate coverage (pre-commit + CI) | advisory only, 63 % of `docs/` excluded | blocking, 100 % of the active tree; `docs/archive/` is the single declared exclusion | graph validator re-enabled in CI with 0 errors over 1,155 active docs; `docs/archive/` is the only docs exclusion in pre-commit; lychee excludes shrunk to archive and evidence roots but still `fail: false` because 116 pre-existing broken links remain |

The three structural problems, in order of leverage:

1. **Quarantining the dead weight in one place is the lever, not reorganization.** `docs/archive/` (2,163 files) plus `docs/04-explanation/history/sourceFiles/` (694 files, 686 without frontmatter) are 63 % of `docs/`. They hold 982 + 315 of the redundant copies and 2,269 of the 2,435 broken links. The 700-file history dump was added in one commit (`71f60c601`, "assemble MCP customization deep research data packs") as LLM research input, not documentation. All gates exclude both trees, so they are invisible to CI and will keep rotting. Because they are wanted for archaeology, the fix is one consolidated, frozen, manifest-indexed `docs/archive/` that search and indexers skip, not removal.
2. **The placement policy legitimised the sprawl.** `config/docs_hygiene/docs_placement_policy.yaml` lists 31 `canonical_roots`, including `planes`, `systems`, `arbitration`, `flight_deck`, `pr_prep`, `governance`, `policy`, and 13 directories untouched since the 2026-05-01 hygiene PRs. `scripts/lint-docs.sh` therefore reports all-green on a tree with 33 top-level directories. Unless the policy is tightened first, every later wave regresses on the next PR.
3. **Evidence blobs live inside `docs/`.** `docs/planes/pm/_evidence/` (113 `.txt` + 25 `.md`, 44 MB) is byte-duplicated into `docs/03-reference/planes/pm/_evidence/` (43 MB). Those two copies are 61 % of the bytes in `docs/`. Evidence belongs under `proof/`, `reports/`, or `out/` per the filesystem guide, never in the Diataxis tree.

## 2. Measured baseline

### 2.1 Where the markdown is

| Location | Tracked md | Last commit | Observation |
|---|---|---|---|
| `docs/archive/` | 2,163 | 2026-10-03 | 982 redundant copies, 1,175 broken links, 2,160 overdue reviews. `pipeline-v2/UPGRADE` and `UPGRADE_legacy` hold six-way identical copies. |
| `docs/04-explanation/history/` | 700 | 2026-05-01 | 694 quarantined source files, 1,094 broken links, 315 internal duplicates. Marker file `.QUARANTINED.md` present. |
| `docs/03-reference/` | 643 | 2026-10-03 | Live, but contains parallel trees (`governance/` 40, `planes/` 56, `systems/` 103) and 57 broken links. |
| `docs/planes/` | 148 md + 113 txt | 2026-08-24 | 147 of 148 under `pm/`; 103 redundant copies; evidence duplicated into `03-reference/planes/`. |
| `docs/90-adr/` | 125 | 2026-09-04 | 52 suffix variants; 40 redundant copies. |
| `docs/systems/` | 73 | 2026-06-22 | 58 basenames also exist in `03-reference/systems/`. |
| `docs/02-how-to/`, `01-tutorials/`, `06-research/`, `05-audit-reports/` | 93 / 23 / 84 / 36 | 2026-10-03 / 10-03 / 07-16 / 07-16 | Live Diataxis sections. |
| 13 parallel dirs: `arbitration`, `flight_deck`, `governance`, `integrations`, `learning`, `mobile`, `packaging`, `policy`, `pr_template`, `releases`, `rollout`, `skills`, `ux` | 142 | 2026-05-01 (bulk import `71f60c601`, 12,165 files; content authored 2026-03) | Every file has a byte-identical or newer twin inside a Diataxis section; zero live referrers except `docs/ux/` (three scripts/personas). |
| `docs/pr_prep/` (47), `docs/pr_merge/` (9) | 56 | 2026-08-13 / 08-23 | Declared compatibility stubs; pinned by `tests/governance/test_pr_prep_contract_v2.py`. |
| `docs/ops/` (33) | 33 | 2026-09-09 | Live; `AGENTS.md:196` and `scripts/governance/validate_change_contract.py` regex pin the path. |
| Repo root | 22 | mixed | 5 maintained public-surface files + 4 tool-required; 13 analyses/inventories. `config/repo_hygiene/root_hygiene_policy.json` is enforced by the `root-hygiene` pre-commit hook, but its allowlist (118 files, 65 dirs) admits every current root file, so the gate cannot fail. |
| `proof/`, `proofs/`, `out/proofs/` | 981 / 15 / — | 2026-10-08 | Governed evidence roots (`src/dopemux/governed_execution/audit_identity/location.py:22` lists `proof/`, `proofs/`, `out/`, `reports/`). Frozen. |
| `extraction/` | 419 | 2026-05-01 | `extraction/v4/runs/` holds 1,276 tracked files incl. a 26-way duplicated test run; `.gitignore:395` already ignores `extraction/v*/`, so they are tracked only because they were added before the rule. `v5/proofs/**` is governed; keep. |
| `out/` | 310 | 2026-06-04 | Mixed: `out/proofs/` is governed; `cockpit-*`, `chatgpt-project-upload-set` (56), `rte-*` packs are legacy or generated. Hygiene policy classes `out/**` as temp, which conflicts with `out/proofs/`. |
| `reports/` | 215 | 2026-10-02 | `work-recovery/` 108 files (March snapshot, 13 MB) is legacy; `leantime-repo-truth-pack/` and `task-orchestratorrepo-truth-pack/` (typo in name) mirror `repo-truth-pack/`. |
| `claudedocs/` | 112 | 2026-09-11 | 70 loose files at its root; three are named in script comments or log text, one by `.control-tower` route record. |
| `llm-plans/` (29), `prompts/` (9), `runbooks/` (3), `UPGRADES/` (17), `tools/prompt_rewrite_v4/` (105), `repo-truth-pack/` (44), `contracts/` (6) | 213 | 2026-05 to 2026-08 | Living docs outside `docs/` (prompts, runbooks, contracts), or legacy harness output (v4 rewrite, UPGRADES) guarded by pre-commit lines 225–248 and `validate_change_contract.py`. |
| `services/`, `tools/`, `docker/`, `templates/`, `src/`, `tests/` | 378 / 107 / 70 / 25 / 29 / 15 | live | Package-local docs; keep in place. |
| Three runbook homes | `runbooks/` 3, `docs/runbooks/` 1, `docs/92-runbooks/` 4 | — | One canonical home required. |

Not counted above and out of scope: 25,636 markdown files inside gitignored `.claude/worktrees/` (three stale worktrees; clean with the worktree tooling, not a docs task), and 70 untracked files under `.agents/` plus `.codex/hooks/` currently sitting on `main`.

### 2.2 Duplication

- 1,147 exact-duplicate groups across tracked markdown; 2,007 files are redundant copies. By location: `docs/archive` 982, `docs/04-explanation` 259, `extraction/v4` 212, `docs/planes` 103, `docs/systems` 60, `docs/90-adr` 40, `docs/arbitration` 38, `docs/03-reference` 34, `out/` 26, `.github/skills` 25, `templates/skills` 24, `proof/pr_merge` 22, `src/dopemux` 16.
- `name-N.md` variants in active docs (archive excluded): 328. Classified by diffing with frontmatter stripped: 162 differ only in frontmatter (safe mechanical removal), 38 near-identical (> 90 % line overlap; adjudicate), 15 substantively different (adjudicate), 113 have no base file (rename to drop the suffix). Full list in `suffix-variants-2026-10-09.json`.
- `.github/skills/` and `templates/skills/` are mutual copies (25 + 24 redundant files). `.claude/skills/pr-docgen-sync` is a third copy of one skill.

### 2.3 Link integrity

2,435 broken relative links after skipping fenced code. Outside the two quarantined trees the count is 166: `03-reference` 57, `planes` 46, `02-how-to` 15, `01-tutorials` 10, `90-adr` 9, `docker/mcp-servers-source` 9, remainder scattered. The `INSTALL.md` hits reported by naive scanners are false positives (shell prompt tokens inside code fences); any acceptance command must skip fences.

Live surfaces that point into `docs/archive/` or `docs/04-explanation/history/`. Archive paths do not change under this plan, so these are stale-link facts rather than a W1 fix-up list; only the `history/sourceFiles` referrers need editing when W1 moves that tree:

- `docs/00-MASTER-INDEX.md` lines 171–183 and 247–283 (the "Archive" section).
- `docs/docs_index.yaml` lines 152–155.
- Twelve active docs with 1–4 references each: `docs/03-reference/overview.md`, `documentation-catalog.md`, `doc-audit-prescan.md`, `governance/authority-map.md`, `governance/authority-map-2.md`, `governance/doc-trust-map.md`, `governance/dopemux-documentation-source-map.md`, `systems/adhd-engine/interruption-shield/quickstart.md`, `systems/dashboard/overview.md`, `systems/serena/multi-workspace-guide.md`, `systems/conport/db-project-wall-and-corpus-recovery-2026-08-02.md`, `docs/02-how-to/orchestrator-dashboard.md`, `docs/02-how-to/doc-audit-prescan.md`.
- `docs/planes/pm/dopemux/_opus_inputs/14-doc-roots-and-memory-corpus-map.md` and its `-2` twin (move with the evidence in W2 anyway).
- Four audit packs under `docs/05-audit-reports/` (`cockpit-adhd-lifestyle-feature-map`, `cockpit-archive-intent-pack`, `cockpit-design-input-merged-brief`, `rte-prelive-audit-pack`, 25 citations): point-in-time evidence; leave as-is and accept the stale links.
- `.lychee.toml` and `.pre-commit-config.yaml` exclusion lists.

References from `proof/`, `reports/`, `audit_inputs/`, and `extraction/` JSON or text blobs are historical citations inside frozen evidence and are left as-is.

### 2.4 Governance gates: what actually runs

| Gate | Scope | Status |
|---|---|---|
| `docs-frontmatter-guard` (pre-commit) | `docs/`, `task-packets/`, `UPGRADES/`, service docs | Runs; excludes `docs/archive/` and `history/sourceFiles/`. |
| `docs-graph-validator` (pre-commit) | same | **Skipped in CI** (`SKIP: docs-graph-validator`, "pre-existing validation issues"). |
| `docs-prohibited-patterns`, `docs-prelude-tokens` | same | Run; same exclusions. |
| lychee (CI `docs.yml`) | `docs/**`, `task-packets/**` | **`fail: false`** and `.lychee.toml` excludes `01-tutorials/`, `02-how-to/`, `06-research/`, `05-audit-reports/`, `systems/`, `archive/`, `technical-deep-dives/`, `README.md`. Effectively off. |
| `scripts/lint-docs.sh` | `docs/` | Zero referrers in Makefile, CI, or hooks. Manual only. |
| `make docs-audit` | `docs CCDOCS CHECKPOINT archive` | Targets directories that no longer exist; output dir gitignored. |
| `next_review` frontmatter | all | ≈ 95 % overdue in every section. Nobody runs the cadence. |
| Unreferenced docs scripts | — | `doc_gate.py`, `doc_mine.py`, `docs_titles_improve.py`, `validate_adhd_doctrine_docs.py`, `lint-docs.sh` have no callers. |
| `docs/docs_index.yaml` | — | Hand-maintained (no generator); 232 lines; checked by `check_docs_hygiene.py` only. |

### 2.5 Prior consolidation (2026-05-01)

PRs #561–#564 ran a repo-hygiene consolidation that moved files into `docs/archive/` under an explicit rule: "All moves preserve file content — nothing is deleted. Historical docs remain accessible in archive/." Its own reports were then duplicated inside the archive (`consolidation-reports/` holds each report twice or three times). This plan keeps that rule in full: nothing is destroyed or exported, and the operator has confirmed the archive is wanted for archaeology. What changes is that the archive becomes one consolidated, frozen, indexed tree that search tools skip, and that the active tree stops carrying duplicates of it. An on-disk archive that no gate checks, that is 2.3× the size of the live documentation, and that carries 48 % of the repo's broken links is not "accessible", it is noise that degrades every search, index, and embedding pass (`dope-context`, `docs_search`, `prescan`).

## 3. Do-not-touch list

These are outside every wave's write allowlist. Moving or deleting them requires separate authority:

- `proof/**` and `proofs/**` — governed evidence; `proof/CCAR-002/SOURCE_MANIFEST.json` SHA-pins `.claude/personas/` and `.claude/agents/`; the H4 hook guards proof artifacts.
- `task-packets/**`, `schemas/**`, `contracts/**`, `.control-tower/**` — contract surfaces; canonical-writer inspection required.
- `.claude/personas/**`, `.claude/agents/**`, `.claude/commands/**`, `.claude/modules/**` — pinned or hook-loaded.
- `services/*/docs/**`, `docker/*/docs/**`, `tools/**`, `src/**`, `tests/**` — package-local documentation owned by those packages.
- `AGENTS.md`, `README.md`, `QUICK_START.md`, `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, `GEMINI.md`, `CHANGELOG.md`, `INSTALL.md`, `llms.txt` — maintained public surface or tool-required.
- `audit_inputs/**`, `repo-truth-pack/**`, `out/proofs/**`, `extraction/repo-truth-extractor/v5/proofs/**` — evidence intake and proof roots cited by `proof/` bundles, `task-packets/*.json`, and `.taskorchestrator/surface_manifest.json`.
- `docs/ops/**` — path pinned by `AGENTS.md:196` and the L2 regex in `scripts/governance/validate_change_contract.py:41`.
- `docs/pr_prep/**`, `docs/pr_merge/**` — compatibility stubs asserted by `tests/governance/test_pr_prep_contract_v2.py`; retire only together with that test.
- `qa/`, `.vibe/`, `.opencode/`, `.conport/`, `.control-tower/`, `dopemux_voice_branding_bundle/` (runtime-loaded by `src/dopemux/ui/voice.py`) — tool-required.

Proof-path conventions disagree (`proof/<skill>/<domain>/<run>/` vs `proof/<skill>/<phase>/<run>/` vs `proof/<PACKET_ID>/`) and the retention rules still name `docs/governance/` as an indefinite-retention location. Both are governance defects to log, not something this plan resolves.

## 3.5 In-repo archive mechanism (applies to every wave)

- **Location**: `docs/archive/` stays the single archive root. Each wave adds a subtree `docs/archive/<wave-id>/` (for example `docs/archive/w3-parallel-trees/`) and preserves the file's original repo-relative path beneath it, so origin is readable from the path.
- **Manifest**: `docs/archive/MANIFEST.jsonl`, one row per archived file: original path, archive path, sha256, source commit, wave id, reason (`exact-duplicate-of:<path>`, `superseded-by:<path>`, `quarantined-research-input`, `point-in-time-evidence`, `obsolete`), and `disposition_candidate` (`keep`, `delete-later`, `export-later`). The last field records what a future operator decision could do; this plan never acts on it.
- **Tool**: `scripts/docs_archive_move.py` (written in W0, about 60 lines): takes a path list and a reason, runs `git mv` into the wave subtree, hashes, appends manifest rows, and refuses to overwrite an existing archive path.
- **Freeze**: the placement checker rejects any new file under `docs/archive/` that is not written by that script (manifest row required), and `unknown_top_level_fallback_dir` no longer points there.
- **Gates and indexers**: `docs/archive/` is the one declared exclusion in pre-commit, lychee, `docs_validator.py`, `dope-context` docs indexing, `doc_audit_prescan.toml`, and `docs_index.yaml`; `docs/archive/overview.md` becomes the human index and states the freeze.
- **Acceptance for every wave**: manifest rows added equals files moved; `git ls-files docs/archive | wc -l` grows by exactly that number; no file disappears from `git ls-files` overall.
- **Recovery**: `git mv` back, or `git log --follow` on the archive path.

## 4. Target layout

```
docs/
  INDEX.md                 root pointer (keep)
  00-MASTER-INDEX.md       human topology (keep, regenerate sections)
  docs_index.yaml          machine index (keep, regenerate)
  01-tutorials/
  02-how-to/
  03-reference/            incl. governance/, systems/, planes/, dcp/, pr-pipeline/ …
  04-explanation/          architecture/, design-decisions/, overview/, product/ … (history/ removed)
  05-audit-reports/
  06-research/             absorbs docs/research/ and llm-plans/
  ops/                     stays until AGENTS.md and validate_change_contract.py are repointed
  pr_prep/, pr_merge/      compatibility stubs; retire with test_pr_prep_contract_v2.py
  90-adr/
  91-rfc/
  92-runbooks/             absorbs runbooks/ and docs/runbooks/
  archive/                 single frozen archive tree with MANIFEST.jsonl (kept for archaeology)
  94-architecture/         1 file today; fold into 04-explanation/architecture/ in W3 or keep as the C4 home
```

Everything else under `docs/` either folds into one of these (W3), moves to an evidence root (W2), or moves into the consolidated `docs/archive/` (W1).

## 5. Waves

Each wave is one Task Packet and one PR. Ordering is by leverage and dependency. "Gate" marks waves that need explicit operator authority because they are destructive or touch contract surfaces.

### W0 — Tighten the gates before moving anything

- **Writes**: `scripts/docs_archive_move.py` (new), `docs/archive/MANIFEST.jsonl` (new, empty), `config/docs_hygiene/docs_placement_policy.yaml`, `config/repo_hygiene/root_hygiene_policy.json`, `.pre-commit-config.yaml`, `.lychee.toml`, `.github/workflows/docs.yml`, `Makefile` (docs targets), `scripts/lint-docs.sh`, `scripts/docs_validator.py` (allowed-path list only), `tests/scripts/test_docs_hygiene.py` and `test_docs_filename_hygiene.py` (they read the policy).
- **Actions**: cut `canonical_roots` to the target directories in §4 (`94-architecture` stays only if W3 keeps it; `docs/templates/` does not exist, the policy already maps it into `03-reference/templates/`); point `unknown_top_level_fallback_dir` away from `docs/archive/unclassified-top-level` (otherwise the hygiene script recreates the archive on the next misplaced file) to `docs/04-explanation/root-relocated/`; add `relocation_rules` for every retired directory (`03-reference/planes/`→`planes/pm/` is the one exception where the non-Diataxis tree wins, see W3; `systems/`→`03-reference/systems/`, `research/`→`06-research/`, `runbooks/`→`92-runbooks/`, `governance/`+`policy/`→`03-reference/governance/`, `arbitration/`→`03-reference/governance/arbitration/`, `flight_deck/`→`03-reference/governance/flight-deck/`, `audit/`→`05-audit-reports/`); delete the existing `map-pm` and `map-projects` rules that route new files INTO `docs/planes` and `docs/systems`; make the placement checker reject any new file under `docs/archive/` that lacks a manifest row;  shrink `allowed_root_files` in `config/repo_hygiene/root_hygiene_policy.json` to the W5 keep-list so the existing `root-hygiene` hook can actually fail; fix `make docs-audit` roots; wire `lint-docs.sh` into pre-commit or delete it; move the five unreferenced docs scripts to `scripts/archive/` with a note in the manifest; remove `SKIP: docs-graph-validator` once W4 clears its "pre-existing issues"; set lychee `fail: true` with a fence-aware offline relative-link check (`--offline`) and a shrunken exclude list.
- **Acceptance**: `pre-commit run --all-files` PASS on the config files themselves; `pytest tests/scripts/test_docs_hygiene.py` and `python3 scripts/check_docs_hygiene.py` go red on the retired directories (they must fail here; W3 turns them green).
- **Rollback**: revert the single commit.
- **Gate**: No (config and tooling only).

### W1 — Consolidate and freeze the archive (no removal)

- **Writes**: `git mv docs/04-explanation/history/sourceFiles/ docs/archive/w1-history-sourcefiles/` (694 files) so the quarantine lives under the one archive root; the six real explanation docs beside it stay and are collapsed in W4. Rewrite `docs/archive/overview.md` as the archive index (what each subtree is, when it was frozen, how to search it). Seed `MANIFEST.jsonl` with one row per existing archive file (reason `pre-existing-archive`, disposition `keep`) and mark the 982 byte-identical copies inside the archive as `delete-later` candidates without touching them. Update the live referrers in §2.3 that point at paths which move (the `history/` ones only; `docs/archive/` paths do not change). Replace the `04-explanation/history/sourceFiles` exclusions in pre-commit, lychee, and the prelude hook with the single `docs/archive/` exclusion. Add `docs/archive/` to `doc_audit_prescan.toml` excludes; `dope-context` already skips any path segment named `archive` (`services/dope-context/src/pipeline/docs_pipeline.py`), so no indexer change is needed.
- **Acceptance**: `git ls-files | wc -l` unchanged; `git ls-files docs/archive | wc -l` = 2,857 + manifest + index; manifest rows = 2,857; `git grep -l '04-explanation/history/sourceFiles' -- ':!docs/archive' ':!proof' ':!reports' ':!audit_inputs'` returns only `CHANGELOG.md`; pre-commit PASS; `dope-context` reindex excludes the archive.
- **Rollback**: `git revert` of the one commit.
- **Gate**: No. Nothing is deleted or exported; this is a move within `docs/` plus config.

### W2 — Get evidence blobs out of `docs/` (moves only)

- **Writes**: `git mv docs/planes/pm/_evidence/`, `_handoff/`, and `dopemux/_opus_inputs/` (115 non-md evidence files + 32 md, 44 MB) to `reports/pm-inventory/` (a `location.py` evidence root; `services/repo-truth-extractor/PHASE_D_DOCS_PIPELINE.md` already excludes those three names); `git mv` the byte-identical copy at `docs/03-reference/planes/pm/_evidence/` to `docs/archive/w2-evidence-duplicates/` with reason `exact-duplicate-of`. Repoint the two `_opus_inputs` referrers. Leave `extraction/v4/runs/`, `out/`, `reports/work-recovery/`, and `FINAL_MERGE_READINESS_SUMMARY.md` tracked as they are; record them in the manifest as `export-later` candidates with the `.gitignore:395` and `generate_final_drain_artifacts.py:128` facts, for a separate operator decision. Resolve the `out/**` = temp vs `out/proofs/` conflict in `config/extraction_hygiene/hygiene_policy.yaml` on paper only (a one-line policy edit, no file moves).
- **Acceptance**: `du -ck $(git ls-files docs)` < 60 MB (baseline 143 MB); no `.txt` under `docs/` outside `docs/archive/` and `docs/_assets`; `git ls-files | wc -l` unchanged; `scripts/audit/validate_audit_proof.py` still PASS on every `proof/*/PROOF.json`.
- **Rollback**: `git revert`.
- **Gate**: No for the moves. The deferred untrack candidates need their own gate if ever acted on, because retention rules call that a chain-of-custody operation.

### W3 — Fold the parallel trees

Dispositions verified by the parallel-tree scout with per-file `cmp` and referrer greps (§6.B). One commit per source directory.

**Free moves into `docs/archive/w3-parallel-trees/`** (every file byte-identical elsewhere, zero live referrers; reason `exact-duplicate-of`): `docs/arbitration/` (38 = `03-reference/governance/arbitration/`), `docs/flight_deck/` (25 = `03-reference/governance/flight-deck/`), `docs/policy/` (3 = `03-reference/governance/policy/`), `docs/learning/` (4 = `01-tutorials/learning/`), `docs/mobile/` (2), `docs/packaging/` (3), `docs/pr_template/` (9 = `03-reference/pr-pipeline/templates/`), `docs/releases/` (1).

**Move into the archive after a small repoint or port**:
- `docs/governance/` (10): the ref copies are newer in all five differing files; move out, then update the path named in `retention-and-redaction-rules.md`.
- `docs/rollout/` (7): one 4-line diff in `agent-enablement-guide.md` (template link); confirm the how-to copy, move out.
- `docs/skills/` (8): numbered twins of `03-reference/skills/pr-merge-specialist/`; move out.
- `docs/ux/` (6): repoint `scripts/brand_lint.py:75`, `scripts/make-zip.sh:71`, and the write target in `.claude/personas/se-ux-ui-designer.agent.md` to `04-explanation/ux/`, then move out. The persona edit needs the CCAR-002 manifest re-pin precedent.
- `docs/integrations/dopetask/` (15): fold the 4 unique files into `02-how-to/integrations/dopetask/` (the probe file is evidence → `05-audit-reports/`), move the 11 duplicates out.

**Fold with content merge**:
- `docs/systems/` → `03-reference/systems/` (canonical: 103 files, cited by `src/dopemux/orchestrator/operator_workflows.py`, `config/orchestrator/*.yaml`, `runtime_authority_manifest.json`). First port the systems-side deltas: `conport/surface-equivalence-and-drift.md` "Search Delegation" section, `serena/capability-manifest.md` plus its link, `serena/intelligence/import-issue-resolution.md` status note, and compare `serena/multi-workspace-guide.md` and `database-test-results-red-phase.md`. Then repoint `docs_index.yaml` (4 lines), `00-MASTER-INDEX.md` (4 links), and `pr_docgen_sync_workflow.py` in both skill mirrors (`readme-3.md` targets). Move the remainder of `docs/systems/` out.
- `docs/03-reference/planes/` → `docs/planes/pm/` **(reverse direction)**: `docs/planes/pm/` is the live tree (ledger tooling writes it; 4 of 5 differing pairs newer; 14 `docs_index.yaml` lines, pr-docgen-sync, `pm_phase*_verify.sh`, `doc_gate.py` all point at it). Absorb the 6 ref-only files (`memory-plane.md`, `pm-plane.md`, `pm/pm-plane.md`, `pm/hub.md`, `pm/readme.md`, `pm/_evidence/readme.md`), repoint `.github/agents/dopemux-planner.agent.md:39`, move the remainder of `03-reference/planes/` out. Root `PM_PLANE.md` stays (newer than the ref twin and load-bearing). Final home: rename `docs/planes/` to `docs/03-reference/planes/` in a later commit once every referrer above has been rewritten, so the Diataxis tree ends up canonical.
- `docs/research/` (31) → `06-research/mcp-customization/` as a frozen data pack (27 of 31 files treat TaskMaster/Leantime/TaskX as current); update `filename_exemptions` and `.claude/commands/research.md`'s template path.
- `docs/audit/` (6) → `05-audit-reports/rte-opus-uiux-claude-design-audit/`.
- `runbooks/` (3) and `docs/runbooks/` (1) → `92-runbooks/`; `prompts/` (9) → `03-reference/prompts/` after rewriting the 12 proof-JSON references (citations only); `llm-plans/` (29) → `06-research/plans/` after a per-file completion check; `contracts/` (6) → `03-reference/contracts/` with the pre-commit line 125 exemption edited.
- `docs/pr_merge/`: port the newer `usage-patterns.md` delta into `03-reference/pr-pipeline/merge/`, leave the stubs.

**Leave in place** (pinned): `docs/ops/`, `docs/pr_prep/`, `docs/pr_merge/` stubs, `UPGRADES/` (guarded), `tools/prompt_rewrite_v4/` + `CLAUDE_AUTOMATION_INSTRUCTIONS.md` (archive together only once the v4 rewrite is confirmed finished), `claudedocs/` (move dated notes to `06-research/` after a reference check; keep the three script-named files).

- **Acceptance**: `ls -d docs/*/ | wc -l` = 14 (`planes/` still present until its rename lands); `bash scripts/lint-docs.sh` PASS; `pytest tests/scripts/test_docs_hygiene.py tests/governance/test_pr_prep_contract_v2.py` PASS; broken links outside evidence ≤ 60.
- **Rollback**: `git revert` per directory commit.
- **Gate**: No, provided W0 landed. The persona repoint in `docs/ux/` needs the CCAR-002 re-pin commit.

### W4 — Resolve the 328 suffix variants

- 162 frontmatter-only: keep the base, move the `-N` file out (reason `exact-duplicate-of`), rewrite inbound links (mechanical; script from the JSON).
- 113 no-base: `git mv name-N.md name.md` (mechanical).
- Before any of the above: rewrite the live referrers that hardcode numbered names — `docs/INDEX.md` (`planes/pm/hub-2.md`, `readme-2.md`), `docs_index.yaml` (`hub-2.md`), `pr_docgen_sync_workflow.py` in `.claude/skills/` and `.github/skills/` (`hub-3.md`, `readme-3.md`), `scripts/pm_phase0_verify.sh` and `pm_phase1_verify.sh` (`-2.md` filenames), `.lychee.toml` (`adr-207-leantime-api-research-3.md`).
- 53 substantive: adjudication list for a single Sonnet-class reviewer with the diff in hand; default rule "newer `git log -1` wins, older merges in and then moves out"; ADR pairs (15) need the ADR owner because superseding an ADR is a status change, not a file move.
- Also clears the "pre-existing validation issues" that keep `docs-graph-validator` skipped; re-enable it here.
- **Acceptance**: `git ls-files 'docs/**/*-[0-9].md' | wc -l` = 0; `pre-commit run docs-graph-validator --all-files` PASS.
- **Gate**: No, except the 15 ADR adjudications, which need the ADR owner's sign-off.

### W5 — Repo root

Keep at root: `README.md`, `QUICK_START.md`, `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md` (public surface; `PM_PLANE.md` is also a marker path in `config/runtime_authority_manifest.json:809`), `AGENTS.md`, `GEMINI.md`, `CHANGELOG.md`, `INSTALL.md` (tool-required or CODEOWNERS-pinned).

`config/repo_hygiene/root_hygiene_policy.json` lists `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md`, `BRAND_SYSTEM.md` as `legacy_root_files` while `public-docs-surface.md` keeps the first three. W0 reconciles the two files; the public-docs-surface wins.

| File | Last commit | Disposition |
|---|---|---|
| `AUDIT_INITIAL_FINDINGS.md` | 2026-05-01 | → `05-audit-reports/root-relocated/audit-initial-findings.md` (target already named in the placement policy); update `config/extraction_hygiene/authority_tiers.yaml` |
| `BRAND_SYSTEM.md` | 2026-06-03 | → `04-explanation/product/brand-system.md`; reconcile with `dopemux_voice_branding_bundle/` |
| `CLAUDE_AUTOMATION_INSTRUCTIONS.md` | 2026-05-01 | → `92-runbooks/v4-prompt-rewrite-harness.md`, or archive with `tools/prompt_rewrite_v4/` |
| `DOPETASK_INTEGRATION_ANALYSIS.md` | 2026-05-01 | → `docs/archive/w5-root/` (938-line analysis dated 2026-02-16; reason `point-in-time-evidence`) |
| `DOPE_MEMORY_INTEGRATION.md` | 2026-05-01 | → `04-explanation/integrations/dope-memory-integration.md` |
| `FINAL_MERGE_READINESS_SUMMARY.md` | 2026-07-26 | stays (generated by `scripts/generate_final_drain_artifacts.py`; recorded as an `export-later` candidate in W2) |
| `KNOWN_GAPS.md` | 2026-05-31 | → `03-reference/governance/known-gaps.md`; rewrite 8 referrers |
| `README_WEBHOOKS.md` | 2026-05-01 | → `02-how-to/webhooks.md` |
| `RECOVERY_INVENTORY.md` | 2026-05-01 | → `docs/archive/w5-root/`; fix the pointer in `llm-plans/RECOVERY_AUDIT_PLAN.md` |
| `SERVICE_CATALOG.md` | 2026-05-01 | → `03-reference/systems/service-catalog.md`; rewrite `AGENTS.md` and `.github/security-scan-instructions.txt` references |
| `SUPERVISOR_INSTRUCTIONS_CHATGPT.md` | 2026-05-01 | → `03-reference/instructions/chatgpt-supervisor.md` |
| `TASK_ORCH_INTEGRATION_REPO_INVENTORY.md`, `TASK_ORCH_MCP_PLUGIN_SURFACE.md` | 2026-05-31 | → `05-audit-reports/task-orchestrator/` together (they cross-link) |

- **Acceptance**: `ls *.md | wc -l` = 10; every moved file keeps inbound links green; `public-docs-surface.md` unchanged; `root_hygiene_policy.json` matches the new root.
- **Gate**: No, except the `AGENTS.md` link edit, which is a contract-surface change and goes through its canonical writer.

### W6 — Semantic merges inside the live tree

Clusters and canonical targets come from the overlap scout (§6.A), spot-checked by the supervisor. Rules: canonical = the file that names the live runtime (for example `compose.yml`, task-orchestrator on port 7890 / service on 8000, `dopemux rte`); merged files leave a one-line redirect stub only when a skill, hook, `docs_index.yaml`, or `llms.txt` names the old path, otherwise move into `docs/archive/w6-superseded/` (reason `superseded-by:<canonical>`) and rewrite links. Check inbound links before every move; the scout did not.

**High confidence (mechanical, 60–70 files)**:
- 27 one-paragraph "Superseded by operator-contract.md" stubs under `03-reference/pr-pipeline/prep/` (adapters/*/readme, `creation-mode-rules`, `go-no-go-criteria`, `handoff-contract`, `pr-drafting-rules`, `workflow-sequence`, and the rest listed in §6.A). Keep `ambiguity-scoring.md` and verify `stash-and-branch-safety-rules.md`, which is partly live.
- 5 frontmatter-only files with empty bodies: `03-reference/test-infrastructure-overview.md`, `performance-optimizations.md`, `adhd-theme-design-principles.md`, `02-how-to/operations/adhd-engine-rollout.md`, `02-how-to/rollout/known-failure-modes.md`.
- `02-how-to/docker-setup-moved.md` (names `docker-compose.dev.yml` and `.prod.yml`, neither tracked; `docker-setup.md` names the real `compose.yml`), `02-how-to/deployment-worktree.md` (one-off branch note), `03-reference/gpt55_pm_implementer_redesign.md` (body is RTF, not markdown), `03-reference/commands/cheat-sheet.md` (garbled JSON), `03-reference/templates/pr-description.md` (a specific mega-PR body), `03-reference/instructions/{l2-outline,referenced-files-index,open-questions,synthesis-summary-v2,project-init-report,project-patch-report}.md` (another project's chat-export analysis and TaskX generator output).
- ~19 near-identical suffix variants that differ only in link targets or a port note, all resolved to the base file: `01-tutorials/installation-3.md`, `multi-project-2.md`, `02-how-to/developing-zen-2.md`, `development-setup-2.md`, `profile-usage-2/-3.md`, `03-reference/best-practices/mcp-token-management-moved{,-2}.md`, `spec/dope-memory/v1/readme-3.md` and `readme-2-moved{,-2}.md`, `services/performance-baseline-2.md`, `services/server-registry-2.md`, `instructions/codex-3.md` (base `codex.md` carries port 8000 and the doc-sync section), `instructions/claude-2.md`→`claude-3.md` (no base exists; keep the richer `claude-2` content).
- `03-reference/architecture/air-dmx-pcp-dcp-architecture-0001.md`: explicitly superseded by `air-dmx-pcp-dcp-routing-architecture-0001.md`; move out after link fixes.
- `03-reference/skills/pr-merge-specialist/*` (7 thin files): duplicates of `pr-pipeline/merge/*` at a sixth of the size; move out.

**Medium confidence (needs a reviewer with the files open, 30–40 files)**:
- **MCP setup**: canonical `02-how-to/mcp-integration-guide.md`. Merge the operator flow of `mcp-setup-other-repos.md` and the troubleshooting sections of `manage-mcp-servers.md`; move `mcp-transport-and-port-bugs.md` to `03-reference/mcp/` (it self-types as reference); move out `mcp-service-discovery-guide.md`, `mcp-tools-overview.md`, `mcp-troubleshooting.md` (pre-catalog model) after porting still-valid steps. `manage-mcp-servers.md` keeps unique dope-memory transport content. `CLAUDE.md` names `mcp-setup-other-repos.md` and `mcp-transport-and-port-bugs.md`, so both need redirect stubs or a `CLAUDE.md` edit.
- **Repo Truth Extractor**: canonical `02-how-to/extraction/repo-truth-extractor-user-guide.md`. Fold in `truth-run-command.md`, `run-v4-from-dopemux-cli.md`, `02-how-to/universal-extractor-usage.md`, and the how-to half of the wizard triple. Reconcile the phase lists in `03-reference/extraction/pipeline-phases.md` vs `phase-interaction-design.md` (they disagree). Retire the v3-runner docs (`pipeline-transport-layer{,-2}.md`, `transport-options.md`, `failure-policy-matrix.md`, `pipeline-reliability-2.md`).
- **Install**: canonical `01-tutorials/quickstart.md` for first run, `02-how-to/install.md` as the full guide. Fold `installation-legacy.md`, `01-tutorials/installation.md`, and the duplicated terminal section of `terminal-setup.md`.
- **Instructions**: `03-reference/instructions/{agents,project-instructions,codex-desktop-bootstrap-prompt,stateless-operator-mode-prompt}.md` are TaskX-era mirrors of `AGENTS.md`; fold into `codex.md` or move out. Keep `gemini.md` (unique safeguard) and `02-how-to/codex-operator-runbook.md`.
- **DCP shelf** (`03-reference/dcp/`, 57 files): `chatgpt-mcp-readonly/PROPOSED_FACADE_TOOLS.md` → `TOOL_CONTRACT.md`; `FAILURE_RUNBOOK.md` → `DISABLE_AND_ROLLBACK.md`; move the session artifacts (`DCP_THREAD_HANDOFF`, `RUNTIME_SURFACE_INVENTORY`, `TASK_ORCHESTRATOR_LOAD`, `DOPEMUX_INIT_REGISTRY_DISCOVERY`, `artifacts/DCP_*.md`) to `05-audit-reports/dcp/`. Model-routing: fold `development-factory/model-routing.md` and `dcp/model-routing-domain.md` into `03-reference/governance/model-routing.md`.
- **Task-orchestrator integration**: canonical `03-reference/orchestrator-integration/index.md`; merge its 11 thin sub-pages (22–41 lines each) into two or three pages; move `task-orchestrator-compatibility-assessment.md` to `05-audit-reports/task-orchestrator/`. Do not merge `03-reference/services/task-orchestrator.md`: it is the FastAPI service on port 8000, a different thing from the MCP plugin on 7890.
- **Multi-instance**: canonical `02-how-to/multi-instance-workflow.md`; `instance-state-persistence.md` self-declares deprecated (design packet P-04) and goes when P-04 lands; fold `role-switching-quickstart.md` into `role-persona-comprehensive-guide.md`.
- **ADHD features**: `adhd-features-user-guide.md` says 15 features, `adhd-features-quick-reference.md` says 11; regenerate the quick reference from the guide. Move the 2025-10 `features/f-new-*` design logs and `f001`/`f002` (plus variants) to `05-audit-reports/adhd-engine/`.
- **PR pipeline rollout docs**: `02-how-to/rollout/` (7), `packaging/` (3), `01-tutorials/learning/` (4) are PR-Merge-Specialist pilot pages; collapse to one rollout page and one learning page.
- **Point-in-time docs under reference**: `fast-dev-os/{thread00-current-operating-ledger,packet-ledger,pr-ledger,proof-ledger}.md` (self-labelled snapshots), `03-reference/task-packets/rte-0*.md` and `tp-cloudflare-webhooks-0001*.md`, `02-how-to/operations/dependabot-security-review.md` → `05-audit-reports/`.

**Stale content on live subjects (rewrite in place, do not move)**: `development-troubleshooting.md` and `services/server-registry.md` still describe Task-Master (removed); `leantime-integration-guide.md` and `claude-code-integration-guide.md` describe Leantime (still live per `AGENTS.md:134`) as of 2026-02. Port drift (3014 vs 7890 vs 8000) needs one ruling applied everywhere.

**Not examined** (scout indexed titles only): `integrations/dopetask/` (11 policy pages, probably mis-filed as how-to), `fast-dev-os/` vs `development-factory/`, `Dopemux Cockpit TUI Design System/`, `spec/uberslicer/`, `truth/`, `second-brain/`, the dope-memory spec pairs. A follow-up scout or the W6 reviewer covers them.

- **Acceptance**: each canonical file passes the frontmatter guard; `docs_index.yaml`, `00-MASTER-INDEX.md`, `llms.txt`, and `CLAUDE.md` name only canonical paths; `grep -rl 'Superseded by' docs/03-reference/pr-pipeline/prep | wc -l` = 0; broken links outside evidence ≤ 20; `dope-context` reindex succeeds.
- **Rollback**: `git revert` per cluster commit.
- **Gate**: No.

### W7 — Indexes, metadata cadence, and gate closure

- Regenerate `00-MASTER-INDEX.md`, `INDEX.md`, `docs_index.yaml`, `llms.txt` against the final tree (write a small generator so `docs_index.yaml` stops being hand-maintained).
- Decide the `next_review` field: either remove it from every frontmatter and from `REQUIRED_FIELDS['runbook']`, or set a quarterly job that fails CI on overdue runbooks only. Recommendation: keep it for `type: runbook` and `type: how-to`, drop it everywhere else.
- Collapse `.github/skills/` + `templates/skills/` + `.claude/skills/` to one source with a sync script, or document which one is generated.
- Shrink `.lychee.toml` and pre-commit `exclude:` lists to evidence roots only; flip lychee to `fail: true`.
- Record the consolidation in `CHANGELOG.md` and close with one independent audit of the final tree (AGENTS.md §9.1 route).
- Hand the operator the manifest's `delete-later` and `export-later` candidate counts as a separate decision package; this plan takes no action on them.
- **Acceptance**: `pre-commit run --all-files` PASS with zero `SKIP`; lychee offline PASS; `lint-docs.sh` PASS; `ls -d docs/*/ | wc -l` = 13; all table targets in §1 met.
- **Gate**: final audit route per AGENTS.md.

## 6. Scout evidence (delegated, cost-first)

Three bounded read-only scouts were dispatched per the cost-first delegation policy. Requested routes: Explore agent / Sonnet (how-to and reference overlap), Explore agent / Sonnet (parallel-tree characterisation), Explore agent / Haiku (non-docs directory classification and governance constraints). Effort: runner default. Observed model identity: UNKNOWN (no runtime receipt). Their findings are summarised below and were spot-checked by the supervisor before being used in W3, W5, and W6.

### 6.A Overlap scout (how-to, reference, runbooks; 506 files indexed)

Twelve overlap clusters: MCP setup (four how-tos repeat `dopemux mcp init`, `repair-config`, `mcp doctor`, and each carries its own troubleshooting section), Repo Truth Extractor (`dopemux rte run` documented in 11 files, prescan in 7, two conflicting phase lists), install/deploy/docker, instructions (TaskX-era mirrors of `AGENTS.md`), DCP and routing (one explicit supersession, two proposed-vs-final pairs, session artifacts filed as reference), PR pipeline (27 superseded stubs, a thin `skills/` duplicate of `merge/`), task-orchestrator integration (11 thin sub-pages; name collision between the port-8000 service and the port-7890 plugin), multi-instance (one self-deprecated page), ADHD features (11 vs 15 feature count), runbooks in four homes, dopetask integration (not examined), fast-dev-os vs development-factory (not examined). The scout's removable-file estimate is 110–130 of 506; only the stubs, the empty files, and the near-identical variants are high confidence. Supervisor spot-checks: 27 stub files found by grep, the RTF body confirmed, three empty bodies confirmed, both phantom compose filenames confirmed absent from git.

### 6.B Parallel-tree scout (planes, systems, governance, arbitration, flight_deck, 13 small dirs)

Per-file `cmp` and referrer greps. `docs/arbitration/`, `flight_deck/`, `policy/`, `learning/`, `mobile/`, `packaging/`, `pr_template/`, `releases/` are 100 % byte-identical to their Diataxis twins with zero live referrers (supervisor re-ran `diff -rq` on the first three: 0 differences). `docs/governance/` is older than `03-reference/governance/` in every differing file. `docs/systems/` and `03-reference/systems/` differ in both directions (10 substantive pairs; the reference tree is cited by code and config). `docs/planes/pm/` is the live PM tree, not `03-reference/planes/`: four of five differing pairs are newer there, the ledger tooling writes it, and `docs_index.yaml`, pr-docgen-sync, and two verify scripts point at it. `docs/ux/` has three live referrers (`brand_lint.py`, `make-zip.sh`, a persona write target). `docs/pr_prep/`, `pr_merge/` are stubs pinned by `tests/governance/test_pr_prep_contract_v2.py`. `docs/ops/` is live and pinned by `AGENTS.md:196` and `validate_change_contract.py:41`. `docs/research/` is a frozen 2026-04 data pack where 27 of 31 files treat TaskMaster/Leantime/TaskX as current. Live code hardcodes numbered filenames (`hub-2.md`, `hub-3.md`, `readme-3.md`, `*-2.md` in verify scripts). The 2026-05-01 commit date is a 12,165-file bulk import, not a staleness signal; content in the small dirs was authored 2026-03.

### 6.C Non-docs directory scout (22 directories, 22 root files, governance constraints)

`proof/`, `proofs/`, `out/proofs/`, `audit_inputs/`, `repo-truth-pack/`, `.control-tower/` are governed evidence or tool-required and stay. `src/dopemux/governed_execution/audit_identity/location.py:22` treats `proof/`, `proofs/`, `out/`, `reports/` as evidence roots; retention rules make any move a chain-of-custody operation and still name `docs/governance/` as an indefinite-retention location; three proof-path conventions coexist. `extraction/v4/runs/` is already matched by `.gitignore:395` and only needs `git rm --cached`. `FINAL_MERGE_READINESS_SUMMARY.md` is generated by `scripts/generate_final_drain_artifacts.py:128`. `dopemux_voice_branding_bundle/` is loaded at runtime by `src/dopemux/ui/voice.py`. `UPGRADES/` is guarded by pre-commit lines 225–248. Three `claudedocs/` files are named in script comments or log text. `docker/mcp-servers-source/pal/` (48 files) is a vendored upstream; the scout's claim that the `docker/mcp-servers/` exemption path does not exist was wrong, both directories exist. `services/` markdown is 340 prompt assets under `repo-truth-extractor/` plus six real per-service docs. Root-file dispositions are in W5; the scout's "root hygiene unenforced" claim was wrong (the `root-hygiene` hook runs; its allowlist is simply too wide), and the plan says so.


## 7. Validation performed for this audit

| Check | Result |
|---|---|
| `bash scripts/lint-docs.sh docs` before and after adding this file | PASS (5/5) — demonstrates the gate's blind spots, not tree health |
| Exact-duplicate census (`shasum` over `git ls-files '*.md'`) | PASS — 1,147 groups |
| Relative-link scan, fence-aware (`reports/docs-hygiene/consolidation-baseline-2026-10-09.json`) | PASS — 2,435 broken |
| Suffix-variant diff classification | PASS — 162 / 38 / 15 / 113 |
| `next_review` overdue census | PASS |
| `pre-commit run --files` on this file and the two JSON baselines | PASS (13 hooks ran, 0 failed) |
| Pre-commit docs hooks on the whole tree | NOT_RUN (would take minutes and is not needed for a read-only audit) |
| Live MCP indexers (`dope-context`, ConPort) | NOT_RUN — ConPort, dope-memory, and task-orchestrator failed to connect this session |

## 8. Remaining uncertainty

- Which `out/`, `reports/work-recovery/`, and `extraction/` files are cited by `proof/` bundles is unverified; any future decision on the `export-later` candidates must grep first.
- Whether the ChatGPT supervisor route and the v4 prompt-rewrite harness are still live decides two root-file dispositions in W5.
- The 53 substantive suffix variants need human or reviewer-model adjudication; counts are exact, verdicts are not.
- `docs/systems/` vs `03-reference/systems/`: 10 substantive pairs were sampled, not all diffed; W3 must diff every shared path before moving anything out.
- No scout checked inbound links for the W6 move candidates; the W6 packet does that first.
- Port drift for task-orchestrator (3014 legacy, 7890 MCP plugin, 8000 FastAPI service) has no single ruling; several "duplicate" pairs differ only in that number.

## 9. Requested next step

None of W0 through W7 now needs an operator gate: every wave is config plus `git mv` within the repository. Authorise W0 as the first Task Packet; W1 (archive consolidation) can follow in the same PR. The only operator decisions left are the deferred `delete-later` and `export-later` candidates the manifest will accumulate. W0 can start immediately as a non-gated packet; it is the prerequisite for everything else.

## 10. Execution log

### 2026-10-10 — W0 + W1 executed on branch `docs/consolidation-w0-w1`

Operator authorised W0 and W1 on 2026-10-10 under the stay-in-repo rule. Executed in worktree `.worktrees/docs-consolidation-w0-w1`:

- **W0**: `canonical_roots` cut to the target set; the 18 remaining trees became `legacy_roots` (tolerated, labelled `legacy-root`, planned targets recorded) so CI stays green until W3; `map-projects` now routes to `03-reference/systems/`; the unknown-top-level fallback no longer points into the archive; `archive_manifest` added. New `docs-archive-manifest-guard` pre-commit hook plus `--check-archive-manifest` mode in `check_docs_hygiene.py`. New `scripts/docs_archive_move.py` (test-first, 9 tests). All ten `history/sourceFiles` hook exclusions collapsed to the single `docs/archive/` exclusion, and the same path swap applied in `docs_prohibited_patterns.sh`, `docs_frontmatter_guard.py`, `docs_validator.py`, `lint-docs.sh`, and three tests. `make docs-audit` roots fixed; `make docs-lint` added. `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md` moved from `legacy_root_files` to `allowed_root_files`. Four unreferenced docs scripts moved to `scripts/legacy/`. `scripts/governance/validate_change_contract.py` now mirrors the hook's `docs/archive/` frontmatter exemption (it had asserted frontmatter on every docs markdown in a diff, which no earlier PR had exercised against the archive). Not done in W0: lychee changes (deferred to W7 as the plan already said), the `allowed_root_files` shrink (deferred to W5).
- **W1**: manifest seeded with 2,174 pre-existing archive rows (856 byte-identical copies labelled `delete-later` candidates, untouched); the 694-file quarantine moved to `docs/archive/w1-history-sourcefiles/docs/04-explanation/history/sourceFiles/`; `docs/archive/overview.md` rewritten as the frozen-archive index; `doc_audit_prescan.toml` excludes the archive; `docs/runbooks/ddd-release-gate-app.md` moved to `92-runbooks/` (the only file the tightened policy flagged). `git ls-files | wc -l` unchanged apart from the three new audit artifacts and the new script and test.

### 2026-10-10 — merge strategy and W2

Operator ruling: the whole workstream merges together when complete. PR #1423 is the single integration PR (kept as a draft until W7); each wave lands as its own commit on `docs/consolidation-w0-w1` so any wave can still be reverted on its own.

- **W2 executed**: `docs/planes/pm/_evidence/`, `_handoff/`, and `dopemux/_opus_inputs/` (188 files, 44 MB) moved to `reports/pm-inventory/` (an evidence root per `location.py`). The byte-identical copies under `docs/03-reference/planes/pm/` (131 files, 130 identical to the originals; the unique `_evidence/readme.md` is superseded by the planes `readme-3.md`) moved into `docs/archive/w2-evidence-duplicates/` with manifest rows (`delete-later` candidates). Referrers repointed: `.gitignore` (zip allowlist and `.outputs` pattern), `00-MASTER-INDEX.md` (three runtime-truth summaries), `documentation-catalog.md`, `PHASE_D_DOCS_PIPELINE.md`, and a path-specific `reports/pm-inventory/` exemption in the markdown-location pre-commit guard. `hygiene_policy.yaml` now classes `out/proofs/**` as `proof_bundle` ahead of the `out/**` temp rule. No code referenced the old paths.
- Acceptance note: `docs/` is 101 MB, not the < 60 MB the plan projected, because the 43 MB duplicate stays in the repository under `docs/archive/` per the stay-in-repo rule. The active tree (outside `docs/archive/`) carries no evidence blobs; the two remaining `.txt` files under active docs are a brand-mark asset and a SHA-sums file.

**Deferred candidates (operator decision package, no action taken)**

| Path | Tracked files | Fact | Candidate |
|---|---|---|---|
| `extraction/v4/runs/`, `extraction/prescan_v5*/` | 1,276 + 3 | already matched by `.gitignore:395` (`extraction/v*/`); 26-way duplicated test run | export-later |
| `out/cockpit-*`, `out/chatgpt-project-upload-set/`, `out/rte-*` | ≈ 250 md | legacy packs; `proof/` citation status UNKNOWN (grep before any action) | export-later |
| `reports/work-recovery/` | 108 md | March 2026 snapshot, 13 MB | export-later |
| `reports/leantime-repo-truth-pack/`, `reports/task-orchestratorrepo-truth-pack/` | 32 md | mirrors of `repo-truth-pack/` | export-later |
| `FINAL_MERGE_READINESS_SUMMARY.md` | 1 | generated by `scripts/generate_final_drain_artifacts.py:128` | untrack-later |
| `docs/archive/` byte-identical copies | 856 + 130 | labelled in `MANIFEST.jsonl` | delete-later |

### 2026-10-10 — W3a/W3b executed (parallel trees, part 1)

- **Archived into `docs/archive/w3-parallel-trees/`** (manifest rows, `delete-later` candidates): `arbitration` (38), `flight_deck` (25), `policy` (3), `learning` (4), `mobile` (2), `packaging` (3), `pr_template` (10), `releases` (1) as `exact-duplicate-of` their Diataxis twins, re-verified by blob hash before moving; `governance` (10), `rollout` (7), `skills` (9) as `superseded-by`; `integrations/dopetask` 11 duplicates and the older `install-migration.md`; `ux` 5 duplicates plus the compatibility `ux-style-guide.md`.
- **Relocated as live content**: the 3 unique dopetask contract pages into `02-how-to/integrations/dopetask/` and the 2026-03-26 probe into `05-audit-reports/dopetask/`; `docs/research/mcp-customization/` to `06-research/mcp-customization/`; `docs/audit/rte-opus-uiux-claude-design-audit/` to `05-audit-reports/`; root `runbooks/` trio to `92-runbooks/devops-autopr-*.md` (kebab-case).
- **Referrers repointed**: `master-design-spec-v2.md`, `brand-opportunities.md`, `brand-resource-pack.md`, `tp-gov-001-…-hardening.md`, `retention-and-redaction-rules.md`, `02-how-to/rollout/agent-enablement-guide.md` (also fixed its `jules/task-template.md` link to the real `task-spec.md`), `scripts/brand_lint.py` (dropped the duplicate authoritative path), `scripts/make-zip.sh`, `.claude/commands/research.md`, the placement policy's `filename_exemptions`, and the write targets in `.claude/personas/se-ux-ui-designer.agent.md` (CCAR-002 hash re-pinned in its own commit; `build_normalized_catalog.py --check` CHECK_PASS).
- `legacy_roots` shrank from 18 to 3 (`planes`, `systems`, `spec`). Historical references inside `task-packets/*.json` and audit packs to the old paths are left as records.
- Deferred from W3: `prompts/`, `llm-plans/`, `contracts/` stay in place (prompt and plan citations live in frozen `proof/` JSON; `contracts/` is a contract surface with its own pre-commit exemption). `docs/planes` → `03-reference/planes` rename deferred: 50+ live referrers including skill mirrors, verify scripts, tests, and a task-packet JSON; `docs/planes` stays a legacy root until a dedicated packet.

### 2026-10-10 — W3c executed (`docs/systems` folded into `03-reference/systems`)

- 49 byte-identical files and 11 numbered variants archived as `exact-duplicate-of`; `dddpg/*` (4), `dope-context/deployment.md`, and `dopecon-bridge/readme-2/-3.md` archived as `superseded-by` the newer reference copies; the five files where the `docs/systems` side carried newer content (`conport/surface-equivalence-and-drift.md` Search Delegation section, `serena/callable-surface-inventory.md`, `serena/intelligence/import-issue-resolution.md`, `serena/intelligence/database-test-results-red-phase.md`, `serena/multi-workspace-guide.md`) had their bodies copied over the reference copies and were archived as `merged-into`; the systems-side path claims were checked against the tree first (`services/serena/intelligence/test_database.py` and `services/serena/multi_workspace_wrapper.py` exist, the `v2` paths the reference copies named do not). `serena/capability-manifest.md` (unique) moved into the reference tree.
- Referrers repointed in all three `pr-docgen-sync` skill mirrors (`system_hubs` now `03-reference/systems/{dopecon-bridge,production}/readme.md`; the `docs/systems/` classification prefix and reference-location list), the taxonomy policy references, `docs_index.yaml` (4 conport entries plus 4 stale `planes/pm/_evidence` entries missed in W2), `00-MASTER-INDEX.md`, `.lychee.toml`, `dope-context-technical-deep-dive.md`, both `design-evolution-2026` copies, and `PHASE_D_DOCS_PIPELINE.md`. `legacy_roots` is now `planes` and `spec`.
- Known stale index entry left for W7: `docs_index.yaml` names `docs/05-audit-reports/service-maturity-gap-analysis.md`, which does not exist on `main` either.

### 2026-10-10 — W3d executed (`docs/planes` folded into `03-reference/planes`); W3 complete

Direction reversed from the scout's recommendation after counting referrers on both sides: `docs/03-reference/planes/` is the Diataxis home and was itself cited by `PROJECT.md`, the governance trust map, the ADHD-engine system doc, the memory deep dive, and `.github/agents/dopemux-planner.agent.md`, so the live content moved there and every `docs/planes/` referrer was repointed instead.

- The five pairs where `docs/planes` was newer (`07-dopetask-integration`, `pm-implementation-ledger`, `pm-plane-normalized-tool-surface`, `task-orchestrator-leantime-followups`, `write-boundaries`) had their bodies copied over the reference copies and were archived as `merged-into`; 28 identical copies archived as `exact-duplicate-of`; the 42 planes-only files (mostly numbered variants plus `execution/agent-leasing-contract.md`) moved into `03-reference/planes/` for W4 to collapse. `docs/planes/` no longer exists; `legacy_roots` is empty.
- Repointed: all three `pr-docgen-sync` skill mirrors (ledger and hub paths, classification prefixes; mirrors verified byte-identical afterwards), `scripts/pm_phase0_verify.sh`, `pm_phase1_verify.sh`, `SUPERVISOR_INSTRUCTIONS_CHATGPT.md`, `docs_index.yaml`, `00-MASTER-INDEX.md`, `INDEX.md`, the `03-reference` and `04-explanation` overviews, `documentation-catalog.md`, `doc-audit-prescan.md`, `services/task-orchestrator.md`, three `migration-taskx-to-dopetask` variants, nine `adr-pm-00*` variants, `PHASE_D_DOCS_PIPELINE.md`, the planes docs' own self-references, `scripts/docs_validator.py` (redundant `docs/planes/` allowed path removed), the placement policy (`map-pm`), and the two integration-test fixtures. `task-packets/*.json` and audit packs keep their historical paths.
- `tests/pr_docgen_sync_skill` 11/11 PASS after the fixture repoint; hygiene checks and lint PASS; `docs/` now has 13 entries plus the untracked `docs/instructions/` scratch file that is not part of this branch.

### 2026-10-10 — W4 executed (suffix variants)

Strict classification after the W3 folds (dated stems such as `-2026-04-24`, `-0001`, and the `deep-research-report-N` series excluded; `pr_prep/` and `pr_merge/` excluded as test-pinned): 132 frontmatter-only, 43 near-identical, 19 substantive, 12 base-less variants. Actions, all recorded in `reports/docs-hygiene/w4-actions-2026-10-10.json`:

- 132 frontmatter-only variants archived as `exact-duplicate-of` their base.
- 43 near-identical: base wins unless the variant was strictly newer by commit date; one such case (`01-tutorials/installation-3.md`) had its body merged into the base. The rest archived as `superseded-by`.
- Substantive non-ADR: `docker-setup-moved{,-2}.md` archived as `obsolete` (they name compose files that do not exist); `dope-memory-deep-dive-2.md`, the copy the indexes pointed at, merged into its base; `pipeline-reliability-2.md`, `governance/rules-2.md`, `instructions/codex-3.md`, planes `00-index-2`/`hub-3`/`readme-3`, dope-memory spec `readme-3`, the `-moved` copies of `worktree-switching-guide` and `dopetask-kernel-integration`, and `01-tutorials/multi-project-2.md` archived as `superseded-by` their base.
- Base-less: `instructions/claude-2.md` → `claude.md` (richer; `claude-3.md` archived), `supervisor-2.md` → `supervisor.md` (`-3` archived; it linked to `-2` variants), `opus-cross-plane-audit-2.md` → base (`-3` byte-identical, archived), `pm-plane-gaps-2.md` → base, `root-relocated/{claude,codex}-2.md` → base names, `tp-cloudflare-webhooks-0001-2/-3.md` (identical bodies) and `history/design-evolution-2026-2.md` archived.
- **Left in place for the ADR owner**: `adr-201-conport-kg-security-hardening-2/-3.md` and `adr-202-serena-v2-production-validation-2/-3.md` differ substantively from their bases; collapsing them is a status decision, not a file move.
- Every inbound reference rewritten by resolving relative links against the move map (16 docs, `docs_index.yaml`) plus literal path replacement in 12 code/config/skill/test files (`pr-docgen-sync` instruction candidates and user-doc targets now name `codex.md`, `claude.md`, `server-registry.md`, `performance-baseline.md`, `hub.md`; `scripts/verify_profile_week2_integration.sh`, `tests/mcp/test_p22_regression_checks.py`, `.lychee.toml`, the placement policy). Zero broken links now point at a variant name; active-docs broken links fell from 166 to 130 (the rest pre-date this work and belong to W6/W7).
- `scripts/docs_validator.py` now accepts the `deprecated` ADR status that three ADRs already use (no schema pins the vocabulary); with that, the graph validator reports 0 errors over all 1,316 active docs and task-packet markdown, so the `SKIP: docs-graph-validator` line was removed from `.github/workflows/docs.yml`. 66 non-blocking "missing recommended section" warnings remain.

### 2026-10-10 — W5 executed (repository root)

Root markdown is now the public surface plus tool-required files: `README.md`, `QUICK_START.md`, `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md`, `AGENTS.md`, `GEMINI.md`, `CHANGELOG.md`, `INSTALL.md`, and the generated `FINAL_MERGE_READINESS_SUMMARY.md` (kept tracked per the stay-in-repo rule and now allow-listed).

- **Relocated with generated frontmatter and rebased links**: `AUDIT_INITIAL_FINDINGS.md` → `05-audit-reports/root-relocated/audit-initial-findings.md`; `BRAND_SYSTEM.md` → `04-explanation/product/brand-system.md`; `CLAUDE_AUTOMATION_INSTRUCTIONS.md` → `92-runbooks/v4-prompt-rewrite-harness.md`; `KNOWN_GAPS.md` → `03-reference/governance/known-gaps.md`; `README_WEBHOOKS.md` → `02-how-to/webhooks.md`; `SUPERVISOR_INSTRUCTIONS_CHATGPT.md` → `03-reference/instructions/chatgpt-supervisor.md`; the two `TASK_ORCH_*` audits → `05-audit-reports/task-orchestrator/task-orch-{integration-repo-inventory,mcp-plugin-surface}.md`.
- **Archived into `docs/archive/w5-root/`**: `DOPETASK_INTEGRATION_ANALYSIS.md` and `RECOVERY_INVENTORY.md` (point-in-time evidence) and `DOPE_MEMORY_INTEGRATION.md`, which turned out to be an older copy of the existing `04-explanation/integrations/dope-memory-integration.md` (the in-tree copy is a superset with the multi-instance MCP wiring section), so it is `superseded-by` that file rather than moved over it.
- **Deviation from the plan table**: `SERVICE_CATALOG.md` stays at root. `AGENTS.md:19` and the doctrine module list it as a Truth Order anchor beside `PROJECT.md`, `ARCHITECTURE.md`, and `PM_PLANE.md`; moving it would mean editing two contract surfaces for no structural gain.
- Referrers repointed in `llms.txt`, `.claude/brand-voice-guidelines.md`, the Cockpit design-system README, the documentation source map, two branding docs, `dopemux-hooksd.md`, `adr-223`, and `root-relocated/docs-audit.md`. The RTE audit pack under `05-audit-reports/rte-opus-uiux-claude-design-audit/` keeps its historical mentions. `config/repo_hygiene/root_hygiene_policy.json` no longer lists the moved files; `legacy_root_files` is empty, so the `root-hygiene` hook now rejects any new root markdown that is not explicitly allowed.
- Validation: placement, filename, lint, root hygiene, graph validator (0 errors) PASS; 202 tests PASS including the Repo Truth Extractor authority-tier test that names `AUDIT_*.md` by pattern.

### 2026-10-10 — W6 executed (mechanical part); content merges deferred to a reviewer

Actions recorded in `reports/docs-hygiene/w6-actions-2026-10-10.json`. Nothing deleted.

- **Archived into `docs/archive/w6-superseded/`** (23 files): the 5 frontmatter-only empty files; the 6 other-project or generator-output files under `03-reference/instructions/` (`l2-outline`, `referenced-files-index`, `open-questions`, `synthesis-summary-v2`, `project-init-report`, `project-patch-report`); `templates/pr-description.md` (a specific PR body); `02-how-to/deployment-worktree.md` (one-off branch note); `gpt55_pm_implementer_redesign.md` (RTF body); `air-dmx-pcp-dcp-architecture-0001.md` (explicitly superseded); `dcp/chatgpt-mcp-readonly/PROPOSED_FACADE_TOOLS.md` (superseded by `TOOL_CONTRACT.md`); the four thin `skills/pr-merge-specialist/*` duplicates of `pr-pipeline/merge/*` (the unique `gemini/`, `jules/`, and `skill.md` assets stay because the skill `BUILD.md` files point there); the three v3-runner extraction docs.
- **Relocated as evidence** (22 files, links rebased): four DCP session artifacts → `05-audit-reports/dcp/`; the 14 `rte-0*` packet-evidence pages → `05-audit-reports/rte/`; the six 2025-10 `features/f-new-*` design logs → `05-audit-reports/adhd-engine/`; `dependabot-security-review.md` → `05-audit-reports/dependabot-security-review-2025-10.md`; `task-orchestrator-compatibility-assessment.md` → `05-audit-reports/task-orchestrator/compatibility-assessment-2026-05-28.md`.
- **Left in place on evidence**: `f001`/`f002` (named by `services/serena/*.py` and `mcp/feature-register.yaml`), `dcp/artifacts/*` (inputs to `tools/dcp/build_comprehensive_bundle.py`), `commands/cheat-sheet.md` (a target of `qa/scenarios/80_docs_drift.py`), the `fast-dev-os` ledgers (linked from the kit README and prompts), the 27 `pr-pipeline/prep` superseded stubs (pinned by `tests/governance/test_pr_prep_contract_v2.py` together with `docs/pr_prep/`).
- Dead index lines for the archived files removed from `03-reference/overview.md`, `02-how-to/overview.md`, `00-MASTER-INDEX.md`, and `worktree-comprehensive-guide.md`; obsolete `root_overrides` and the RTF filename exemption removed from the placement policy.

**Deferred to a reviewer with the files open** (content authoring, not file hygiene; the plan's own W6 rated these medium confidence): MCP setup how-to merge into `mcp-integration-guide.md`; Repo Truth Extractor how-to fold into the user guide and the `pipeline-phases` vs `phase-interaction-design` phase-list conflict; `installation-legacy` / tutorials `installation` fold into `install.md`; TaskX-era `instructions/*` fold into `codex.md`; the 11 thin `orchestrator-integration` sub-pages; `instance-state-persistence.md` retirement (waits on design packet P-04); the ADHD quick-reference regeneration (11 vs 15 features); `rollout/` + `learning/` + `packaging/` collapse; `FAILURE_RUNBOOK` → `DISABLE_AND_ROLLBACK`; model-routing fold; `fast-dev-os` vs `development-factory`; the Task-Master and Leantime stale-content rewrites; the task-orchestrator port ruling (3014 / 7890 / 8000); and the `adr-201`/`adr-202` variant pairs for the ADR owner.

### 2026-10-10 — W7 executed (indexes, links, gates); workstream complete pending audit

- **Links**: 27 broken relative links whose target basename exists at exactly one active path were repointed across 13 files. The 116 that remain either name files that exist nowhere in the repository (108) or have several same-named candidates (8); the full list with candidates is `reports/docs-hygiene/w7-broken-links-2026-10-10.json` for a reviewer. No link in the active tree points at a suffix-variant or archived name.
- **Indexes**: `docs_index.yaml` references resolve (the one dead `service-maturity-gap-analysis` entry, already dead on `main`, removed); `INDEX.md`, `00-MASTER-INDEX.md`, and both section overviews resolve. `docs_index.yaml` remains hand-maintained; writing a generator was out of this workstream's reach and is listed below.
- **Gates**: `.lychee.toml` `exclude_path` shrunk from 16 entries to `docs/archive/`, `docs/05-audit-reports/`, `docs/06-research/`, `docs/94-architecture/c4/`, `README.md`; the job stays `fail: false` until the 116 residual links are resolved. The graph validator runs in CI again (W4). Every docs hook excludes only `docs/archive/`.
- **`next_review` decision**: keep the field (the validator requires it for runbooks) and do not add a CI cadence; a quarterly overdue report is cheap to add later, while deleting the field from ≈ 1,100 frontmatters would be diff noise for no behaviour.
- **Skill mirrors**: `.claude/skills`, `.github/skills`, and `templates/skills` were kept byte-identical through every edit (verified with `cmp`); collapsing them to one source needs the owner of the `BUILD.md` sync process, so it is listed below.
- **Residual exact duplicates in the active tree** (35 groups): 19 are the test-pinned `docs/pr_prep/`/`docs/pr_merge/` compatibility copies, 10 are inside the frozen `06-research/mcp-customization` data pack, 5 are the ADR variant pairs left for the ADR owner.

## 11. Closing state and hand-off

Branch `docs/consolidation-w0-w1`, PR #1423, eleven commits, 1,685 files changed of which about 1,500 are renames. Every wave is one commit and reverts independently. Nothing was deleted or exported; 3,455 manifest rows record every archive move.

Still open, each needing a decision or an author rather than a file move:

1. AGENTS.md §9.1 embedded audit of this PR (hook and policy packet) before readiness. NOT_RUN; needs an operator-authorised auditor route.
2. The W6 content merges listed above (MCP, RTE, install, instructions, orchestrator thin pages, multi-instance, ADHD quick reference, rollout/learning, FAILURE_RUNBOOK, model-routing, fast-dev-os vs development-factory, Task-Master/Leantime stale text, the task-orchestrator port ruling).
3. `adr-201`/`adr-202` variant pairs (ADR owner).
4. The manifest's 1,420 `delete-later` and the W2 `export-later` candidates (operator decision package; no action taken).
5. 116 residual broken links with no unique target.
6. A `docs_index.yaml` generator and the three-way skill mirror collapse (tooling owners).

