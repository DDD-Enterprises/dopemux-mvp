# Dopemux Constraint Pack Index

- status: complete
- reason this pack exists: provide Deep Research with curated Dopemux authority and boundary docs without unrelated repository artifacts.

## Upload Guidance

- Use the full pack for baseline and synthesis Deep Research chats.
- For 10-file server Deep Research chats, use a subset: `ARCHITECTURE.md`, `system-boundaries.md`, `PM_PLANE.md`, relevant `SYSTEM_*.md`, and the `TRUTH_*.md` files most relevant to the server.

## Reminder

- Preserve split authority.
- Bridge is not authority.
- PM, memory, and retrieval are split.
- Mark UNKNOWN when authority or runtime truth is not proven.

## Files Copied

| File | Source path |
| --- | --- |
| `RULES.md` | `user-provided constraint text in current request` |
| `ARCHITECTURE.md` | `ARCHITECTURE.md` |
| `system-boundaries.md` | `docs/03-reference/systems/system-boundaries.md` |
| `PM_PLANE.md` | `PM_PLANE.md` |
| `TRUTH_SYSTEMS.md` | `docs/03-reference/truth/truth-systems.md` |
| `TRUTH_CANONICALS.md` | `docs/03-reference/truth/truth-canonicals.md` |
| `TRUTH_GAPS.md` | `docs/03-reference/truth/truth-gaps.md` |
| `TRUTH_DATA_EVENTS.md` | `docs/03-reference/truth/truth-data-events.md` |
| `TRUTH_INTERFACES.md` | `docs/03-reference/truth/truth-interfaces.md` |
| `SYSTEM_Dopemux.md` | `docs/03-reference/systems/dopemux/system-dopemux.md` |
| `SYSTEM_TaskOrchestrator.md` | `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md` |
| `SYSTEM_ConPort.md` | `docs/03-reference/systems/conport/system-conport.md` |
| `SYSTEM_DopeMemory.md` | `docs/03-reference/systems/dope-memory/system-dopememory.md` |
| `SYSTEM_DopeContext.md` | `docs/03-reference/systems/dope-context/system-dopecontext.md` |
| `SYSTEM_DopeconBridge.md` | `docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md` |
| `SYSTEM_ADHDEngine.md` | `docs/03-reference/systems/adhd-engine/system-adhdengine.md` |
| `SYSTEM_RepoTruthExtractor.md` | `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md` |
| `SERVICE_CATALOG.md` | `SERVICE_CATALOG.md` |
| `PROJECT.md` | `PROJECT.md` |

## Missing Files

- None

## Duplicate Candidates Skipped

| Canonical file | Skipped candidate | Selected source |
| --- | --- | --- |
| `ARCHITECTURE.md` | `docs/03-reference/systems/dope-context/architecture.md` | `ARCHITECTURE.md` |
| `ARCHITECTURE.md` | `docs/systems/dope-context/architecture.md` | `ARCHITECTURE.md` |
| `PM_PLANE.md` | `docs/03-reference/planes/pm-plane.md` | `PM_PLANE.md` |
| `PM_PLANE.md` | `docs/03-reference/planes/pm/pm-plane.md` | `PM_PLANE.md` |
| `TRUTH_CANONICALS.md` | `docs/archive/unclassified-top-level/repo-truth/truth-canonicals.md` | `docs/03-reference/truth/truth-canonicals.md` |
| `TRUTH_INTERFACES.md` | `docs/archive/unclassified-top-level/repo-truth/truth-interfaces.md` | `docs/03-reference/truth/truth-interfaces.md` |

## Exclusions

- Excluded design-system/cockpit docs, screenshots, zips, `out/`, rollout plans, and unrelated audit artifacts.
- No fake replacement was created for missing required files.
