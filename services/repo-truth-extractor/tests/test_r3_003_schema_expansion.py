"""RTE-TRUTH R3-003 (schema expansion) regression tests.

Task packet: task-packets/generated/TP-RTE-TRUTH-R3-003.json
Findings: F-39 (schema-expansion opportunity, post-C9), F-36 (thinnest
contracts on highest-value artifacts: D1/E2/G1), F-38 (unbounded/absent
enums on scored fields: B3 severity; S0 input-as-output contract
confusion).

Scope, following the pattern R3-001 established for C18/C19/C20/C21/G6/G7
(services/repo-truth-extractor/promptsets/v4/schemas/):

- New `.schema.json` files for the F-39 "post-C9, ready to schematize"
  candidates: C1 (SERVICE_ENTRYPOINTS), C2 (EVENTBUS_SURFACE /
  EVENT_PRODUCERS / EVENT_CONSUMERS), C7 (API_DASHBOARD_SURFACE), C8
  (DETERMINISM_RISK_LOCATIONS / IDEMPOTENCY_RISK_LOCATIONS /
  CONCURRENCY_RISK_LOCATIONS / SECRETS_RISK_LOCATIONS), C14
  (CODE_HEALTH_SURFACE), G5 (AUTH_FLOW_SURFACE). Every required field and
  enum vocabulary is transcribed verbatim from each prompt's own "Item
  Schema" / "* Definitions" sections under `## Schema` -- nothing invented.
- Hardened the G6/G7 evidence-object subschema (path/line_range/excerpt
  required, additionalProperties:false, excerpt maxLength 200) -- before
  this, `evidence` was `{"type": "array", "minItems": 1}` with no per-item
  shape, so a fabricated `{"note": "..."}` evidence entry validated
  cleanly. The new schema files for C1/C2/C7/C8/C14/G5/B3/D1/E2/G1 ship
  with the same hardened evidence shape from day one.
- B3 (BOUNDARY_BYPASS_RISKS): added a `severity` enum
  (critical/high/medium/low), the vocabulary already used identically by
  C8 and C14 in this same promptset -- reused, not invented.
- Thin-contract fixes (F-36): D1's four `id,evidence`-only sub-artifacts
  (DOC_CONTRACT_CLAIMS/DOC_BOUNDARIES/DOC_SUPERSESSION/CAP_NOTICES) now
  declare `path`+`line_range` as required -- this does not change runtime
  behavior: `lib/phase_contract_map.py`'s
  `RUNNER_MINIMUM_REQUIRED_KEYS = ("id", "path", "line_range")` fallback
  already makes these two fields required today because
  `promptsets/v4/artifacts.yaml` declares `required_fields: []` for these
  four rows (see `test_d1_thin_contract_fields_are_already_runtime_required_via_fallback`
  below) -- the prompt's own declared contract was simply understating
  what's already enforced. E2 (EXEC_ENV_CHAIN) promotes `name` (the env
  var name, the single field its own Extraction Procedure step 4 names
  first) into the required set. G1 (GOV_CI_GATES) gets the hardened
  evidence subschema only -- no new required domain field, because
  PROMPT_G1's Extraction Procedure names no single unambiguous field to
  transcribe without inventing vocabulary (see TP-RTE-TRUTH-R3-003 final
  report for the explicit scope decision).
- S0 (F-38, "S0 input-as-output contract confusion" / audit finding M2):
  PROMPT_S0's `## Schema -> Required output content contracts` bullet
  list enumerated 9 *upstream input* filenames (already listed under
  `## Inputs -> Required arbitration artifacts`) as if S0 writes them,
  when S0's real `## Outputs` are only 2 files. Trimmed the list to the 2
  real outputs. The M4 finding (S0-S6 emit two near-identical files each,
  "better to emit once and copy at runtime") is a *runtime* pipeline
  change, out of scope for this prompt/schema-only packet -- see the
  OUT-OF-BOUNDARY finding in the final report.

Runtime-reachability note: these `.schema.json` files are an offline
dry-run validation lane (this test module validates sample/fixture
payloads against them directly via `jsonschema.Draft202012Validator`);
they are not (yet) loaded by the OpenAI-request-time schema builder in
`lib/structured_output_contracts.py`, which independently derives its own
generic per-field schema from `promptset.yaml` + `artifacts.yaml` + each
prompt's own `required_item_fields:` line via
`lib/phase_contract_map.py::_required_item_fields_by_artifact`. The
`test_*_prompt_required_item_fields_reach_the_runtime_contract_compiler`
tests below prove that the *prompt-text* edits in this packet (D1's
promoted path/line_range, E2's promoted name) are actually consumed by
that real runtime compiler -- not merely documented in a JSON file no
code reads.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = REPO_ROOT / "services" / "repo-truth-extractor"
SCHEMA_DIR = SERVICE_DIR / "promptsets" / "v4" / "schemas"
PROMPT_DIR = SERVICE_DIR / "promptsets" / "v4" / "prompts"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _schema(filename: str) -> Dict[str, Any]:
    payload = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(payload)
    return payload


def _validator(filename: str) -> Draft202012Validator:
    return Draft202012Validator(_schema(filename))


def _evidence(path: str = "src/example.py", line_range=(10, 10), excerpt: str = "x = 1") -> list:
    return [{"path": path, "line_range": list(line_range), "excerpt": excerpt}]


# ---------------------------------------------------------------------------
# Fixture: one compliant item per new/hardened schema file, keyed by filename.
# Values for C1/C2/C7/C8/C14/G5 are the prompts' own "Worked Example" blocks
# (transcribed, not invented); D1/E2/G1/B3 items are minimal-but-compliant
# since those prompts carry no worked example.

COMPLIANT_ITEMS: Dict[str, Dict[str, Any]] = {
    "C1_SERVICE_ENTRYPOINTS.schema.json": {
        "id": "SERVICE_ENTRYPOINTS:d5f3a9b2",
        "service_id": "task-orchestrator",
        "entrypoint_type": "uvicorn",
        "invocation": "uvicorn task_orchestrator.app:app --host 0.0.0.0 --port 8100",
        "module_path": "task_orchestrator.app:app",
        "path": "services/task-orchestrator/Dockerfile",
        "line_range": [22, 22],
        "evidence": _evidence("services/task-orchestrator/Dockerfile", (22, 22), "CMD uvicorn ..."),
    },
    "C2_EVENTBUS_SURFACE.schema.json": {
        "id": "EVENTBUS_SURFACE:a3f1b2c4",
        "event_name": "task.completed",
        "channel": "event_bus",
        "transport": "in_process",
        "retry_policy": "none",
        "ordering_guarantee": "none",
        "path": "services/dopecon-bridge/dopecon_bridge/event_bus.py",
        "line_range": [15, 42],
        "evidence": _evidence("services/dopecon-bridge/dopecon_bridge/event_bus.py", (15, 20), "class EventBus:"),
    },
    "C2_EVENT_PRODUCERS.schema.json": {
        "id": "EVENT_PRODUCERS:1a2b3c4d",
        "event_name": "task.completed",
        "producer_symbol": "emit_task_completed",
        "call_pattern": "emit",
        "path": "services/task-orchestrator/app/events.py",
        "line_range": [8, 10],
        "evidence": _evidence("services/task-orchestrator/app/events.py", (8, 8), "bus.emit('task.completed', payload)"),
    },
    "C2_EVENT_CONSUMERS.schema.json": {
        "id": "EVENT_CONSUMERS:5e6f7a8b",
        "event_name": "task.completed",
        "consumer_symbol": "on_task_completed",
        "registration_pattern": "decorator",
        "path": "services/dashboard/app/handlers.py",
        "line_range": [30, 33],
        "evidence": _evidence("services/dashboard/app/handlers.py", (30, 31), "@bus.subscribe('task.completed')"),
    },
    "C7_API_DASHBOARD_SURFACE.schema.json": {
        "id": "API_DASHBOARD_SURFACE:b7e2d1f8",
        "http_method": "POST",
        "path_template": "/api/v1/tasks/{task_id}/decompose",
        "handler_symbol": "decompose_task",
        "auth_required": False,
        "path": "services/task-orchestrator/app/api/pm_tools.py",
        "line_range": [45, 78],
        "evidence": _evidence(
            "services/task-orchestrator/app/api/pm_tools.py",
            (45, 47),
            "@router.post('/api/v1/tasks/{task_id}/decompose')",
        ),
    },
    "C8_DETERMINISM_RISK_LOCATIONS.schema.json": {
        "id": "DETERMINISM_RISK_LOCATIONS:e8c4f2a1",
        "risk_type": "random_call",
        "severity": "high",
        "affected_symbol": "_select_phase_sample",
        "non_deterministic_call": "random.sample(files, sample_size)",
        "mitigation_present": True,
        "path": "services/repo-truth-extractor/run_extraction_v5.py",
        "line_range": [13690, 13698],
        "evidence": _evidence(
            "services/repo-truth-extractor/run_extraction_v5.py",
            (13690, 13694),
            "def _deterministic_phase_sample(files, n, seed_salt):",
        ),
    },
    "C8_IDEMPOTENCY_RISK_LOCATIONS.schema.json": {
        "id": "IDEMPOTENCY_RISK_LOCATIONS:2c3d4e5f",
        "risk_type": "missing_idempotency_key",
        "severity": "medium",
        "affected_symbol": "create_task",
        "operation": "INSERT INTO tasks without unique constraint guard",
        "mitigation_present": False,
        "path": "services/task-orchestrator/app/db.py",
        "line_range": [90, 95],
        "evidence": _evidence("services/task-orchestrator/app/db.py", (90, 91), "cursor.execute('INSERT INTO tasks ...')"),
    },
    "C8_CONCURRENCY_RISK_LOCATIONS.schema.json": {
        "id": "CONCURRENCY_RISK_LOCATIONS:6a7b8c9d",
        "risk_type": "shared_mutable_state",
        "severity": "critical",
        "affected_symbol": "_GLOBAL_CACHE",
        "shared_resource": "_GLOBAL_CACHE dict",
        "access_pattern": "read_write",
        "mitigation_present": False,
        "path": "services/repo-truth-extractor/lib/cache.py",
        "line_range": [12, 12],
        "evidence": _evidence("services/repo-truth-extractor/lib/cache.py", (12, 12), "_GLOBAL_CACHE = {}"),
    },
    "C8_SECRETS_RISK_LOCATIONS.schema.json": {
        "id": "SECRETS_RISK_LOCATIONS:7b19ad3c",
        "risk_type": "hardcoded_secret",
        "severity": "critical",
        "affected_symbol": "_build_client",
        "secret_category": "api_key",
        "exposure_vector": "Literal key committed to git history; readable by anyone with repo access",
        "mitigation_present": False,
        "path": "services/example/client.py",
        "line_range": [42, 42],
        "evidence": _evidence("services/example/client.py", (42, 42), 'OPENAI_API_KEY = "[REDACTED]"'),
    },
    "C14_CODE_HEALTH_SURFACE.schema.json": {
        "id": "CODE_HEALTH_SURFACE:9f8e7d6c",
        "file_path": "services/repo-truth-extractor/run_extraction_v5.py",
        "function_name": "run_extraction",
        "issue_type": "long_function",
        "severity": "medium",
        "description": "Function exceeds 100 lines of code",
        "line_range": [100, 260],
        "evidence": _evidence("services/repo-truth-extractor/run_extraction_v5.py", (100, 101), "def run_extraction(...):"),
    },
    "G5_AUTH_FLOW_SURFACE.schema.json": {
        "id": "AUTH_FLOW_SURFACE:f2a7c3d1",
        "auth_type": "dependency_injection",
        "mechanism": "fastapi_depends",
        "protected_symbol": "decompose_task",
        "enforcement_point": "route_parameter",
        "path": "services/task-orchestrator/app/api/pm_tools.py",
        "line_range": [45, 48],
        "evidence": _evidence(
            "services/task-orchestrator/app/api/pm_tools.py",
            (45, 46),
            "async def decompose_task(..., user = Depends(get_current_user)):",
        ),
    },
    "B3_BOUNDARY_BYPASS_RISKS.schema.json": {
        "id": "BOUNDARY_BYPASS_RISKS:aa11bb22",
        "risk": "DEBUG=True disables auth guard on /internal routes",
        "severity": "high",
        "location": "src/dopemux/config.py:80",
        "evidence": _evidence("src/dopemux/config.py", (78, 82), "if DEBUG: skip_auth = True"),
    },
    "D1_DOC_INDEX.schema.json": {
        "id": "DOC_INDEX:example",
        "name": "Example doc",
        "path": "docs/example.md",
        "kind": "contract",
        "line_range": [7, 9],
        "evidence": _evidence("docs/example.md", (7, 9), "0007: Example contract statement"),
    },
    "D1_DOC_CONTRACT_CLAIMS.schema.json": {
        "id": "DOC_CONTRACT_CLAIMS:cc33dd44",
        "path": "docs/90-adr/0012-example.md",
        "line_range": [14, 14],
        "evidence": _evidence("docs/90-adr/0012-example.md", (14, 14), "The service MUST validate every request."),
    },
    "D1_DOC_BOUNDARIES.schema.json": {
        "id": "DOC_BOUNDARIES:ee55ff66",
        "path": "docs/90-adr/0012-example.md",
        "line_range": [20, 20],
        "evidence": _evidence("docs/90-adr/0012-example.md", (20, 20), "This module owns the pricing authority."),
    },
    "D1_DOC_SUPERSESSION.schema.json": {
        "id": "DOC_SUPERSESSION:gg77hh88",
        "path": "docs/90-adr/0003-old.md",
        "line_range": [1, 1],
        "evidence": _evidence("docs/90-adr/0003-old.md", (1, 1), "STATUS: DEPRECATED, supersedes 0002"),
    },
    "D1_CAP_NOTICES.schema.json": {
        "id": "CAP_NOTICES:ii99jj00",
        "path": "docs/03-reference/extraction/pipeline-phases.md",
        "line_range": [5, 5],
        "evidence": _evidence("docs/03-reference/extraction/pipeline-phases.md", (5, 5), "Timer automation is planned, not wired."),
    },
    "E2_EXEC_ENV_CHAIN.schema.json": {
        "id": "EXEC_ENV_CHAIN:kk11ll22",
        "name": "DPMX_LIVE_OK",
        "path": "src/dopemux/config.py",
        "line_range": [30, 30],
        "evidence": _evidence("src/dopemux/config.py", (30, 30), "os.getenv('DPMX_LIVE_OK')"),
    },
    "G1_GOV_CI_GATES.schema.json": {
        "id": "GOV_CI_GATES:mm33nn44",
        "path": ".github/workflows/ci.yml",
        "line_range": [40, 44],
        "evidence": _evidence(".github/workflows/ci.yml", (40, 40), "run: pytest --min-coverage=80"),
    },
    "G6_DEPENDENCY_HEALTH_SURFACE.schema.json": {
        "id": "DEPENDENCY_HEALTH_SURFACE:abc123",
        "issue_type": "unpinned_dependency",
        "package_name": "requests",
        "path": "pyproject.toml",
        "line_range": [10, 10],
        "evidence": _evidence("pyproject.toml", (10, 10), 'requests = "*"'),
    },
    "G7_TECHNICAL_DEBT_REGISTER.schema.json": {
        "id": "TECHNICAL_DEBT_REGISTER:def456",
        "debt_type": "todo_marker",
        "description": "TODO: replace shim",
        "path": "src/dopemux/shim.py",
        "line_range": [42, 42],
        "evidence": _evidence("src/dopemux/shim.py", (42, 42), "# TODO: replace shim"),
    },
}

NEW_R3_003_FILES = [
    "C1_SERVICE_ENTRYPOINTS.schema.json",
    "C2_EVENTBUS_SURFACE.schema.json",
    "C2_EVENT_PRODUCERS.schema.json",
    "C2_EVENT_CONSUMERS.schema.json",
    "C7_API_DASHBOARD_SURFACE.schema.json",
    "C8_DETERMINISM_RISK_LOCATIONS.schema.json",
    "C8_IDEMPOTENCY_RISK_LOCATIONS.schema.json",
    "C8_CONCURRENCY_RISK_LOCATIONS.schema.json",
    "C8_SECRETS_RISK_LOCATIONS.schema.json",
    "C14_CODE_HEALTH_SURFACE.schema.json",
    "G5_AUTH_FLOW_SURFACE.schema.json",
    "B3_BOUNDARY_BYPASS_RISKS.schema.json",
    "D1_DOC_INDEX.schema.json",
    "D1_DOC_CONTRACT_CLAIMS.schema.json",
    "D1_DOC_BOUNDARIES.schema.json",
    "D1_DOC_SUPERSESSION.schema.json",
    "D1_CAP_NOTICES.schema.json",
    "E2_EXEC_ENV_CHAIN.schema.json",
    "G1_GOV_CI_GATES.schema.json",
]

HARDENED_EVIDENCE_FILES = NEW_R3_003_FILES + [
    "G6_DEPENDENCY_HEALTH_SURFACE.schema.json",
    "G7_TECHNICAL_DEBT_REGISTER.schema.json",
]


@pytest.mark.parametrize("filename", sorted(SCHEMA_DIR.glob("*.schema.json"), key=lambda p: p.name), ids=lambda p: p.name if isinstance(p, Path) else p)
def test_every_schema_file_in_the_directory_is_valid_json_schema(filename: Path) -> None:
    _schema(filename.name)


@pytest.mark.parametrize("filename", NEW_R3_003_FILES)
def test_new_r3_003_schema_accepts_its_compliant_item(filename: str) -> None:
    schema = _schema(filename)
    payload = {"schema": schema["title"], "items": [COMPLIANT_ITEMS[filename]]}
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize("filename", HARDENED_EVIDENCE_FILES)
def test_schema_rejects_fabricated_unattributed_evidence(filename: str) -> None:
    schema = _schema(filename)
    item = dict(COMPLIANT_ITEMS[filename])
    item["evidence"] = [{"note": "seen somewhere, trust me"}]
    payload = {"schema": schema["title"], "items": [item]}
    assert not Draft202012Validator(schema).is_valid(payload)


@pytest.mark.parametrize("filename", HARDENED_EVIDENCE_FILES)
def test_schema_rejects_evidence_missing_excerpt(filename: str) -> None:
    schema = _schema(filename)
    item = dict(COMPLIANT_ITEMS[filename])
    item["evidence"] = [{"path": "x.py", "line_range": [1, 1]}]
    payload = {"schema": schema["title"], "items": [item]}
    assert not Draft202012Validator(schema).is_valid(payload)


@pytest.mark.parametrize("filename", HARDENED_EVIDENCE_FILES)
def test_schema_rejects_evidence_excerpt_over_200_chars(filename: str) -> None:
    schema = _schema(filename)
    item = dict(COMPLIANT_ITEMS[filename])
    item["evidence"] = [{"path": "x.py", "line_range": [1, 1], "excerpt": "x" * 201}]
    payload = {"schema": schema["title"], "items": [item]}
    assert not Draft202012Validator(schema).is_valid(payload)


# B3's required_item_fields (`id, risk, severity, location, evidence`) has
# no top-level `line_range` -- the prompt never declares one as required, so
# the schema correctly doesn't type it either (it passes through untyped via
# additionalProperties:true, same as every other non-required/"recommended"
# field in this promptset's schema convention). Excluded from the top-level
# line_range test below; its *evidence*-level line_range is still covered by
# test_schema_rejects_fabricated_unattributed_evidence/missing_excerpt/etc.
ITEM_LEVEL_LINE_RANGE_FILES = [f for f in HARDENED_EVIDENCE_FILES if f != "B3_BOUNDARY_BYPASS_RISKS.schema.json"]


def test_b3_schema_has_no_top_level_line_range_property() -> None:
    schema = _schema("B3_BOUNDARY_BYPASS_RISKS.schema.json")
    item_schema = schema["properties"]["items"]["items"]
    assert "line_range" not in item_schema["required"]
    assert "line_range" not in item_schema["properties"]


@pytest.mark.parametrize("filename", ITEM_LEVEL_LINE_RANGE_FILES)
def test_schema_rejects_zero_or_negative_line_range_start(filename: str) -> None:
    schema = _schema(filename)
    item = dict(COMPLIANT_ITEMS[filename])
    item["line_range"] = [0, 1]
    payload = {"schema": schema["title"], "items": [item]}
    assert not Draft202012Validator(schema).is_valid(payload)


# ---------------------------------------------------------------------------
# Enum-specific rejection tests (F-38 / F-39 enum vocabulary).

@pytest.mark.parametrize(
    ("filename", "field", "bad_value"),
    [
        ("C1_SERVICE_ENTRYPOINTS.schema.json", "entrypoint_type", "kubernetes_pod"),
        ("C2_EVENTBUS_SURFACE.schema.json", "transport", "carrier_pigeon"),
        ("C2_EVENT_PRODUCERS.schema.json", "call_pattern", "yeet"),
        ("C2_EVENT_CONSUMERS.schema.json", "registration_pattern", "telepathy"),
        ("C7_API_DASHBOARD_SURFACE.schema.json", "http_method", "FETCH"),
        ("C8_DETERMINISM_RISK_LOCATIONS.schema.json", "risk_type", "vibes_based"),
        ("C8_DETERMINISM_RISK_LOCATIONS.schema.json", "severity", "catastrophic"),
        ("C8_IDEMPOTENCY_RISK_LOCATIONS.schema.json", "risk_type", "unknown_risk"),
        ("C8_CONCURRENCY_RISK_LOCATIONS.schema.json", "access_pattern", "quantum_superposition"),
        ("C8_SECRETS_RISK_LOCATIONS.schema.json", "secret_category", "friendship"),
        ("C14_CODE_HEALTH_SURFACE.schema.json", "issue_type", "vibes"),
        ("C14_CODE_HEALTH_SURFACE.schema.json", "severity", "meh"),
        ("G5_AUTH_FLOW_SURFACE.schema.json", "auth_type", "vibes_check"),
        ("G5_AUTH_FLOW_SURFACE.schema.json", "mechanism", "handshake"),
        ("G5_AUTH_FLOW_SURFACE.schema.json", "enforcement_point", "astral_plane"),
        ("B3_BOUNDARY_BYPASS_RISKS.schema.json", "severity", "extreme"),
        ("G6_DEPENDENCY_HEALTH_SURFACE.schema.json", "issue_type", "vibes_dependency"),
        ("G7_TECHNICAL_DEBT_REGISTER.schema.json", "debt_type", "vibes_marker"),
    ],
)
def test_schema_rejects_out_of_vocabulary_enum_value(filename: str, field: str, bad_value: str) -> None:
    schema = _schema(filename)
    item = dict(COMPLIANT_ITEMS[filename])
    assert field in item, f"fixture for {filename} has no {field!r} field to mutate"
    item[field] = bad_value
    payload = {"schema": schema["title"], "items": [item]}
    assert not Draft202012Validator(schema).is_valid(payload)


def test_b3_boundary_bypass_risks_schema_declares_severity_enum() -> None:
    """F-38: B3 severity previously had no vocabulary at all (any string passed)."""
    schema = _schema("B3_BOUNDARY_BYPASS_RISKS.schema.json")
    severity_schema = schema["properties"]["items"]["items"]["properties"]["severity"]
    assert severity_schema.get("enum") == ["critical", "high", "medium", "low"]


# ---------------------------------------------------------------------------
# Multi-artifact steps (C2, C8) must track every declared artifact, not just
# one file per step -- this is why "6 candidates" becomes more than 6 files.

def test_c2_step_schematizes_all_three_declared_artifacts() -> None:
    for filename in ("C2_EVENTBUS_SURFACE.schema.json", "C2_EVENT_PRODUCERS.schema.json", "C2_EVENT_CONSUMERS.schema.json"):
        assert (SCHEMA_DIR / filename).exists()


def test_c8_step_schematizes_all_four_declared_artifacts() -> None:
    for filename in (
        "C8_DETERMINISM_RISK_LOCATIONS.schema.json",
        "C8_IDEMPOTENCY_RISK_LOCATIONS.schema.json",
        "C8_CONCURRENCY_RISK_LOCATIONS.schema.json",
        "C8_SECRETS_RISK_LOCATIONS.schema.json",
    ):
        assert (SCHEMA_DIR / filename).exists()


# ---------------------------------------------------------------------------
# Runtime-reachability proof: the prompt-text `required_item_fields:` edits
# in this packet (D1's promoted path/line_range; E2's promoted name) are
# consumed by the REAL runtime contract compiler, not just documented in a
# schema file nothing loads. This is what lib/structured_output_contracts.py
# actually uses to build the OpenAI strict-mode request schema and to gate
# outputs in describe_contract_failure -- proving these fields are REACHED,
# not merely present on disk.

def _phase_contract_map_module():
    return _load_module(
        SERVICE_DIR / "lib" / "phase_contract_map.py",
        "phase_contract_map_for_r3_003",
    )


def _structured_output_contracts_module():
    return _load_module(
        SERVICE_DIR / "lib" / "structured_output_contracts.py",
        "structured_output_contracts_for_r3_003",
    )


def test_d1_thin_contract_fields_are_already_runtime_required_via_fallback() -> None:
    """Before touching any prompt text: prove that D1's four `id,evidence`-only
    sub-artifacts already get `path`+`line_range` injected as required at
    runtime today, via RUNNER_MINIMUM_REQUIRED_KEYS in phase_contract_map.py
    (because promptsets/v4/artifacts.yaml declares `required_fields: []` for
    these rows, which is falsy and falls back to the minimum-key tuple).
    This is why promoting path/line_range into the *prompt's own* declared
    `required_item_fields:` line (this packet's fix) reconciles documentation
    with pre-existing runtime behavior rather than changing behavior.
    """
    pcm = _phase_contract_map_module()
    artifact_rules = pcm._artifact_rules_by_key()
    for artifact_name in (
        "DOC_CONTRACT_CLAIMS.partX.json",
        "DOC_BOUNDARIES.partX.json",
        "DOC_SUPERSESSION.partX.json",
        "CAP_NOTICES.partX.json",
    ):
        rule = artifact_rules[("D", artifact_name)]
        assert rule["required_fields"] == [], f"{artifact_name} required_fields drifted from empty-list precondition"
    assert pcm.RUNNER_MINIMUM_REQUIRED_KEYS == ("id", "path", "line_range")


def test_d1_prompt_required_item_fields_now_include_path_and_line_range() -> None:
    prompt_text = (PROMPT_DIR / "PROMPT_D1_CLAIMS___BOUNDARIES___SUPERSESSION.md").read_text(encoding="utf-8")
    pcm = _phase_contract_map_module()
    parsed = pcm._required_item_fields_by_artifact(
        prompt_text,
        [
            "DOC_INDEX.partX.json",
            "DOC_CONTRACT_CLAIMS.partX.json",
            "DOC_BOUNDARIES.partX.json",
            "DOC_SUPERSESSION.partX.json",
            "CAP_NOTICES.partX.json",
        ],
    )
    for artifact_name in (
        "DOC_INDEX.partX.json",
        "DOC_CONTRACT_CLAIMS.partX.json",
        "DOC_BOUNDARIES.partX.json",
        "DOC_SUPERSESSION.partX.json",
        "CAP_NOTICES.partX.json",
    ):
        fields = set(parsed[artifact_name])
        assert {"id", "path", "line_range", "evidence"}.issubset(fields), (artifact_name, fields)


def test_e2_prompt_required_item_fields_now_include_name() -> None:
    prompt_text = (PROMPT_DIR / "PROMPT_E2_ENV_LOADING___CONFIG_CHAIN.md").read_text(encoding="utf-8")
    pcm = _phase_contract_map_module()
    parsed = pcm._required_item_fields_by_artifact(prompt_text, ["EXEC_ENV_CHAIN.json"])
    assert "name" in set(parsed["EXEC_ENV_CHAIN.json"])


def test_d1_and_e2_required_fields_reach_the_openai_response_format_builder() -> None:
    """End-to-end: compile the real phase contract map from disk (promptset.yaml
    + artifacts.yaml + model_map.yaml + each prompt's own required_item_fields
    line + reports/repo_truth_map.json), then build the actual OpenAI strict
    JSON schema for D1 and E2 via lib.structured_output_contracts, and assert
    the promoted fields show up as `required` inside the generated per-item
    schema. If this test passes only because repo_truth_map.json happens to be
    stale/missing these steps, it will be SKIPPED (not silently green) -- see
    the skip branch below.
    """
    pcm = _phase_contract_map_module()
    soc = _structured_output_contracts_module()

    contract_map = pcm.compile_phase_contract_map(emit_warnings=False)
    steps = contract_map.get("steps", {})

    d1_key = "D:D1"
    e2_key = "E:E2"
    if d1_key not in steps or e2_key not in steps:
        pytest.skip(
            "D1/E2 not present in the compiled phase contract map (reports/repo_truth_map.json "
            "may not declare them as JSON-managed for this snapshot); cannot prove runtime "
            "reachability against a map that doesn't scope these steps."
        )

    d1_contract = steps[d1_key]
    response_format, _meta = soc.build_openai_response_format(d1_contract, artifact_names=["DOC_CONTRACT_CLAIMS.partX.json"])
    schema = response_format["json_schema"]["schema"]
    any_of = schema["properties"]["artifacts"]["items"]["anyOf"]
    assert len(any_of) == 1
    item_schema = any_of[0]["properties"]["payload"]["properties"]["items"]["items"]
    assert {"id", "path", "line_range", "evidence"}.issubset(set(item_schema["required"]))

    e2_contract = steps[e2_key]
    response_format, _meta = soc.build_openai_response_format(e2_contract, artifact_names=["EXEC_ENV_CHAIN.json"])
    schema = response_format["json_schema"]["schema"]
    any_of = schema["properties"]["artifacts"]["items"]["anyOf"]
    assert len(any_of) == 1
    item_schema = any_of[0]["properties"]["payload"]["properties"]["items"]["items"]
    assert "name" in set(item_schema["required"])


# ---------------------------------------------------------------------------
# S0 (F-38 / audit finding M2): "Required output content contracts" must no
# longer conflate the 9 upstream *input* filenames with S0's actual 2 outputs.

def test_s0_schema_section_no_longer_lists_upstream_inputs_as_outputs() -> None:
    prompt_text = (PROMPT_DIR / "PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md").read_text(encoding="utf-8")
    schema_section = prompt_text.split("## Schema", 1)[1].split("## Extraction Procedure", 1)[0]
    misclassified_inputs = [
        "CONTROL_PLANE_TRUTH_MAP.md",
        "DOPE_MEMORY_IMPLEMENTATION_TRUTH.md",
        "EVENTBUS_WIRING_TRUTH.md",
        "TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md",
        "TASKX_INTEGRATION_TRUTH.md",
        "WORKFLOWS_TRUTH_GRAPH.md",
        "PORTABILITY_AND_MIGRATION_RISK_LEDGER.md",
        "CONFLICT_LEDGER.md",
        "RISK_REGISTER_TOP20.md",
    ]
    for filename in misclassified_inputs:
        assert filename not in schema_section, f"{filename} still mislabeled as an S0 output in ## Schema"
    # The real outputs must still be present.
    assert "ARCHITECTURE_SYNTHESIS_OPUS.md" in schema_section
    assert "S0_ARCHITECTURE_SYNTHESIS_OPUS.md" in schema_section


def test_s0_outputs_section_unchanged() -> None:
    """Regression guard: this packet only touches the mislabeled ## Schema
    list, not the real ## Outputs contract or the upstream-consumed input
    filenames (S1-S12 read S0_ARCHITECTURE_SYNTHESIS_OPUS.md as an input)."""
    prompt_text = (PROMPT_DIR / "PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md").read_text(encoding="utf-8")
    outputs_section = prompt_text.split("## Outputs", 1)[1].split("## Schema", 1)[0]
    assert "ARCHITECTURE_SYNTHESIS_OPUS.md" in outputs_section
    assert "S0_ARCHITECTURE_SYNTHESIS_OPUS.md" in outputs_section
