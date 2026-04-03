---
id: SYSTEM_Dopetask
title: System Dopetask
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: System Dopetask (reference) for dopemux documentation and developer workflows.
---
### 1. Purpose

`dopetask` is an external task-execution CLI that this repository installs into a dedicated virtual environment and invokes through wrapper scripts. In this checkout, `dopemux` delegates all kernel execution to it: `dopemux` forwards kernel commands into `scripts/taskx`, which is only a compatibility shim for `scripts/dopetask`, which then execs the `dopetask` binary installed into the pinned virtual environment. `dopetask` does not own dopemux CLI orchestration, PM truth, memory truth, retrieval truth, MCP startup, or routing decisions.

### 2. Core Responsibilities

- Task packet execution.
  Observed: the live `dopetask 0.5.1` help describes itself as a "Minimal Task Packet Lifecycle CLI"; top-level commands include `tp`; versioned `0.5.1` fixtures show `dopetask tp run`, `dopetask tp exec`, and `dopetask tp series exec`, with `tp series exec` taking a required `TP_FILE` argument.

- dopemux-integrated lifecycle execution for compile, run, collect, gate, promote, feedback, loop, and doctor.
  Observed: `src/dopemux/commands/kernel_commands.py` maps `dopemux kernel compile|run|collect|gate|promote|feedback|loop` to `scripts/taskx` with base args `["dopemux", <stage>]`, and maps `dopemux kernel doctor` to `scripts/taskx doctor`. Live help from `./scripts/dopetask dopemux --help` exposes `compile`, `run`, `collect`, `gate`, `promote`, `feedback`, and `loop`; live help from `./scripts/dopetask --help` exposes `doctor`.

- Task/task-packet workflow execution defined outside the `dopemux` Python package.
  Observed: live `dopetask` help exposes top-level commands such as `compile-tasks`, `run-task`, `collect-evidence`, `gate-allowlist`, `promote-run`, `spec-feedback`, and `loop`. Older repo docs mention `plan.yaml` examples, but direct proof of current `plan.yaml` handling from the pinned binary in this checkout is `UNKNOWN`.

- Execution of workflows defined outside the `dopemux` Python package.
  Observed: `scripts/dopetask` installs `dopetask==0.5.1` from `.dopetask-pin` into `.dopetask_venv` and then `exec`s `$VENV/bin/dopetask "$@"`; `pyproject.toml` declares `dopetask==0.5.1` as a dependency, but the runtime binary is not implemented under `src/dopemux/*`.

- Environment-isolated execution via `.dopetask_venv`.
  Observed: `scripts/dopetask` creates and manages `REPO_ROOT/.dopetask_venv`, records the installed version in `.dopetask_venv/.dopetask_version`, reinstalls on version drift, and activates that venv before `exec`. `tests/unit/test_dopetask_wrapper_submodule.py` verifies missing pin/root refusal, ready-venv execution, and reinstall on version drift.

### 3. Non-Responsibilities

- CLI orchestration layer.
  Observed: `dopemux` owns the operator CLI surface in `src/dopemux/cli.py` and `src/dopemux/commands/kernel_commands.py`; `dopetask` is invoked behind that layer.

- PM authority.
  Observed: repo guidance and `src/dopemux/pm/writes.py` place PM writes across Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts. `dopetask` is not the PM system of record.

- Memory authority.
  Observed: repo truth identifies dope-memory as the durable memory sink and ConPort as structured memory/retrieval. No inspected `dopetask` wrapper surface in this repo makes it memory authority.

- Retrieval authority.
  Observed: retrieval surfaces are handled by dope-context and ConPort, not by the inspected `dopetask` wrapper chain.

- MCP lifecycle.
  Observed: MCP startup and shutdown are owned by dopemux command code and service wiring, not by `scripts/dopetask` or the observed `dopetask` invocation path.

- Routing layer.
  Observed: routing mode and router service control live under dopemux routing commands and configs, not under the `dopetask` wrapper chain.

- Canonical state or artifact authority.
  Observed: `dopetask` help and wrapper behavior show filesystem outputs such as `out/tasks`, task queue files, and run workspaces, but no inspected authority source shows `dopetask` as system-of-record for PM state, memory state, or durable canonical system state.

### 4. Execution Path

The observed invocation chain is:

`dopemux CLI` -> `src/dopemux/commands/kernel_commands.py` -> `scripts/taskx` -> `scripts/dopetask` -> `.dopetask_venv/bin/dopetask`

`scripts/taskx` is only a compatibility shim. Its entire runtime behavior is `exec .../dopetask "$@"` with a comment stating it exists during the `taskx -> dopetask` transition. `scripts/dopetask` is the real bootstrapper: it verifies `.dopetaskroot` and `.dopetask-pin`, parses install method, dependency name, and version, creates `.dopetask_venv` if needed, installs or reinstalls the pinned external package, activates the venv, and `exec`s the binary from that venv. Execution therefore happens outside the `dopemux` Python package and outside any `dopetask` source tree in this repository.

### 5. Key Surfaces

- `scripts/dopetask`
  Primary runtime entry. Observed responsibilities: repo-root guardrails, pin parsing, venv creation, pinned install, version drift correction, `doctor` special-case hinting, final `exec`.

- `scripts/taskx`
  Compatibility shim only. Observed behavior: `exec "$(…)/dopetask" "$@"`.

