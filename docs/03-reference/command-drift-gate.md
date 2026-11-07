---
id: COMMAND-DRIFT-GATE-REFERENCE
title: Slash Command Drift Gate
type: reference
owner: '@hu3mann'
author: claude-code
date: '2026-10-29'
last_review: '2026-10-29'
next_review: '2027-01-27'
prelude: What the slash-command drift gate (tests/arch/test_claude_command_references.py, PRs #1445 and #1462) checks in .claude/commands, how to run it, how to fix each finding, and what must never be allowlisted.
---
# Slash Command Drift Gate

This page describes a gate that is **not merged yet**. Everything below was read from the two open PR branches, not from `main`. When the PRs merge, line numbers will shift; re-anchor then.

Anchor notation used throughout: `A:` is `origin/fix/cmd-repair-001` at `77940fdca` (PR #1445), `B:` is `origin/followup/zen-prose-gate` at `9b716f948` (PR #1462), `M:` is `origin/main` at `93050d135`. `path:N` means line N of that path at that ref, read with `git show <ref>:<path>`.

## 1. Status

| Item | PR #1445 | PR #1462 |
|---|---|---|
| Title | fix(commands): repair dead ConPort names, stale pins and dead targets; add drift gate | fix(commands): retire dead zen commands; enable /mcp prose scan in the drift gate |
| Head branch | `fix/cmd-repair-001` | `followup/zen-prose-gate` |
| Base branch | `main` | `fix/cmd-repair-001` |
| State | OPEN, not merged (`mergedAt` null) | OPEN, not merged (`mergedAt` null) |
| GitHub merge state | `BEHIND` main, mergeable | `CLEAN`, mergeable |
| Review decision | none recorded | none recorded |
| Files / commits (GitHub) | 87 files / 21 commits | 18 files / 7 commits |

**Relationship: stacked, but #1462 is built on an older #1445 head.** #1462's base is `fix/cmd-repair-001`, and its description says to merge #1445 first. `git merge-base origin/fix/cmd-repair-001 origin/followup/zen-prose-gate` is `f082007ff`, and `git merge-base --is-ancestor` of the #1445 head into #1462 returns 1 (not an ancestor). #1445 has 7 newer commits (`77940fdca` back to `8144c5ca0`) that are all under `proof/`, and #1462 has 7 commits of its own. The two PRs do not touch the same non-proof files except through the stack: #1462 edits `tests/arch/test_claude_command_references.py`, `dx/implement.md` and `dx/note.md`, which #1445 also edits, so merge #1445 first.

The finished gate (both PRs applied) is the one in `B:tests/arch/test_claude_command_references.py`. Where #1445 alone differs, this page says so.

Last CI read (`gh pr checks`): #1462 shows PR Steward final readiness, `independent embedded audit`, `Unit Tests`, and the rest passing, with Integration, Installer Smoke and Scoped Coverage skipped. None of those jobs runs the gate itself (see section 4).

## 2. What drift the gate detects

The gate scans every `*.md` under `.claude/commands/`, recursively (`B:tests/arch/test_claude_command_references.py:26` sets `COMMANDS_DIR`; `:64-65` is `_command_files`, an `rglob("*.md")`). It reads files only and has no network or service dependency (docstring, `B:...:3`). It does not scan `.claude/agents/`, `.claude/modules/`, or anything outside `.claude/commands/`.

There are four checks in the test module, plus a second, older gate in `fleet_catalog.py`.

### 2.1 Dead ConPort tool names, and any other uncaptured MCP tool (`check_mcp_tool_refs`)

| Item | Detail | Anchor |
|---|---|---|
| Function | `check_mcp_tool_refs(commands_dir, repo_root)` | `B:...:104-114` |
| Pattern (underscore form) | `mcp__<server>__<tool>`: server `[A-Za-z0-9-]+(?:_[A-Za-z0-9-]+)*?`, tool `[A-Za-z0-9_*-]+` | `B:...:51-53` |
| Pattern (prose form, new in #1462) | `/mcp <server> <tool>`, not preceded by a word character or `/` | `B:...:55-57` |
| Both forms scanned on every line | `_mcp_refs` runs both regexes per line | `B:...:68-76` |
| Data source | `mcp_tool_surfaces.json` at the repo root, key `servers` | `B:...:79-81` |
| Which servers are checked | Only servers whose `source` is `live` or `seed` and whose `tools` map is non-empty | `B:...:45` (`_CAPTURED_SOURCES`), `:84-91` |
| Rule | If the server is captured and the tool is not in its list, report a violation. A bare `*` tool is skipped here | `B:...:107-113` |
| Message | `<file relative to commands/>:<line>: mcp__<server>__<tool> is not a <server> tool` | `B:...:111-113` |

This is the check that catches dead ConPort names. The live ConPort list in `M:mcp_tool_surfaces.json:15-20` is 17 tools (`source: live`, endpoint `http://localhost:3005/sse`, captured `2026-07-16T23:39:38Z`): `delete_custom_data`, `fork_instance`, `get_active_work`, `get_context`, `get_custom_data`, `get_decisions`, `get_progress`, `get_recent_activity`, `log_decision`, `log_progress`, `promote`, `promote_all`, `save_custom_data`, `search_content`, `update_context`, `update_progress`, `workspace_summary`. Anything else after `mcp__conport__`, including the old `conport_`-prefixed names and the FTS tools, is reported. The gate has no hard-coded list of "dead names"; a name is dead because it is absent from the captured list.

Captured servers on `main` (from the same JSON): `conport` (live, 17), `desktop-commander` (live, 4), `dope-context` (live, 18), `dope-memory` (live, 10), `task-orchestrator` (live, 14), `serena` (seed, 27), `github-official` (seed, 12). Tool names on these servers are verified. For all other servers the tool name is not verified.

Behaviours that follow from the regexes (confirmed by running the helper functions on a synthetic file in a scratch export, not in the repo):

- Any `/mcp <word> <word>` in prose is parsed as server and tool. The line `Run /mcp status now.` produced the server `status` and the violation `unknown MCP server 'status'`. Avoid writing `/mcp` followed by two words unless you mean a server and tool.
- A malformed tool token is reported whole instead of being truncated to a valid prefix. `get_context--bad` and `*bad` are reported (`B:...:46-50` comment, tests at `:381-395`).
- `mcp__<server>__*` is not tool-checked, only server-checked (`B:...:108-109`).

### 2.2 Dead targets, part 1: unknown MCP servers (`check_mcp_servers`)

| Item | Detail | Anchor |
|---|---|---|
| Function | `check_mcp_servers(commands_dir, repo_root, unverified=UNVERIFIED_SERVERS)` | `B:...:117-140` |
| Known servers | Union of the keys of `mcp_tool_surfaces.json` `servers`, `mcp_catalog.yaml` `servers`, and `.mcp.json` `mcpServers` | `B:...:94-101`; `M:mcp_catalog.yaml:168`; `M:.mcp.json:2` |
| Unknown server rule | A referenced server (wildcard references included) that is not known is a violation | `B:...:126-129` |
| Message | `<file>:<line>: unknown MCP server '<server>'` | `B:...:129` |

This is what flags a server that does not exist, such as `task-master-ai`, `zen`, or `serena-v2`.

### 2.3 Unverified-server roster (`UNVERIFIED_SERVERS`)

A server can be known but have no captured tool list (for example stdio servers captured as `unreachable` with zero tools, or servers that are only `planned`). Such servers cannot be tool-checked, so the gate makes you list them on purpose.

| Item | Detail | Anchor |
|---|---|---|
| Constant | `UNVERIFIED_SERVERS = frozenset({"pal-stdio", "gpt-researcher"})` in #1462 (`{"pal", "gpt-researcher"}` in #1445) | `B:...:31`; `A:...:30` |
| Rule 1 | A referenced, known, uncaptured server that is not in the roster is a violation: `server '<s>' lacks a captured tool list: UNVERIFIED_SERVERS` | `B:...:130-134` |
| Rule 2 | A roster entry that is no longer referenced, or has since become captured, is a violation: `UNVERIFIED_SERVERS entry '<s>' is not referenced or is now verifiable` | `B:...:135-139` |

Consequence: the roster must match the commands exactly. If you remove the last reference to `gpt-researcher` from every command, the gate fails until you also remove it from the roster. In #1462 a lingering `mcp__pal__*` reference fails Rule 1, because `pal` is a known server (`unreachable`, no tools) that is not on the roster; this is how the `pal` to `pal-stdio` rename is enforced.

### 2.4 Stale pins (`check_model_pins`)

| Item | Detail | Anchor |
|---|---|---|
| Function | `check_model_pins(commands_dir)` | `B:...:154-167` |
| What it reads | Only `model:` lines inside the leading `---` frontmatter block | `B:...:61` (`_MODEL_LINE`), `:143-151` |
| Allowed values | `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`, `opus`, `sonnet`, `haiku`, `inherit` | `B:...:33-43` |
| Rule | Value (surrounding quotes stripped) not in the set is a violation: `<file>:<line>: model '<value>' is not allowed` | `B:...:163-166` |

A file with no leading `---` block, or a `model:` line outside it, is not checked. Dated IDs such as `claude-sonnet-4-20250514` are rejected because only the exact strings above pass.

### 2.5 Dead targets, part 2: missing scripts (`check_script_refs`)

| Item | Detail | Anchor |
|---|---|---|
| Function | `check_script_refs(commands_dir, repo_root)` | `B:...:170-181` |
| Pattern | `scripts/<chars>.py` or `.sh`, optionally prefixed `./`, and not preceded by `[\w/.-]` | `B:...:58-60` |
| Rule | `repo_root / <match>` must be an existing file; otherwise `<file>:<line>: <path> does not exist` | `B:...:176-180` |

Only repo-root `scripts/` paths are checked. `foo/scripts/x.py` and `xscripts/a.py` are ignored on purpose (test at `B:...:342-345`). Only `.py` and `.sh` extensions are matched. The gate checks that the file exists, not that it works or accepts the arguments the command passes.

### 2.6 Retired zen commands

There is no separate "zen" rule. The two commands `zen` and `zen-continue` called `/mcp zen execute_workflow ...`, a server named `zen` that exists nowhere. #1445 could not scan that prose form without flagging them (its own note at `A:...:49-51` says so). #1462 deletes the two files and turns the prose scan on, so any future `/mcp zen ...` or `mcp__zen__...` is reported by the unknown-server rule in 2.2. The negative control that pins this is `B:...:360-365` (`/mcp zen execute_workflow {}` must report `unknown MCP server 'zen'`).

### 2.7 The `/mcp` prose scan (added by #1462)

The prose regex at `B:...:55-57` and the second loop in `_mcp_refs` (`B:...:74-76`) are the whole change in the scanner. In #1445 the scanner has only the underscore form (`A:...:47-48`, `:62-69`). The prose form feeds both 2.1 and 2.2. A prose violation is worded in the underscore style: the test at `B:...:351-357` expects `mcp__conport__no_such_tool` for the input `/mcp conport no_such_tool {}`. The scan ignores `/mcp` embedded in a path, for example `docs/mcp zen thing` (`B:...:375-378`).

The #1462 audit left three LOW findings unrepaired (per the PR body): the prose lookbehind omits `.` and `-`, `_MCP_REF` has no leading boundary, and two prose tests would pass if the scan were a no-op.

### 2.8 The older gate: `find_unknown_command_tool_surfaces`

This predates the PRs and is a separate check over the same files.

| Item | Detail | Anchor |
|---|---|---|
| Function | `find_unknown_command_tool_surfaces(command_dir, catalog)` | `A:src/dopemux/mcp/fleet_catalog.py:859-874` |
| Regex | `\bmcp__([A-Za-z0-9_-]+)__([A-Za-z0-9_-]+\|\*)` | `A:...:31` |
| Server rule | Surface not in the catalog servers or `tool_aliases` is reported as `<path>:<line>:<surface>` | `A:...:844-848`, `:868-870` |
| Tool rule | Only for `conport`, against a static snapshot | `A:...:60` (`_MCP_TOOL_SNAPSHOTS`), `:871-873` |
| Snapshot | `_CONPORT_TOOL_SNAPSHOT`: the same 17 live SSE tool names | `A:...:34-59` |
| Tests | `test_claude_command_tool_surfaces_are_catalog_known_or_explicit_aliases` and two negative controls | `A:tests/arch/test_mcp_fleet_catalog_contract.py:344-372` |

On `main` this snapshot held the old `conport_*` names (the JSON-RPC dispatch map), so it checked commands against the wrong surface. #1445 replaces it with the 17 live names (diff of `src/dopemux/mcp/fleet_catalog.py`, 42 lines changed). The two gates now agree on ConPort, but they keep separate data: the snapshot is a hard-coded constant, the new gate reads `mcp_tool_surfaces.json`. If you change the ConPort tool list you must update both.

### 2.9 A related existing hook (not part of the PRs)

`M:.pre-commit-config.yaml:41-46` runs `scripts/validate_memory_command_refs.py` on `.claude/commands/*.md`. It rejects references to deprecated memory backends (`openmemory`, `memory_bank`, `mem0`, `/mcp memory`, `Claude-Context`), skipping lines that contain "deprecated" or "do not use" (`M:scripts/validate_memory_command_refs.py:10-13`, `:24-25`). It is independent of the drift gate.

## 3. How to run it

### 3.1 Command

The gate is an ordinary pytest module; there is no standalone CLI and no flags of its own.

```bash
cd <repo-root>
uv run --frozen --extra test pytest tests/arch/test_claude_command_references.py
```

This follows the Makefile pattern (`M:Makefile:61-62`, `uv run --frozen --extra test pytest tests`). `pytest.ini` applies `--strict-markers`, `--strict-config` and `--import-mode=importlib` (`M:pytest.ini:13-17`). To run the older ConPort-snapshot gate as well:

```bash
uv run --frozen --extra test pytest tests/arch/test_mcp_fleet_catalog_contract.py -k command_tool_surfaces
```

`make test-unit` and `make test-fast` do not run it: they target `tests/unit` only (`M:Makefile:64-65`, `:75-76`). `make test` does, because `testpaths = tests` (`M:pytest.ini:18`) and the module sits in `tests/arch/`.

### 3.2 Exit codes and output

Standard pytest: exit 0 when every test passes, exit 1 when any test fails. The module has 4 real-repo tests (`B:...:198-211`) and, in #1462, 25 tests in total (18 in #1445). Each real-repo test asserts that its check returns `[]`, so a failure prints the list of violation strings. Each string starts with a path relative to `.claude/commands/`, a line number, then the message from section 2:

```
caveat.md:3: mcp__conport__conport_save_custom_data is not a conport tool
ctx/index-search.md:12: model 'claude-sonnet-4-5' is not allowed
adr-new.md:9: scripts/adr_new.py does not exist
zen-continue.md:2: unknown MCP server 'zen'
```

(These four lines are real outputs from running the checks against an export of `main`'s commands; see section 3.3.) The roster violations (`server '<s>' lacks ...`, `UNVERIFIED_SERVERS entry ...`) carry no file or line, because they describe the set of references, not one line.

### 3.3 What was run for this page

| Run | Result |
|---|---|
| `B` test file against `B` commands, exported with `git archive` to a scratch directory, `pytest -c /dev/null --noconftest` | PASS, 25 passed |
| `A` test file against `A` commands, same method | PASS, 18 passed |
| `B` test file against `M` commands, same method | FAIL as expected: 4 of the real-repo tests fail, 21 pass |
| Check functions counted against `M` commands, `B` file | tool refs 26, servers 5, model pins 26, scripts 4 |
| Check functions counted against `M` commands, `A` file | tool refs 25, servers 0, model pins 26, scripts 4 |

These ran on exported copies in a scratch directory, never in the repo and never on a checked-out branch. They used the repo `.venv` Python but not the repo's `pytest.ini`, `conftest.py` files, or `uv`. The command in 3.1, run inside a checkout with the repo config, is **NOT_RUN**. The `A` counts of 25 / 26 / 4 match the PR #1445 description; the `B` counts differ because #1462 adds the prose scan and tightens the regexes.

### 3.4 Where it is wired

| Mechanism | Wired? | Evidence |
|---|---|---|
| pytest | Yes. Collected by any run that includes `tests/arch`, including `make test` | `M:pytest.ini:18`, `M:Makefile:61-62` |
| Makefile target of its own | No | No `tests/arch` match in `Makefile` at `A` |
| pre-commit | No hook for it | `M:.pre-commit-config.yaml` has only the memory-refs hook for commands (`:41-46`); no `tests/arch` match at `A` |
| GitHub Actions | No step found | In `M:.github/workflows/ci-complete.yml` the Unit Tests job runs `tests/unit`, `tests/test_voice_core.py`, `tests/test_brand_voice.py` (`:186-190`) and `tests/dcp/` (`:203-206`); a grep of `M:.github` for `tests/arch` returned nothing, and no workflow at `A` adds one |

So nothing in CI or pre-commit runs this gate today. It protects the commands only when a person or agent runs it. Treat "CI is green" as no evidence about command drift.

## 4. How to fix each class of finding

Always fix the command file. Do not edit the data files or the test to make a finding disappear (section 7).

| Finding | What to change | Worked example from the diff |
|---|---|---|
| `mcp__conport__X is not a conport tool` | Use a live name from the 17 above and the argument shape the live tool takes. If the tool does not exist, change the workflow, not the name. | `decision.md`: `mcp__conport__conport_log_decision` became `mcp__conport__log_decision`, and the argument `summary` became `topic` and `decision` (`A:.claude/commands/decision.md:3`). Dead FTS tools: `search_decisions_fts` became `search_content`, which has no `limit`, so `bootstrap.md` now says to read only the top 3-5 results; caveats are read with `get_custom_data` with `category: "caveats"` because `search_content` does not cover custom data |
| `unknown MCP server 'X'` | Point at a server that exists in `mcp_tool_surfaces.json`, `mcp_catalog.yaml` or `.mcp.json`, or remove the call and say the capability is unavailable. | `plan.md`: `Use sequential_thinking ...` became `Use the PAL planner tool (MCP server pal-stdio) ...`. `zen.md` and `zen-continue.md` could not be repointed (PAL has no `execute_workflow` tool), so #1462 deletes them. Dead-name table: `B:docs/02-how-to/mcp-integration-guide.md:156-163` |
| `mcp__pal__*` after #1462 | Rename to `mcp__pal-stdio__*` (PAL was renamed; the roster entry is `pal-stdio`) | `dx/implement.md` allowed-tools lines 8-9 and `dx/note.md:48` (`B:` paths), 4 lines total |
| `server 'X' lacks a captured tool list: UNVERIFIED_SERVERS` | Only if the reference is correct: add the server to `UNVERIFIED_SERVERS` in the test, in the same change, with a reason in the commit message. Otherwise remove the reference. | The roster itself (`B:...:28-31`) is the example: `pal-stdio` and `gpt-researcher` |
| `UNVERIFIED_SERVERS entry 'X' is not referenced or is now verifiable` | Remove the entry from the roster. If the server now has a captured list, tool names are checked instead. | Pins the rule in the test at `B:...:244-252` |
| `model 'X' is not allowed` | Use one of the seven allowed values. Keep the tier (haiku stays haiku). One `model:` line per file. | 26 files: `dx/start.md:9` `model: "claude-sonnet-4-5"` became `model: "claude-sonnet-5-5"`. Counted from the diff: 24 `claude-sonnet-4-5`, 1 `claude-sonnet-4-5-20250929`, 1 `claude-haiku-4-5-20251001` removed; 25 `claude-sonnet-5-5` and 1 `claude-haiku-5-5` added |
| `scripts/X does not exist` | Point at a script that exists, or delete the instruction and add an "unavailable" note. Do not create an empty script to satisfy the gate. | `safe.md`: the `./scripts/set-profile.sh set dangerous` block was replaced by "A profile-switching script for safe/dangerous mode is unavailable ..."; `adr-new.md` lost `scripts/adr_new.py` and `scripts/docs_manifest.py` with an "unavailable" note |

Two repairs were not simple renames, and the PR descriptions flag them as behaviour changes to review: `followup.md` can no longer link a custom_data item, because the live `log_progress` only links decisions, so the slug rides in the description; and the merge-versus-replace semantics of `update_context` are UNKNOWN.

## 5. What the PRs repaired

Counted from `git diff --stat` and `--name-status` of `origin/main...<branch>`.

| Scope | PR #1445 | PR #1462 (on top of #1445's older head) |
|---|---|---|
| Command files modified | 46 | 2 (`dx/implement.md`, `dx/note.md`) |
| Command files deleted | 0 | 2 |
| Command files added | 0 | 0 |
| Other non-proof files | `src/dopemux/mcp/fleet_catalog.py` (modified), `tests/arch/test_claude_command_references.py` (added, 334 lines) | `tests/arch/test_claude_command_references.py` (107 lines changed), `docs/02-how-to/mcp-integration-guide.md` (19 lines changed) |
| Proof-only files | the rest of the 87 | the rest of the 18 |
| Command files in tree after the PR | 75 (same as `main`) | 73 (`main` has 75) |

Categories in #1445, from its description and cross-checked against the diff:

| Category | Files (per PR description) | Cross-check from the diff |
|---|---|---|
| Live ConPort names and argument shapes, FTS replaced (W01) | 18 | 14 files had a removed line containing `conport_`; the other W01 files changed FTS names and arguments |
| Stale model pins to Claude 5.5 IDs (W02) | 26 | 26 `model:` lines changed |
| Dead script or tool targets (W03) | 5 | `adr_new.py` and `docs_manifest.py` (`adr-new.md`), `docs_manifest.py` (`doc-new.md`), `set-profile.sh` (`safe.md`), `sequential_thinking` (`plan.md`), `task-master-ai` (`plan-tasks.md`) |
| The gate itself (W04) | 1 | `tests/arch/test_claude_command_references.py` added |
| Fleet snapshot (W05) | 1 | `fleet_catalog.py` `_CONPORT_TOOL_SNAPSHOT` now the 17 live names |
| Audit-1 fixes (W06) | 4 | not separately countable from the squash-level diff |

**Retired commands (#1462), exactly:** `.claude/commands/zen.md` and `.claude/commands/zen-continue.md`, that is the slash commands `/zen` and `/zen-continue`.

## 6. Allowlists and exemptions

The gate has exactly two knobs. Both are constants in the test file.

| Knob | Location | Meaning | Add an entry when |
|---|---|---|---|
| `UNVERIFIED_SERVERS` | `B:...:28-31` | Known servers whose tool names cannot be verified because no live or seed tool list exists | A command legitimately references a real server that has no captured tool list |
| `ALLOWED_COMMAND_MODELS` | `B:...:33-43` | Permitted `model:` frontmatter values | A new Claude model ID is adopted for commands, as a deliberate repo-wide decision |

How to add one correctly:

1. Prove the server or model is real first: for a server, it is in `mcp_catalog.yaml`, `.mcp.json` or the snapshot, and the thing you call exists in its source; for a model, it is a current ID.
2. Edit the constant in `tests/arch/test_claude_command_references.py` and the command in the same commit, so the tree is never red in between.
3. State the reason in the commit message. Keep the roster minimal: the gate itself fails on an entry nothing references.
4. If the server later gets a live or seed capture in `mcp_tool_surfaces.json`, remove its roster entry; the gate will demand it (Rule 2 in 2.3).

There is no per-file or per-line exemption mechanism and no inline "ignore" marker. Do not invent one.

**Do not allowlist:**

- A name that does not exist on the server. The fix for a dead tool is a live tool or a rewritten workflow, never a roster entry (a roster entry only waives tool checking for servers that have no tool list).
- A nonexistent server (`zen`, `task-master-ai`, `serena-v2`). Remove the reference.
- A stale or dated model ID. Re-pin to an allowed value.
- A missing script. Do not add a stub file only so the path resolves.
- Anything by editing `mcp_tool_surfaces.json`, `mcp_catalog.yaml` or `.mcp.json` to add a fake entry or fake tool. Those are captured or generated data; the live ConPort list comes from a real capture (`M:mcp_tool_surfaces.json:15-20`).

## 7. How an agent should use it

1. **When to run it.** After any edit under `.claude/commands/`, and before claiming a command change is done. Also after changing `mcp_tool_surfaces.json`, `mcp_catalog.yaml`, `.mcp.json`, the ConPort tool list, or `fleet_catalog.py`, since those are the gate's data sources. Run the pre-commit memory-refs hook too (`scripts/validate_memory_command_refs.py`).
2. **Which command.** The pytest line in 3.1. Because CI does not run it, a green PR does not mean the commands are clean.
3. **Reading a failure.** Take the path and line from the violation string and open that file under `.claude/commands/`. Match the message to the table in section 4. Roster messages have no line: compare the set of referenced servers with `UNVERIFIED_SERVERS`.
4. **After fixing.** Re-run the whole module, not only the failing test; a fix can make a roster entry stale.
5. **Report states literally.** If you could not run it, say NOT_RUN; do not report PASS from reading the code.

What not to do:

- Do not weaken the gate to pass it: do not loosen a regex, widen `ALLOWED_COMMAND_MODELS`, add to `UNVERIFIED_SERVERS` to silence a real error, delete a negative control, or mark a test skip or xfail.
- Do not hand-edit the data files to add the tool you wish existed.
- Do not "fix" a prose false positive by deleting the line without checking: if `/mcp <word> <word>` appears in explanatory text, reword it.
- Do not leave a command calling a capability that does not exist. Say it is unavailable, as the repairs did.
- Do not treat the `pal` versus `pal-stdio` naming as settled: #1445 left it as a known inconsistency and #1462 moves the roster to `pal-stdio`.

## 8. Source map

Paths in the middle column are given in full once; `...` stands for `tests/arch/test_claude_command_references.py`.

| Fact | Ref and anchor |
|---|---|
| PR states, bases, files, commits, merge state | `gh pr view 1445`, `gh pr view 1462` (live read, 2026-10-29) |
| Stack relationship, 7 newer #1445 commits | `git merge-base`, `git merge-base --is-ancestor`, `git log` between the two branches |
| `COMMANDS_DIR`, scan root | `B:...:26` |
| `UNVERIFIED_SERVERS` (#1462 / #1445) | `B:...:31` / `A:...:30` |
| `ALLOWED_COMMAND_MODELS` | `B:...:33-43` |
| Captured sources `live` and `seed` | `B:...:45` |
| `_MCP_TOOL`, `_MCP_SERVER`, `_MCP_REF` | `B:...:51-53` (#1445: `A:...:47-48`) |
| `_MCP_PROSE_REF` | `B:...:55-57` |
| `_SCRIPT_REF`, `_MODEL_LINE` | `B:...:58-61` |
| `_command_files`, `_mcp_refs` | `B:...:64-76` |
| `_surface_servers`, `_captured_tools`, `_known_servers` | `B:...:79-101` |
| `check_mcp_tool_refs` | `B:...:104-114` |
| `check_mcp_servers` | `B:...:117-140` |
| `_frontmatter_lines`, `check_model_pins` | `B:...:143-167` |
| `check_script_refs` | `B:...:170-181` |
| Real-repo tests | `B:...:198-211` |
| Prose and regex-edge controls | `B:...:348-403` |
| Prose-form limit note in #1445 | `A:...:49-51` |
| ConPort live tool list (17) | `M:mcp_tool_surfaces.json:15-20` |
| `servers:` key in catalog, `mcpServers` key | `M:mcp_catalog.yaml:168`, `M:.mcp.json:2` |
| Old gate: regex, snapshot, finder, tests | `A:src/dopemux/mcp/fleet_catalog.py:31`, `:34-60`, `:844-874`; `A:tests/arch/test_mcp_fleet_catalog_contract.py:344-372` |
| Dead-name table and gate-coverage paragraph | `B:docs/02-how-to/mcp-integration-guide.md:156-175` |
| `make test`, `test-unit`, `test-fast` | `M:Makefile:61-62`, `:64-65`, `:75-76` |
| `testpaths`, strict markers, importlib mode | `M:pytest.ini:18`, `:13-17` |
| Pre-commit memory-refs hook and its patterns | `M:.pre-commit-config.yaml:41-46`; `M:scripts/validate_memory_command_refs.py:10-13`, `:24-25` |
| CI unit job test paths | `M:.github/workflows/ci-complete.yml:186-190`, `:203-206` |
| Worked-example command lines | `A:.claude/commands/decision.md:3`, `A:.claude/commands/dx/start.md:9`, `B:.claude/commands/dx/implement.md:8-9`, `B:.claude/commands/dx/note.md:48` |
| Retired files | `git diff --name-status origin/fix/cmd-repair-001...origin/followup/zen-prose-gate` (status `D` for `zen.md`, `zen-continue.md`) |

## 9. Discrepancies

Places where a PR description disagrees with the branch it describes. None of them changes what the gate checks.

1. **#1445 says `PROOF.json.sig` is absent** and that the repo's proof-only closure check fails on exactly that gate. The branch now contains `proof/MACRO-DMX-CMD-REPAIR-001/PROOF.json.sig` and `proof/pr_merge/embedded-audit/pr-1445/PROOF.json.sig`, added by the 7 proof-only commits that postdate the description. The description is stale.
2. **#1462 says "CI will show `independent embedded audit` red until a signed per-PR attestation is added"** and that it has no `PROOF.json` or `AUDITOR_REPORT.md`. The branch contains `proof/MACRO-DMX-CMD-REPAIR-002/{AUDITOR_REPORT.md,PROOF.json,PROOF.json.sig}` and `proof/pr_merge/embedded-audit/pr-1462/PROOF.json(.sig)`, and `gh pr checks 1462` shows `independent embedded audit` passing. Stale.
3. **#1462 says "this PR's 4 commits"**; GitHub and `git log` show 7 (the 4 listed in the description plus 3 later proof commits).
4. **#1462 is described as stacked on #1445, but it is built on `f082007ff`, not on the current #1445 head** `77940fdca`. #1445 has 7 newer proof-only commits that #1462 does not contain. Not a code conflict, but a rebase or retarget may be needed.
5. **#1445's "known limits" say the gate does not scan `/mcp <server> <tool>`** and the integration guide is stale. True for #1445 alone (`A:...:49-51`); both are addressed by #1462. Not an error, but anyone reading only #1445 will get an out-of-date picture.

The "202 passed" (#1445) and "209 passed" (#1462) test counts are consistent with the test functions found (18 and 25, with 202 + 7 = 209); I did not re-run the full `tests/arch` directory, so those totals are NOT_RUN here.
