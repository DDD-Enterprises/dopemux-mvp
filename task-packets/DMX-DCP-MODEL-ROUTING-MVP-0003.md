# Task Packet — DMX-DCP-MODEL-ROUTING-MVP-0003 · DCP · Routing Backend Policy Map

This task packet uses Markdown transport because the artifact path is `.md`.
The fenced JSON payload below is the canonical schema payload for validation
against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

```json
{
  "id": "DMX-DCP-MODEL-ROUTING-MVP-0003",
  "project": "dopemux-mvp",
  "target": "Add a pure, deterministic backend policy recommendation map for already-classified DCP RouteDecision values, with no backend invocation or runtime integration.",
  "invariants": [
    "The backend policy map returns inert recommendation data only; it must not call, import, shell out to, or wire any backend runner, connector, MCP tool, GitHub API, queue, scheduler, or service integration.",
    "RouteDecision runtime/source truth is authoritative for implemented behavior; task packet prose cannot authorize unsupported runtime behavior.",
    "Blocked, unknown, red-lane, escalation-required, stale-proof, missing-proof, stop-condition, live-write, service-mutation, merge, and dynamic forbidden-action decisions fail closed to BackendKind.NONE.",
    "Classifier baseline guardrail prohibitions are not themselves backend blockers for otherwise safe runnable decisions.",
    "Backend preference data is not authorization; any future caller must preserve separate approval, proof, runtime, and operator gates.",
    "Validation must include focused unit coverage, DCP unit coverage, syntax checks, diff hygiene, static no-go scanning, and pre-commit on changed files."
  ],
  "depends_on": [
    "DMX-DCP-MODEL-ROUTING-MVP-0001",
    "DMX-DCP-MODEL-ROUTING-MVP-0002"
  ],
  "repo_binding": {
    "project_id": "DDD-Enterprises/dopemux-mvp",
    "repo_marker": "AGENTS.md",
    "origin_hint": "https://github.com/DDD-Enterprises/dopemux-mvp.git",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-DCP-MODEL-ROUTING-MVP",
    "base_branch": "main",
    "parent_tp_id": "DMX-DCP-MODEL-ROUTING-MVP-0002",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "dcp/model-routing-0003-backend-policy-map",
    "base_branch": "main"
  },
  "commit": {
    "message": "fix(dcp): canonicalize DMX-DCP-MODEL-ROUTING-MVP-0003 task packet",
    "allowlist": [
      "src/dopemux/dcp/__init__.py",
      "src/dopemux/dcp/routing_backend_policy.py",
      "tests/unit/dcp/test_routing_backend_policy.py",
      "task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md"
    ],
    "verify": [
      "python - <<'PY'\nimport json, re\nfrom pathlib import Path\nfrom jsonschema import Draft7Validator\npacket = Path('task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md').read_text()\nmatch = re.search(r'```json\\n(.*?)\\n```', packet, re.S)\nassert match, 'missing fenced json payload'\npayload = json.loads(match.group(1))\nschema = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())\nerrors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))\nif errors:\n    raise SystemExit('\\n'.join('%s: %s' % (('/'.join(map(str, e.path)) or '<root>'), e.message) for e in errors))\nprint('PASS task packet payload schema validation')\nPY",
      "python -m compileall -q src/dopemux/dcp",
      "python -m pytest -q tests/unit/dcp/test_routing_model.py tests/unit/dcp/test_routing_classifier.py tests/unit/dcp/test_routing_backend_policy.py",
      "python -m pytest -q tests/unit/dcp",
      "git diff --check",
      "rg -n \"subprocess|requests|httpx|urllib|socket|open\\(|write_text|write_bytes|Path\\(.+write|os\\.system|shell=True|gh pr merge|merge_pull_request|queue_drain|execute=True|scripts/dopetask|scripts/taskx|opencode|grok|ECC|npm|npx|pnpm|bun|docker compose up|mcp\\.tool|GraphQL|REST\" src/dopemux/dcp/routing_backend_policy.py tests/unit/dcp/test_routing_backend_policy.py",
      "pre-commit run --files src/dopemux/dcp/routing_backend_policy.py tests/unit/dcp/test_routing_backend_policy.py task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md"
    ]
  },
  "pr": {
    "title": "feat(dcp): add backend policy recommendations",
    "body": "## Summary\n- add pure DCP backend policy recommendation data for already-classified RouteDecision values\n- fail closed to BackendKind.NONE for blocked, unknown, red-lane, escalation-required, proof-stopped, and forbidden-action decisions\n- export the policy API and add packet-scoped unit coverage with canonical task packet contract\n\n## Validation\n- PASS: embedded task packet schema validation\n- PASS: python -m compileall -q src/dopemux/dcp\n- PASS: python -m pytest -q tests/unit/dcp/test_routing_model.py tests/unit/dcp/test_routing_classifier.py tests/unit/dcp/test_routing_backend_policy.py\n- PASS: python -m pytest -q tests/unit/dcp\n- PASS: git diff --check\n- PASS: static no-go scan over policy, tests, and packet note\n\n## Explicit Non-Claims\nThis does not integrate callable backends, connectors, MCP wiring, Dopetask execution, Task Orchestrator writes, GitHub writes, or production readiness.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": false,
    "steps": [
      "analyze",
      "planner",
      "implement",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Inspect DCP routing model, classifier, exports, tests, active task packet constraints, and repo governance before editing.",
      "requirements": [
        "Identify RouteDecision fields and fail-closed invariants that the backend policy must preserve.",
        "Identify classifier baseline guardrails separately from dynamic or live forbidden actions.",
        "Confirm the change is limited to pure recommendation data and does not introduce backend invocation."
      ],
      "commands": [
        "git status --short --branch",
        "sed -n '1,260p' src/dopemux/dcp/routing_model.py",
        "sed -n '1,260p' src/dopemux/dcp/routing_classifier.py",
        "sed -n '1,220p' tests/unit/dcp/test_routing_classifier.py"
      ],
      "expected_files": [
        "src/dopemux/dcp/routing_backend_policy.py",
        "tests/unit/dcp/test_routing_backend_policy.py",
        "task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md"
      ],
      "validation": [
        "Relevant routing model and classifier fields are inspected before implementation.",
        "Runtime behavior claims are grounded in source and tests, not packet prose."
      ],
      "context_files": [
        "AGENTS.md",
        "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json",
        "src/dopemux/dcp/routing_model.py",
        "src/dopemux/dcp/routing_classifier.py"
      ]
    },
    {
      "id": "S2",
      "task": "Add a pure backend policy data module and export its public recommendation types.",
      "requirements": [
        "Use frozen dataclasses and enums for inert backend preference data.",
        "Return BackendKind.NONE for any non-runnable, blocked, unknown, red-lane, escalation-required, stale-proof, missing-proof, stop-condition, dynamic forbidden-action, live-write, service-mutation, merge, or supervisor-required route shape.",
        "Recommend safe backend preference data only for safe code, docs/design, and audit route shapes.",
        "Do not add imports or code paths that can execute backends, mutate services, call tools, or invoke subprocesses."
      ],
      "commands": [
        "python -m compileall -q src/dopemux/dcp"
      ],
      "expected_files": [
        "src/dopemux/dcp/routing_backend_policy.py",
        "src/dopemux/dcp/__init__.py"
      ],
      "validation": [
        "compileall exits 0 for src/dopemux/dcp.",
        "Static no-go scan finds no backend invocation, shell, network, queue, MCP, GitHub, or service integration markers in the new module."
      ],
      "context_files": [
        "src/dopemux/dcp/routing_model.py",
        "src/dopemux/dcp/routing_classifier.py",
        "src/dopemux/dcp/__init__.py"
      ]
    },
    {
      "id": "S3",
      "task": "Add focused unit tests that lock safe recommendations and fail-closed behavior.",
      "requirements": [
        "Cover safe code, docs/design, and audit recommendations.",
        "Cover blocked status, red-lane state, non-runnable proof conditions, missing or stale proof, stop conditions, escalation requirements including ON_UNKNOWN, first-class UNKNOWN enum dimensions, live runtime impacts, merge/live task types, supervisor requirements, and dynamic forbidden actions.",
        "Cover classifier-produced safe code routes so baseline guardrail forbidden actions do not block every real classifier decision.",
        "Keep tests deterministic and free of external services."
      ],
      "commands": [
        "python -m pytest -q tests/unit/dcp/test_routing_model.py tests/unit/dcp/test_routing_classifier.py tests/unit/dcp/test_routing_backend_policy.py",
        "python -m pytest -q tests/unit/dcp"
      ],
      "expected_files": [
        "tests/unit/dcp/test_routing_backend_policy.py"
      ],
      "validation": [
        "Focused routing model/classifier/backend policy tests pass.",
        "Full tests/unit/dcp suite passes."
      ],
      "context_files": [
        "tests/unit/dcp/test_routing_model.py",
        "tests/unit/dcp/test_routing_classifier.py",
        "tests/unit/dcp/test_routing_backend_policy.py"
      ]
    },
    {
      "id": "S4",
      "task": "Replace the explanatory packet note with canonical task packet shape, then validate diff hygiene, pre-commit hooks, and PR review closure.",
      "requirements": [
        "Task packet fenced JSON validates against docs/03-reference/spec/dopetask/dopetask-canonical-spec.json.",
        "Changed files stay within commit.allowlist.",
        "No accidental generated junk or unrelated edits are present.",
        "Required GitHub checks are distinguished from non-required failures.",
        "Unresolved review threads are addressed with evidence-backed fixes or explicit technical response."
      ],
      "commands": [
        "python - <<'PY'\nimport json, re\nfrom pathlib import Path\nfrom jsonschema import Draft7Validator\npacket = Path('task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md').read_text()\nmatch = re.search(r'```json\\n(.*?)\\n```', packet, re.S)\nassert match, 'missing fenced json payload'\npayload = json.loads(match.group(1))\nschema = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())\nerrors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))\nif errors:\n    raise SystemExit('\\n'.join('%s: %s' % (('/'.join(map(str, e.path)) or '<root>'), e.message) for e in errors))\nprint('PASS task packet payload schema validation')\nPY",
        "git diff --check",
        "pre-commit run --files src/dopemux/dcp/routing_backend_policy.py tests/unit/dcp/test_routing_backend_policy.py task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md",
        "git status --short --branch",
        "gh pr checks 895 --repo DDD-Enterprises/dopemux-mvp"
      ],
      "expected_files": [
        "task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md"
      ],
      "validation": [
        "Task packet schema validation passes.",
        "git diff --check exits 0.",
        "pre-commit exits 0 for changed files.",
        "Working tree is clean after commit.",
        "Required PR checks pass or any remaining pending/failing required checks are reported explicitly."
      ],
      "context_files": [
        "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json",
        "task-packets/DMX-DCP-MODEL-ROUTING-MVP-0003.md"
      ]
    }
  ]
}
```