- `.dopetask-pin`
  Version/install authority for the wrapper. Observed contents in this checkout: `install=pip`, `dep=dopetask`, `version=0.5.1`.

- `dopetask` CLI commands that are directly observable in this repo
  Observed from live `--help` and versioned fixtures: `compile-tasks`, `run-task`, `collect-evidence`, `gate-allowlist`, `promote-run`, `commit-run`, `spec-feedback`, `loop`, `doctor`, `tp`, `dopemux`, and others. For dopemux-integrated subcommands, the observed surface is `dopetask dopemux compile|run|collect|gate|promote|feedback|loop`.

- Plan/task inputs
  Directly observed current inputs are task-oriented surfaces such as `--task-id` and `TP_FILE`. Older docs mention `plan.yaml`, `execute --plan=plan.yaml`, and `validate --plan=plan.yaml`, but those flags were not present in the observed `0.5.1` top-level help. Current `plan.yaml` support is therefore `UNKNOWN` from repo-truth in this checkout.

### 6. System Boundaries

- `dopemux`
  What dopetask receives: subprocess arguments from `dopemux kernel` delegation, passed through `scripts/taskx` and `scripts/dopetask`.
  What dopetask outputs: process stdout/stderr and exit status; `kernel_commands.py` directly observes and propagates return codes.
  What dopetask does not control: dopemux command registration, MCP startup, routing mode, workspace startup behavior, or PM write routing.

- `task-orchestrator`
  Observable interaction in this checkout: none directly from the inspected wrapper and delegation code.
  What dopetask receives/outputs relative to task-orchestrator: `UNKNOWN` from the authoritative sources inspected for this document.
  What dopetask does not control: task-orchestrator runtime packaging, API, and PM workflow authority.

- Filesystem
  What dopetask receives: repository root, `.dopetaskroot`, `.dopetask-pin`, venv path, and command-specific file/path arguments such as `TP_FILE`; live help also shows output-oriented directories like `out/tasks` defaults on `compile-tasks` and `task_queue.json` defaults on `run-task`.
  What dopetask outputs: files and run workspaces implied by command help such as compiled task outputs and run workspaces. Exact artifact schema is not proven from the wrapper alone.
  What this repo does not prove: dopetask defines artifact shape operationally, but not canonically within this repo.
  What dopetask does not control: canonical PM data stores, dopemux config stores, or MCP service data planes.

- Environment
  What dopetask receives: an isolated Python virtual environment under `.dopetask_venv` plus any shell environment inherited by the wrapper.
  What dopetask outputs: an installed binary and version marker inside `.dopetask_venv`; runtime side effects beyond that depend on subcommand and are only partially observable from help text.
  What dopetask does not control: the broader dopemux package environment, beyond whatever arguments/environment are passed into the subprocess.

### 7. Authority Model

- `dopetask` is authoritative for task execution behavior once control has passed into the external binary.
- `dopetask` is not authoritative for PM truth.
- `dopetask` is not authoritative for memory.
- `dopetask` is not authoritative for routing.
- `dopetask` is not authoritative for orchestration; `dopemux` owns the CLI orchestration layer in this repo and delegates into `dopetask`.
- Internal `dopetask` implementation behavior beyond the exposed CLI/help, wrapper invocation path, and observed exit-code delegation is `UNKNOWN` from this repository.

### 8. Known Drift / Issues

- TaskX naming still remains as a shim.
  Observed: `scripts/taskx` still exists and `kernel_commands.py` still refers to TaskX even though the script only forwards to `scripts/dopetask`.

- "TaskX" and "dopetask" naming still overlap in commands and docs.
  Observed: `kernel_commands.py` docstrings and labels still say TaskX; README and integration docs describe dopetask; several older docs still show TaskX-era surfaces.

- Installed version and expected behavior can drift if docs lag the pin.
  Observed: `.dopetask-pin`, `pyproject.toml`, live `./scripts/dopetask --version`, and `uv.lock` align on `0.5.1` in this checkout, while older docs and migration notes still mention `0.2.0` and older command names such as `execute` and `validate`.

- `dopemux kernel` naming does not exactly match top-level `dopetask` CLI naming.
  Observed: `dopemux kernel` uses `compile`, `run`, `collect`, `gate`, `promote`, `feedback`, and `loop`; the observed top-level `dopetask` CLI exposes `compile-tasks`, `run-task`, `collect-evidence`, `gate-allowlist`, and `promote-run`, while also exposing a separate `dopemux` subcommand surface. This creates ambiguity about which interface is canonical for a given operation.

- Visibility into dopetask internals is limited from this repo.
  Observed: this repository contains the wrapper, pin, dependency declaration, tests, and some help fixtures, but not the `dopetask` source implementation. Internal storage, internal APIs, and exact execution semantics beyond the visible CLI are therefore only partially knowable here.

### 9. Working Rules

- Treat `dopetask` as an external execution engine, not as code owned by `dopemux`.
- Verify behavior through actual command execution such as `./scripts/dopetask --help`, `./scripts/dopetask --version`, and subcommand help, not by assuming docs are current.
- Do not assume `dopemux` controls execution semantics after it hands off to `dopetask`.
- Trace kernel execution failures into the wrapper chain and the external `dopetask` binary before blaming `dopemux`.
- When behavior is unclear, run `dopetask` directly instead of going through `dopemux` first, so wrapper/delegation issues can be separated from execution-engine issues.
- Treat `TaskX` references as legacy naming unless a runtime path proves otherwise.
