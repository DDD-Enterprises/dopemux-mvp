# RTE Deep Audit Stage 3: Prescan Architecture & Thoroughness

## Prescan Design (Stage 0)
- **Engine:** `lib/prescan/engine.py` using `PrescanEngine`.
- **Passes:** Executes four canonical passes: `dedup`, `discover`, `feasibility`, `optimize`.
- **Artifacts:** Generates `IntelligenceRouter` and persists intelligence to the `prescan/` run directory.
- **Thoroughness:** Inspects file sizes, complexity, git history, and dependency graphs before the first LLM call.

## Control Flow & Determinism
- **Integrated by Default:** Unlike v3/v4, prescan is integrated into the v5 `main()` loop.
- **Advisory vs. Authoritative:** By default, prescan is non-authoritative (`--prescan-allow-scope-reduction` is off). It provides hints but does not prune the scan scope unless explicitly authorized.
- **Dynamic Tiering:** Prescan materially affects the run by upgrading model tiers (e.g., `bulk` -> `synthesis`) for partitions containing high-complexity code.

## Hidden Heuristics
- **Reordering:** The router reorders file paths within partitions based on 'importance' heuristics discovered during prescan.
- **Brief Generation:** `PartitionBriefGenerator` uses prescan intelligence to inject 2000-token summaries into prompts, providing global context to local extractions.

## Verdict
Prescan architecture is **Highly Sophisticated**. It transcends simple "artifact generation" by materially improving real-scan context through reordering, dynamic tiering, and cross-partition briefing. 
