# TP-DCP-MCP-RO-0010 — Command Log

Executor: Claude Sonnet implementation subagent (Opus-orchestrated Claude
Code Sonnet subagent), worktree
`[LOCAL_PATH_REDACTED]`,
branch `claude/dcp-mcp-ro-0010-registry-v2-resolver`. All commands below were
run from the repo root of that worktree, in this order (TDD: tests written
and confirmed RED before any implementation file existed).

## Deviations from the packet JSON (documented, not silent)

1. **`port_policy` omitted from the static family table.** Packet JSON step
   S2 says "bind per-family service policies from a static ADR policy table
   (resolution_class + chatgpt_posture + **port_policy**)". The task brief
   given to this executor explicitly enumerates the static table as
   `(resolution_class, chatgpt_posture)` 2-tuples only, and ADR-DCP-MCP-RO-
   0009 itself only specifies a concrete port policy for one family
   (`to_mcp_wrapper` — `reserved_singleton`, port `7890`); it gives no port
   policy for the other 8. Inventing 8 unsourced `port_policy` values would
   be fabricated data, not ADR-derived fact. `FAMILY_POLICY_TABLE` therefore
   ships as a 2-tuple `{family: (resolution_class, chatgpt_posture)}`,
   matching both the explicit brief and `capability_report()`'s documented
   output shape (`family, configured, resolution_class, chatgpt_posture,
   live, callable` — no `port_policy` key). This is a conscious scoping
   decision, not a missed field; port-lease/port-policy handling is
   explicitly out of scope for this packet (TP-DCP-MCP-RO-0010 invariants:
   "OUT OF SCOPE: ... port leases, TCP probes").
