"""Regression tests for admitting grok-cli / grok-4.7 to the embedded-audit contract.

TP-DMX-EMBEDDED-AUDIT-GROK-4-7-ROUTE-001.

The contract admits exactly two Grok tool/model pairs, both on the one tool
``grok-cli``, and binds them in **both** directions so neither half can be stated
without the other:

    auditor_model == grok-4.7  =>  auditor_tool  == grok-cli
    auditor_tool  == grok-cli  =>  auditor_model in {grok-4.5, grok-4.7}

Nothing else is admitted: not grok-4.6, not ``-build`` telemetry labels, not
aliases. Widening the Grok surface further is an operator decision, and changing
the exact-surface test below is how that decision becomes visible.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"

# The contract exactly as it stood before this packet (origin/main c5a0ca34f),
# vendored so the backward-compatibility differential is hermetic instead of
# depending on a git ref that a shallow CI checkout may not have. Pinned by hash
# so the fixture cannot be quietly edited into agreement.
PRE_CHANGE_REF = "c5a0ca34f"
PRE_CHANGE_SCHEMA_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "embedded_audit.schema.pre_grok_4_7.json"
)
PRE_CHANGE_SCHEMA_SHA256 = (
    "a5151872772e225e9fe9e293a958dd9d9ffce60a58934384233b49cdc4fcb9d3"
)

# The enum members as they stood BEFORE this packet. These are historical facts,
# not configuration: every pair valid under them must stay valid, or this change
# silently narrowed an existing contract.
PRE_CHANGE_TOOLS = (
    "agy",
    "antigravity",
    "claude-code-cli",
    "copilot-cli",
    "gemini-cli",
    "grok-cli",
    "opencode-cli",
    "pal-mcp-clink",
    "none",
)
PRE_CHANGE_MODELS = (
    "sonnet",
    "claude-sonnet-4.6",
    "opus",
    "gemini",
    "gemini-3.1-pro-high",
    "grok-4.5",
    "kimi-k3",
    "unknown",
)

NON_SKIPPED_STATUSES = ("PASS", "PASS_WITH_RISKS", "FAIL", "NEEDS_SUPERVISOR")
ALL_STATUSES = NON_SKIPPED_STATUSES + ("SKIPPED",)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _audit(
    *,
    status: str = "PASS",
    auditor_tool: str = "grok-cli",
    auditor_model: str = "grok-4.7",
    # Pins `-m grok-4.7` deliberately. The schema does not parse `invocation`, so
    # this consistency is not enforced -- which is exactly why the fixtures should
    # model the recommended pinned usage rather than teach the unpinned form.
    invocation: str | None = "grok -m grok-4.7 --always-approve --max-turns 80 "
    "--output-format plain -p '<bounded read-only audit prompt>'",
    exit_code: int | None = 0,
    skip_reason: str | None = None,
) -> dict:
    return {
        "required": True,
        "status": status,
        "auditor_tool": auditor_tool,
        "auditor_model": auditor_model,
        "invocation": invocation,
        "exit_code": exit_code,
        "report_path": "proof/TP-DMX-EMBEDDED-AUDIT-GROK-4-7-ROUTE-001/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": skip_reason,
    }


def _errors(audit: dict, schema: dict | None = None) -> list:
    validator = Draft7Validator(schema if schema is not None else _schema())
    return sorted(validator.iter_errors(audit), key=lambda err: list(err.path))


def _valid(audit: dict, schema: dict | None = None) -> bool:
    return _errors(audit, schema) == []


def _without_enums(schema: dict) -> dict:
    """The schema with the auditor_tool/auditor_model enums removed.

    Isolates the allOf conditionals from the enums: whatever is still rejected is
    rejected by a conditional, not by enum membership.
    """
    stripped = copy.deepcopy(schema)
    del stripped["properties"]["auditor_tool"]["enum"]
    del stripped["properties"]["auditor_model"]["enum"]
    return stripped


# ---------------------------------------------------------------------------
# The new pair: grok-cli / grok-4.7
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", NON_SKIPPED_STATUSES)
def test_grok_4_7_pair_is_valid_for_every_non_skipped_status(status: str) -> None:
    assert _errors(_audit(status=status)) == []


@pytest.mark.parametrize(
    "tool", [t for t in PRE_CHANGE_TOOLS if t != "grok-cli"] + ["not-a-tool"]
)
@pytest.mark.parametrize("status", NON_SKIPPED_STATUSES)
def test_grok_4_7_with_any_other_tool_is_invalid(tool: str, status: str) -> None:
    """The model half may not be borrowed by another tool."""
    assert _errors(_audit(status=status, auditor_tool=tool))


@pytest.mark.parametrize(
    "model",
    [
        "unknown",
        "grok-4.6",
        "grok-4.5-build",
        "grok-4.7-build",
        "grok-4",
        "grok-5",
        "Grok-4.7",
        "grok-4.7 ",
        "gemini",
        "gemini-3.1-pro-high",
        "kimi-k3",
        "sonnet",
        "opus",
        "",
    ],
)
@pytest.mark.parametrize("status", NON_SKIPPED_STATUSES)
def test_grok_cli_with_any_model_outside_the_admitted_pair_is_invalid(
    model: str, status: str
) -> None:
    """The tool half may not be borrowed by another model, nor widened to a sibling."""
    assert _errors(_audit(status=status, auditor_tool="grok-cli", auditor_model=model))


@pytest.mark.parametrize("model", ["grok-4.6", "grok-4.7-build", "grok-4.5-build", "unknown"])
def test_grok_cli_conditional_rejects_without_help_from_the_enum(model: str) -> None:
    """grok-cli => {4.5, 4.7} must be enforced by the conditional itself.

    With the enums stripped, a non-admitted model on grok-cli must still fail, so
    the guarantee does not depend on enum membership happening to cover it.
    """
    stripped = _without_enums(_schema())
    assert _errors(_audit(auditor_model=model), stripped)


@pytest.mark.parametrize("tool", ["agy", "claude-code-cli", "opencode-cli", "none", "x"])
def test_grok_4_7_conditional_rejects_without_help_from_the_enum(tool: str) -> None:
    stripped = _without_enums(_schema())
    assert _errors(_audit(auditor_tool=tool), stripped)


@pytest.mark.parametrize("model", ["grok-4.5", "grok-4.7"])
def test_grok_cli_conditional_accepts_only_the_pair_without_enums(model: str) -> None:
    stripped = _without_enums(_schema())
    assert _errors(_audit(auditor_model=model), stripped) == []


# ---------------------------------------------------------------------------
# The old pair still works
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", NON_SKIPPED_STATUSES)
def test_grok_4_5_pair_is_still_valid(status: str) -> None:
    assert _errors(_audit(status=status, auditor_model="grok-4.5")) == []


def test_grok_4_5_with_other_tool_is_still_invalid() -> None:
    assert _errors(_audit(auditor_tool="claude-code-cli", auditor_model="grok-4.5"))


def test_grok_4_5_build_label_remains_not_admitted() -> None:
    assert _errors(_audit(auditor_model="grok-4.5-build"))


# ---------------------------------------------------------------------------
# SKIPPED rules are unchanged
# ---------------------------------------------------------------------------


def test_skipped_none_unknown_remains_valid() -> None:
    assert (
        _errors(
            _audit(
                status="SKIPPED",
                auditor_tool="none",
                auditor_model="unknown",
                invocation=None,
                exit_code=None,
                skip_reason="No independent auditor was available.",
            )
        )
        == []
    )


@pytest.mark.parametrize("model", ["grok-4.5", "grok-4.7"])
def test_skipped_with_grok_pair_is_invalid(model: str) -> None:
    """SKIPPED must not name a runner that did not run."""
    assert _errors(
        _audit(
            status="SKIPPED",
            auditor_model=model,
            invocation=None,
            exit_code=None,
            skip_reason="claimed skip",
        )
    )


def test_non_skipped_none_unknown_remains_invalid() -> None:
    assert _errors(_audit(auditor_tool="none", auditor_model="unknown"))


# ---------------------------------------------------------------------------
# Bidirectionality must not pass vacuously on a missing key
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dropped", ["auditor_tool", "auditor_model"])
def test_grok_4_7_conditional_is_self_contained(dropped: str) -> None:
    """JSON Schema `properties` is vacuous for an absent key.

    Without `then.required`, dropping one half of the pair would satisfy the
    conditional instead of failing it. Checked with the top-level `required`
    removed so that the conditional's own `then.required` is what is under test.
    """
    schema = _schema()
    schema = copy.deepcopy(schema)
    schema["required"] = [k for k in schema["required"] if k != dropped]
    audit = _audit()
    del audit[dropped]
    messages = [err.message for err in Draft7Validator(schema).iter_errors(audit)]
    assert any(dropped in message for message in messages)


def test_every_grok_conditional_carries_then_required() -> None:
    grok_conditionals = [
        entry
        for entry in _schema()["allOf"]
        if "grok" in json.dumps(entry["if"])
    ]
    # grok-4.5 => grok-cli, grok-cli => {4.5, 4.7}, grok-4.7 => grok-cli
    assert len(grok_conditionals) == 3
    for entry in grok_conditionals:
        assert entry["if"].get("required"), entry
        assert entry["then"].get("required"), entry


# ---------------------------------------------------------------------------
# Exact surface: nothing but grok-4.7 was added
# ---------------------------------------------------------------------------


def test_schema_admits_exactly_one_grok_tool_and_two_grok_models() -> None:
    """Guard against a later packet quietly widening the Grok surface.

    grok-4.6, build labels and aliases are NOT admitted. Admitting another Grok
    model is an operator decision; changing this test makes it visible.
    """
    schema = _schema()
    tools = schema["properties"]["auditor_tool"]["enum"]
    models = schema["properties"]["auditor_model"]["enum"]
    assert [t for t in tools if "grok" in t] == ["grok-cli"]
    assert [m for m in models if "grok" in m] == ["grok-4.5", "grok-4.7"]


def test_schema_delta_against_pre_change_is_exactly_grok_4_7() -> None:
    old = json.loads(PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    new = _schema()

    assert (
        new["properties"]["auditor_tool"]["enum"]
        == old["properties"]["auditor_tool"]["enum"]
    )
    old_models = old["properties"]["auditor_model"]["enum"]
    new_models = new["properties"]["auditor_model"]["enum"]
    assert sorted(new_models) == sorted(old_models + ["grok-4.7"])

    # Everything outside auditor_tool/auditor_model enums and allOf is untouched.
    def _rest(schema: dict) -> dict:
        rest = copy.deepcopy(schema)
        del rest["allOf"]
        del rest["properties"]["auditor_tool"]["enum"]
        del rest["properties"]["auditor_model"]["enum"]
        return rest

    assert _rest(new) == _rest(old)

    # allOf: every pre-change conditional is byte-identical except the one
    # `auditor_tool == grok-cli` conditional, plus exactly one appended/added
    # conditional for grok-4.7.
    def _is_grok_tool_conditional(entry: dict) -> bool:
        return entry.get("if", {}).get("properties", {}).get("auditor_tool") == {
            "const": "grok-cli"
        }

    old_rest = [e for e in old["allOf"] if not _is_grok_tool_conditional(e)]
    new_rest = [e for e in new["allOf"] if not _is_grok_tool_conditional(e)]
    added = [e for e in new_rest if e not in old_rest]
    assert [e for e in old_rest if e not in new_rest] == []
    assert len(added) == 1
    assert added[0]["if"]["properties"]["auditor_model"] == {"const": "grok-4.7"}
    assert added[0]["then"]["properties"]["auditor_tool"] == {"const": "grok-cli"}
    assert added[0]["then"]["required"] == ["auditor_tool"]
    assert len(new["allOf"]) == len(old["allOf"]) + 1

    # The modified conditional is now an enum of exactly the two admitted models.
    (new_tool_cond,) = [e for e in new["allOf"] if _is_grok_tool_conditional(e)]
    assert new_tool_cond["then"]["properties"]["auditor_model"] == {
        "enum": ["grok-4.5", "grok-4.7"]
    }
    assert new_tool_cond["then"]["required"] == ["auditor_model"]


# ---------------------------------------------------------------------------
# Class-level backward compatibility: nothing previously valid became invalid
# ---------------------------------------------------------------------------


def test_pre_change_fixture_is_the_real_pre_change_contract() -> None:
    """The vendored pre-change schema is pinned by content hash."""
    actual = hashlib.sha256(PRE_CHANGE_SCHEMA_PATH.read_bytes()).hexdigest()
    assert actual == PRE_CHANGE_SCHEMA_SHA256, (
        "The vendored pre-change schema does not match the pinned hash. Either it "
        "was edited, or it was regenerated from the wrong ref. Do not update the "
        "constant to match the file -- work out which one is wrong."
    )
    assert "grok-4.7" not in PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8")


def test_vendored_pre_change_schema_matches_git_when_git_is_available() -> None:
    """Cross-check the vendored copy against the immutable pre-change commit.

    A corroboration, not the guarantee: it may skip when git cannot resolve the
    commit (shallow checkout). The guarantee is the hash pin above and the
    differential below, neither of which can skip.
    """
    try:
        from_git = subprocess.run(
            [
                "git",
                "show",
                f"{PRE_CHANGE_REF}:schemas/proof/embedded_audit.schema.json",
            ],
            capture_output=True,
            check=True,
            cwd=ROOT,
            text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        pytest.skip(f"git cannot resolve {PRE_CHANGE_REF}: {exc}")

    assert json.loads(from_git) == json.loads(
        PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8")
    )


def test_new_schema_matches_pre_change_schema_on_all_old_pairs() -> None:
    """Exact differential: old and new schema agree on every pre-change pair.

    Compares against the real pre-change contract rather than a re-implementation
    of its rules. This test cannot skip: the pre-change schema is vendored and
    hash-pinned, not read from a git ref that may be absent.
    """
    old_schema = json.loads(PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    new_schema = _schema()
    disagreements = []
    for tool, model in itertools.product(PRE_CHANGE_TOOLS, PRE_CHANGE_MODELS):
        for status in ALL_STATUSES:
            skipped = status == "SKIPPED"
            audit = _audit(
                status=status,
                auditor_tool=tool,
                auditor_model=model,
                invocation=None if skipped else "<bounded read-only audit prompt>",
                exit_code=None if skipped else 0,
                skip_reason="reason" if skipped else None,
            )
            was_valid = _valid(audit, old_schema)
            now_valid = _valid(audit, new_schema)
            if was_valid != now_valid:
                disagreements.append((status, tool, model, was_valid, now_valid))

    assert disagreements == [], f"verdict changed for pre-change inputs: {disagreements}"


def test_only_new_verdicts_are_grok_cli_with_grok_4_7() -> None:
    """Over pre-change tools plus grok-4.7, the only newly valid inputs are grok-cli/4.7."""
    old_schema = json.loads(PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    new_schema = _schema()
    models = PRE_CHANGE_MODELS + ("grok-4.7",)
    newly_valid = []
    for tool, model in itertools.product(PRE_CHANGE_TOOLS, models):
        for status in ALL_STATUSES:
            skipped = status == "SKIPPED"
            audit = _audit(
                status=status,
                auditor_tool=tool,
                auditor_model=model,
                invocation=None if skipped else "<bounded read-only audit prompt>",
                exit_code=None if skipped else 0,
                skip_reason="reason" if skipped else None,
            )
            if _valid(audit, new_schema) and not _valid(audit, old_schema):
                newly_valid.append((status, tool, model))

    assert sorted(newly_valid) == sorted(
        (status, "grok-cli", "grok-4.7") for status in NON_SKIPPED_STATUSES
    )


# ---------------------------------------------------------------------------
# Neighbouring conditionals must not be weakened
# ---------------------------------------------------------------------------


def test_agy_gemini_31_pair_still_valid() -> None:
    assert (
        _errors(_audit(auditor_tool="agy", auditor_model="gemini-3.1-pro-high")) == []
    )


def test_opencode_kimi_pair_still_valid() -> None:
    assert _errors(_audit(auditor_tool="opencode-cli", auditor_model="kimi-k3")) == []


def test_gemini_31_rejected_for_grok_cli() -> None:
    assert _errors(_audit(auditor_tool="grok-cli", auditor_model="gemini-3.1-pro-high"))


def test_kimi_rejected_for_grok_cli() -> None:
    assert _errors(_audit(auditor_tool="grok-cli", auditor_model="kimi-k3"))
