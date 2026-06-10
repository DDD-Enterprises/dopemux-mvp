# No-Write / Static Hazard Review

Static evidence that the facade performs no writes, runs no shell, and constructs no mutating route. Enforced by tests `test_no_filesystem_write_ops_in_facade_source`, `test_no_shell_or_eval_in_facade_source`, `test_no_mutating_http_verbs_in_facade_source`, `test_gitstate_only_runs_read_only_git_verbs` (packet 0008).

## Hazard scan over executable source (`services/dcp-readonly-facade/src`)

```
$ rg -n "write_text|open\(.*['\"]w|mkdir|unlink|remove|rmtree|PUT|PATCH|DELETE|/route/pm|/kg/|/ddg/|index_workspace|clear_index|transition|memory_correct|memory_generate_reflection|subprocess|os.system|shell=True" services/dcp-readonly-facade/src
services/dcp-readonly-facade/src/dcp_facade/task_orchestrator.py:105:    Retrieve workflow state snapshot: phases, stages, allowed transitions, and
services/dcp-readonly-facade/src/dcp_facade/dope_context.py:32:  - index_workspace, index_docs, clear_index (mutating)
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:39:    ("POST", "/tools/memory_correct"),          # dope-memory mutation
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:40:    ("POST", "/tools/memory_generate_reflection"),
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:44:    ("GET", "/ddg/decisions"),                  # dopecon-bridge proxy
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:49:    "memory_correct",
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:50:    "memory_generate_reflection",
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:56:    "/ddg/",
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:57:    "/kg/",
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py:58:    "/route/pm",
services/dcp-readonly-facade/src/dcp_facade/gitstate.py:12:import subprocess
services/dcp-readonly-facade/src/dcp_facade/gitstate.py:29:        result = subprocess.run(  # noqa: S603 - fixed argv, shell=False, no caller input
services/dcp-readonly-facade/src/dcp_facade/gitstate.py:37:    except (OSError, subprocess.SubprocessError):
services/dcp-readonly-facade/src/dcp_facade/tools.py:533:        - workflow transition endpoints (MUTATING)
```

## Classification (every hit is benign)

| Location | Hit | Why benign |
| --- | --- | --- |
| `gitstate.py:12,29,37` | `subprocess` | Read-only git only: fixed argv (`rev-parse`/`status`), `shell=False`, no caller input. Enforced by `test_gitstate_only_runs_read_only_git_verbs`. |
| `route_manifest.py:39-58` | `memory_correct`, `/ddg/`, `/kg/`, `/route/pm`, etc. | Denylist **definitions** — these literals exist so the adapters can deny them. Never used to construct a request. |
| `tools.py:533`, `dope_context.py:32`, `task_orchestrator.py:105` | `transition`, `index_workspace` | Docstrings documenting denied routes / response-schema field names. Not executable. |

No `write_text`/`write_bytes`/`mkdir`/`unlink`/`rmtree`/write-mode `open`/`os.system`/`shell=True`/`.put(`/`.patch(`/`.delete(` appears in any executable path. Confirmed PASS.