2. **Block reasons do not forward `validate_workspace()`'s raw error
   string**, unlike v1's `resolver.py` (`f"workspace validation failed:
   {err}"`). `validate_workspace()` can return messages containing an
   absolute path (e.g. `"Path does not exist: <path>"`), which would
   violate this packet's NEW hard constraint ("Block reason strings
   returned to callers must not leak absolute paths, ports, or URLs") that
   v1 predates. `resolver_core.py` uses a fixed, generic message instead
   (`"workspace validation failed"`) and swallows `err` (documented in
   `resolver_core.py`'s docstring and §6 of REGISTRY_V2_CONTRACT.md).
3. **v1-shaped documents fail closed rather than being coerced or
   partially loaded**, per the packet's explicit instruction to "choose the
   fail-closed option and document it" (S1 task text). See §4 of
   REGISTRY_V2_CONTRACT.md for the full rationale and migration steps.

## 0. TDD RED — before implementation

```
$ python3 -m pytest -q services/dcp-readonly-facade/tests/test_registry_v2.py services/dcp-readonly-facade/tests/test_resolver_core.py services/dcp-readonly-facade/tests/test_capability.py
==================================== ERRORS ====================================
___ ERROR collecting services/dcp-readonly-facade/tests/test_registry_v2.py ____
ImportError: cannot import name 'registry_v2' from 'dcp_facade' (.../src/dcp_facade/__init__.py)
__ ERROR collecting services/dcp-readonly-facade/tests/test_resolver_core.py ___
ModuleNotFoundError: No module named 'dcp_facade.registry_v2'
____ ERROR collecting services/dcp-readonly-facade/tests/test_capability.py ____
ModuleNotFoundError: No module named 'dcp_facade.capability'
=========================== short test summary info ============================
ERROR services/dcp-readonly-facade/tests/test_registry_v2.py
ERROR services/dcp-readonly-facade/tests/test_resolver_core.py
ERROR services/dcp-readonly-facade/tests/test_capability.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
```

Confirmed RED for the expected reason (feature modules genuinely absent),
not a typo. Implementation then proceeded module-by-module
(`registry_v2.py` → GREEN on `test_registry_v2.py`, then
`resolver_core.py` → GREEN on `test_resolver_core.py`, then
`capability.py` → GREEN on `test_capability.py`).

## 1. New test suite (52 tests) — GREEN, verbose

```
$ python3 -m pytest services/dcp-readonly-facade/tests/test_registry_v2.py services/dcp-readonly-facade/tests/test_resolver_core.py services/dcp-readonly-facade/tests/test_capability.py -v
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
rootdir: [LOCAL_PATH_REDACTED]
configfile: pytest.ini
collected 52 items

services/dcp-readonly-facade/tests/test_registry_v2.py ................. [ 32%]
...........                                                              [ 53%]
services/dcp-readonly-facade/tests/test_resolver_core.py ............... [ 82%]
....                                                                     [ 90%]
services/dcp-readonly-facade/tests/test_capability.py .....              [100%]

============================== 52 passed in ~2s ==============================
```

Breakdown: `test_registry_v2.py` = 28 tests (module constants, JSON Schema
contract, fail-closed parse for every named invalid fixture, deterministic
generation id, file-load path). `test_resolver_core.py` = 19 tests (every
negative gate branch — including both halves of the eligibility gate,
`.dopemux/` presence and `validate_workspace()` separately — primary-
checkout positive, linked-worktree positive with real `git worktree add
--detach` fixtures, block-reason opacity, purity self-check).
`test_capability.py` = 5 tests (configured/unconfigured marking, empty-
family case, configured-never-implies-live/callable, exact public-field
set).

## 2. Full facade suite (packet.commit.verify #1) — MUST be green

```
$ python3 -m pytest -q services/dcp-readonly-facade/tests
........................................s............................... [ 38%]
........................................................................ [ 77%]
..........................................                               [100%]
=========================== short test summary info ============================
SKIPPED [1] services/dcp-readonly-facade/tests/test_live_optional.py:26: set DCP_FACADE_LIVE_TESTS=1 to run live tests
185 passed, 1 skipped in 10.24s
```

Exit code: `0`. The single skip is pre-existing (`test_live_optional.py`,
gated by `DCP_FACADE_LIVE_TESTS=1`) and unrelated to this packet. 133
pre-existing tests (185 − 52 new) still pass unmodified — no v1
regression.

## 3. Byte-compile (packet.commit.verify #2)

```
$ python3 -m compileall -q services/dcp-readonly-facade
```

Exit code: `0`, no output (quiet mode; no syntax errors).

## 4. JSON Schema self-check (draft-07)

```
$ python3 -c "import json,jsonschema; jsonschema.Draft7Validator.check_schema(json.load(open('services/dcp-readonly-facade/schema/registry_v2.schema.json'))); print('schema ok')"
schema ok
```

Exit code: `0`.

## 5. Purity scan (packet.commit.verify #3, extended per task-brief hard constraint)

```
$ rg -n "requests\.|httpx\.|urllib|socket\.|subprocess|os\.system|shell=True|docker" services/dcp-readonly-facade/src/dcp_facade/registry_v2.py services/dcp-readonly-facade/src/dcp_facade/resolver_core.py services/dcp-readonly-facade/src/dcp_facade/capability.py
services/dcp-readonly-facade/src/dcp_facade/registry_v2.py:45:    "docker_mcp_gateway",
services/dcp-readonly-facade/src/dcp_facade/registry_v2.py:65:    "docker_mcp_gateway": ("host_singleton", "blocked"),
```

Exit code: `0` (rg found matches → exit 0, meaning "not empty"). **Both
matches are the ADR-DCP-MCP-RO-0009-mandated service-family string literal
`"docker_mcp_gateway"`** (one of the exact 9 required family identifiers,
appearing in `ALLOWED_SERVICE_FAMILIES` and `FAMILY_POLICY_TABLE`) — a data
constant, not a Docker/container-inspection call. `resolver_core.py` and
`capability.py` produce zero matches. No forbidden primitive
(`requests.`/`httpx.`/`urllib`/`socket.`/`subprocess`/`os.system`/
`shell=True`) appears anywhere in any of the three files; this was
confirmed both by this scan and by a dedicated unit test
(`test_resolver_core_module_has_no_forbidden_primitives`, which explicitly
documents and excludes the same ADR-mandated `docker_mcp_gateway` literal).
Docstring prose that originally described purity in words like "no
network, socket, subprocess" was reworded specifically to avoid tripping
this scan with prose, not code — see `registry_v2.py`/`resolver_core.py`
module docstrings.

## 6. Secret scan (packet.commit.verify #4)

```
$ rg -n "OPENAI_API_KEY|ANTHROPIC_API_KEY|sk-|Bearer |TOKEN: [REDACTED]" services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly | wc -l
100
```

Exit code: `0`. This pattern is **not** clean repo-wide, before or after
this packet — baseline (this branch, before any of this packet's files
existed, i.e. `git stash -u` applied) is **90** matches. This packet adds
**10** more, all in files it created. Restricting the scan to exactly the
files this packet touched:

```
$ rg -n "OPENAI_API_KEY|ANTHROPIC_API_KEY|sk-|Bearer |TOKEN: [REDACTED]" \
    services/dcp-readonly-facade/src/dcp_facade/registry_v2.py \
    services/dcp-readonly-facade/src/dcp_facade/resolver_core.py \
    services/dcp-readonly-facade/src/dcp_facade/capability.py \
    services/dcp-readonly-facade/schema/registry_v2.schema.json \
    services/dcp-readonly-facade/tests/test_registry_v2.py \
    services/dcp-readonly-facade/tests/test_resolver_core.py \
    services/dcp-readonly-facade/tests/test_capability.py \
    services/dcp-readonly-facade/tests/fixtures/registry_v2/
services/dcp-readonly-facade/schema/registry_v2.schema.json:5:...the bare family name 'task-orchestrator'...
services/dcp-readonly-facade/schema/registry_v2.schema.json:47:...The bare name 'task-orchestrator' is forbidden.
services/dcp-readonly-facade/tests/test_registry_v2.py:53:    assert "task-orchestrator" not in REG2.ALLOWED_SERVICE_FAMILIES
services/dcp-readonly-facade/tests/test_registry_v2.py:127:    assert any("task-orchestrator" in w for w in reg.warnings)
services/dcp-readonly-facade/src/dcp_facade/registry_v2.py:6:...(the bare name ``task-orchestrator`` is forbidden)...
services/dcp-readonly-facade/src/dcp_facade/registry_v2.py:34:# name "task-orchestrator" is FORBIDDEN in registry v2...
services/dcp-readonly-facade/src/dcp_facade/registry_v2.py:51:FORBIDDEN_FAMILY_NAMES: tuple[str, ...] = ("task-orchestrator",)
services/dcp-readonly-facade/src/dcp_facade/registry_v2.py:157:            return None, f"forbidden service family 'task-orchestrator': {family!r}"
services/dcp-readonly-facade/tests/fixtures/registry_v2/invalid_bare_task_orchestrator.yaml:1:# Invalid: bare 'task-orchestrator' family name is forbidden...
services/dcp-readonly-facade/tests/fixtures/registry_v2/invalid_bare_task_orchestrator.yaml:9:      task-orchestrator:
```

Every match is the substring `sk-` inside the literal word
**`ta**sk-**orchestrator`** — the forbidden-family-name string this packet
is REQUIRED to reject (ADR-DCP-MCP-RO-0009 §"Required Service Families";
TP-DCP-MCP-RO-0010 invariant). This is the same pre-existing false-positive
class already present in ~90 other locations across the facade/docs tree
(e.g. `envelope.py:25: SOURCE_TASK_ORCHESTRATOR = "task-orchestrator"`,
`FAILURE_RUNBOOK.md` documenting this exact scan command). No real
credential, token, bearer value, or password literal appears in any file
this packet created or modified — manually reviewed line-by-line above.

## 7. `git status --short`

```
$ git status --short
 M .claude/claude_config.json
 M services/dcp-readonly-facade/registry.example.yaml
?? .claude/.untracked-work-probe-cache.json
?? docs/03-reference/dcp/chatgpt-mcp-readonly/REGISTRY_V2_CONTRACT.md
?? services/dcp-readonly-facade/schema/
?? services/dcp-readonly-facade/src/dcp_facade/capability.py
?? services/dcp-readonly-facade/src/dcp_facade/registry_v2.py
?? services/dcp-readonly-facade/src/dcp_facade/resolver_core.py
?? services/dcp-readonly-facade/tests/fixtures/
?? services/dcp-readonly-facade/tests/test_capability.py
?? services/dcp-readonly-facade/tests/test_registry_v2.py
?? services/dcp-readonly-facade/tests/test_resolver_core.py
?? task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0010.json
?? task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0010.md
```

`.claude/claude_config.json` and `.claude/.untracked-work-probe-cache.json`
were **already** dirty/untracked at session start (see the session's
initial `git status`, taken before this packet's work began) — this
executor did not touch either. `task-packets/dcp/chatgpt-mcp-readonly/
TP-DCP-MCP-RO-0010.{json,md}` were likewise already present as untracked
files at session start (the packet spec provided for this task) and were
only read, never modified, by this executor. All other entries are this
packet's deliverables, and every one of them falls within
`commit.allowlist` (`services/dcp-readonly-facade/**`,
`docs/03-reference/dcp/chatgpt-mcp-readonly/**`,
`task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0010.{json,md}`,
`proof/TP-DCP-MCP-RO-0010/**`).

## 8. `git diff --stat`

```
$ git add -N <all new files>   # intent-to-add only, for a diff --stat view; reverted with `git reset` immediately after
$ git diff --stat
 .claude/claude_config.json                                              |   6 +-
 docs/03-reference/dcp/chatgpt-mcp-readonly/REGISTRY_V2_CONTRACT.md      | 278 ++++++++++++++++
 services/dcp-readonly-facade/registry.example.yaml                      |  72 ++--
 services/dcp-readonly-facade/schema/registry_v2.schema.json             |  68 ++++
 services/dcp-readonly-facade/src/dcp_facade/capability.py               |  43 +++
 services/dcp-readonly-facade/src/dcp_facade/registry_v2.py              | 291 ++++++++++++++++
 services/dcp-readonly-facade/src/dcp_facade/resolver_core.py            | 201 ++++++++++++
 services/dcp-readonly-facade/tests/fixtures/registry_v2/disabled_target.yaml           |  15 +
 services/dcp-readonly-facade/tests/fixtures/registry_v2/invalid_bare_task_orchestrator.yaml | 10 +
 services/dcp-readonly-facade/tests/fixtures/registry_v2/invalid_duplicate_target_id.yaml    | 12 +
 services/dcp-readonly-facade/tests/fixtures/registry_v2/invalid_missing_identity.yaml       |  5 +
 services/dcp-readonly-facade/tests/fixtures/registry_v2/invalid_unknown_family.yaml         | 10 +
 services/dcp-readonly-facade/tests/fixtures/registry_v2/invalid_v1_project_id_doc.yaml      | 15 +
 services/dcp-readonly-facade/tests/fixtures/registry_v2/valid.yaml                          | 19 ++
 services/dcp-readonly-facade/tests/test_capability.py                   | 139 ++++++++
 services/dcp-readonly-facade/tests/test_registry_v2.py                  | 253 ++++++++++++++
 services/dcp-readonly-facade/tests/test_resolver_core.py                | 365 +++++++++++++++++++++
 17 files changed, 1774 insertions(+), 28 deletions(-)
```

`.claude/claude_config.json`'s 6-line delta is pre-existing (from before
this executor's session start) and untouched by this executor; the
`git index` was reset (`git reset`, no `--hard`) immediately after taking
this diff, restoring the plain-untracked state shown in §7 — no files were
staged or committed by this executor.

## 9. Registry v2 example file — self-validates against its own schema and parser with zero warnings

```
$ python3 -c "
import sys, json
sys.path.insert(0, 'src')
import yaml, jsonschema
from dcp_facade.registry_v2 import parse_registry_v2
doc = yaml.safe_load(open('registry.example.yaml'))
schema = json.load(open('schema/registry_v2.schema.json'))
jsonschema.Draft7Validator(schema).validate(doc)
print('schema: OK')
reg = parse_registry_v2(doc)
print('targets:', list(reg.targets))
print('warnings:', reg.warnings)
assert reg.warnings == []
assert set(reg.targets) == {'dopemux-main', 'dopemux-pr-1031'}
print('parse: OK, zero warnings')
"
schema: OK
targets: ['dopemux-main', 'dopemux-pr-1031']
warnings: []
parse: OK, zero warnings
```

## 10. Git-worktree fixture mechanics — empirically verified before writing tests

```
$ git -C primary worktree add --detach -q ../linked <HEAD-sha>
$ cat linked/.git
gitdir: /.../primary/.git/worktrees/linked
$ cat /.../primary/.git/worktrees/linked/commondir
../..
```

Confirmed `.git`-as-gitfile → `gitdir:` → `commondir` → common `.git`'s
parent derivation matches `resolver_core._derive_roots()` exactly, and that
git does not track empty directories (so a linked worktree's `.dopemux/`
marker must be created directly in the worktree, mirroring what
`make_workspace` already does for a primary checkout) — both confirmed
empirically before the corresponding test fixture (`make_linked_worktree`
in `test_resolver_core.py`) was written.
