"""Regression tests for first-class Grok representation in the embedded-audit contract.

TP-DMX-EMBEDDED-AUDIT-GROK-ROUTE-001.

The contract admits exactly one Grok tool/model pair and binds it in **both**
directions, so neither half can be stated without the other:

    auditor_model == grok-4.5  =>  auditor_tool  == grok-cli
    auditor_tool  == grok-cli  =>  auditor_model == grok-4.5

`grok-4.5-build` is deliberately NOT admitted. It is a runner-internal
usage/telemetry label, not a requestable model id -- `grok -m grok-4.5-build`
fails with `unknown model id`, while `grok-4.5` is selectable. Admitting it
would let a proof name a model that cannot be requested.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"

# The contract exactly as it stood before this packet, vendored so the
# backward-compatibility differential is hermetic instead of depending on a git
# ref that a shallow CI checkout may not have. Pinned by hash so the fixture
# cannot be quietly edited into agreement.
PRE_CHANGE_SCHEMA_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "embedded_audit.schema.pre_grok.json"
)
PRE_CHANGE_SCHEMA_SHA256 = (
    "ec144a96e560afad132b6ff3e6974bc56cd9a4f9065beafa9750d0381f74ca33"
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
    "pal-mcp-clink",
    "none",
)
PRE_CHANGE_MODELS = (
    "sonnet",
    "claude-sonnet-4.6",
    "opus",
    "gemini",
    "gemini-3.1-pro-high",
    "unknown",
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _audit(
    *,
    status: str = "PASS",
    auditor_tool: str = "grok-cli",
    auditor_model: str = "grok-4.5",
    # Pins `-m grok-4.5` deliberately. The schema does not parse `invocation`
    # (see test_schema_does_not_constrain_invocation_string in the AGY suite), so
    # this consistency is not enforced -- which is exactly why the fixtures should
    # model the recommended usage rather than teach the unpinned form. The runner
    # default has moved to grok-4.6, so an unpinned invocation now drifts off the
    # only admitted model.
    invocation: str | None = "grok -m grok-4.5 --always-approve --max-turns 80 "
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
        "report_path": "proof/TP-DMX-EMBEDDED-AUDIT-GROK-ROUTE-001/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": skip_reason,
    }


def _errors(audit: dict, schema: dict | None = None) -> list:
    validator = Draft7Validator(schema if schema is not None else _schema())
    return sorted(validator.iter_errors(audit), key=lambda err: list(err.path))


def _valid(audit: dict) -> bool:
    return _errors(audit) == []


# ---------------------------------------------------------------------------
# Operator-mandated regression matrix
# ---------------------------------------------------------------------------


def test_pass_grok_pair_is_valid() -> None:
    assert _errors(_audit(status="PASS")) == []


def test_pass_with_risks_grok_pair_is_valid() -> None:
    assert _errors(_audit(status="PASS_WITH_RISKS")) == []


def test_pass_grok_cli_with_unknown_model_is_invalid() -> None:
    assert _errors(_audit(auditor_model="unknown"))


def test_pass_none_tool_with_grok_model_is_invalid() -> None:
    assert _errors(_audit(auditor_tool="none"))


def test_pass_claude_code_cli_with_grok_model_is_invalid() -> None:
    """The model half may not be borrowed by another tool."""
    assert _errors(_audit(auditor_tool="claude-code-cli"))


def test_pass_grok_cli_with_gemini_model_is_invalid() -> None:
    """The tool half may not be borrowed by another model."""
    assert _errors(_audit(auditor_model="gemini"))


def test_pass_grok_cli_with_build_label_is_invalid() -> None:
    """`grok-4.5-build` is a usage/telemetry label, not a requestable model id."""
    assert _errors(_audit(auditor_model="grok-4.5-build"))


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


def test_skipped_with_grok_pair_is_invalid() -> None:
    """SKIPPED must not name a runner that did not run."""
    assert _errors(
        _audit(
            status="SKIPPED",
            invocation=None,
            exit_code=None,
            skip_reason="claimed skip",
        )
    )


# ---------------------------------------------------------------------------
# Bidirectionality must not pass vacuously on a missing key
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dropped", ["auditor_tool", "auditor_model"])
def test_grok_conditional_is_self_contained(dropped: str) -> None:
    """JSON Schema `properties` is vacuous for an absent key.

    Without `then.required`, dropping one half of the pair would satisfy the
    conditional instead of failing it. The top-level `required` list happens to
    catch this too; this test pins the conditional's own self-containment so the
    guarantee survives a refactor of the required list.
    """
    audit = _audit()
    del audit[dropped]
    messages = [err.message for err in Draft7Validator(_schema()).iter_errors(audit)]
    assert any(dropped in message for message in messages)


# ---------------------------------------------------------------------------
# Class-level backward compatibility: nothing previously valid became invalid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tool", "model"), list(itertools.product(PRE_CHANGE_TOOLS, PRE_CHANGE_MODELS))
)
def test_pre_change_enum_members_still_accepted(tool: str, model: str) -> None:
    """Every pre-change tool/model member is still an accepted enum value.

    This asserts enum membership only -- the pre-change conditionals
    (SKIPPED pairing, agy/gemini-3.1-pro-high) legitimately reject some
    combinations, and those rejections are pinned separately below.
    """
    errors = _errors(_audit(auditor_tool=tool, auditor_model=model))
    enum_errors = [
        err
        for err in errors
        if err.validator == "enum"
        and list(err.path) in (["auditor_tool"], ["auditor_model"])
    ]
    assert enum_errors == [], f"{tool}/{model} lost enum membership: {enum_errors}"


def test_pre_change_fixture_is_the_real_pre_change_contract() -> None:
    """The vendored pre-change schema is pinned by content hash.

    The differential below is only meaningful if it compares against the actual
    contract as it stood before this packet. Pinning the hash means the fixture
    cannot be edited to make the differential pass -- doing so fails here first.
    """
    actual = hashlib.sha256(PRE_CHANGE_SCHEMA_PATH.read_bytes()).hexdigest()
    assert actual == PRE_CHANGE_SCHEMA_SHA256, (
        "The vendored pre-change schema does not match the pinned hash. Either it "
        "was edited, or it was regenerated from the wrong ref. Do not update the "
        "constant to match the file -- work out which one is wrong."
    )
    assert "grok" not in PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8")


def test_vendored_pre_change_schema_matches_git_when_git_is_available() -> None:
    """Cross-check the vendored copy against git, when git can answer.

    This is the belt to the hash pin's braces: it catches a fixture that was
    vendored from the wrong ref but whose hash constant was updated to match.
    It may skip -- it is a corroboration, not the guarantee. The guarantee is
    the hash pin above and the differential below, neither of which can skip.
    """
    try:
        from_git = subprocess.run(
            ["git", "show", "origin/main:schemas/proof/embedded_audit.schema.json"],
            capture_output=True,
            check=True,
            cwd=ROOT,
            text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        pytest.skip(f"git cannot resolve origin/main: {exc}")

    if "grok-cli" in from_git:
        pytest.skip("origin/main already carries the grok route; this packet merged")

    assert json.loads(from_git) == json.loads(
        PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8")
    )


def test_new_schema_matches_pre_change_schema_on_all_old_pairs() -> None:
    """Exact differential: old and new schema must agree on every pre-change pair.

    Compares against the real pre-change contract rather than a re-implementation
    of its rules, so this compares contracts instead of comparing a contract to a
    paraphrase.

    This test **cannot skip**. An earlier draft read the old schema from
    ``git show`` and skipped when the ref was unavailable, which would have gone
    silently green under a shallow CI checkout -- a backward-compatibility
    guarantee that evaporates exactly when nobody is watching. The pre-change
    schema is vendored and hash-pinned instead, so the differential is hermetic.
    """
    old_schema = json.loads(PRE_CHANGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    new_schema = _schema()
    disagreements = []
    for tool, model in itertools.product(PRE_CHANGE_TOOLS, PRE_CHANGE_MODELS):
        for status in ("PASS", "PASS_WITH_RISKS", "FAIL", "NEEDS_SUPERVISOR", "SKIPPED"):
            skipped = status == "SKIPPED"
            audit = _audit(
                status=status,
                auditor_tool=tool,
                auditor_model=model,
                invocation=None if skipped else "<bounded read-only audit prompt>",
                exit_code=None if skipped else 0,
                skip_reason="reason" if skipped else None,
            )
            was_valid = _errors(audit, old_schema) == []
            now_valid = _errors(audit, new_schema) == []
            if was_valid != now_valid:
                disagreements.append((status, tool, model, was_valid, now_valid))

    assert disagreements == [], f"verdict changed for pre-change inputs: {disagreements}"


# ---------------------------------------------------------------------------
# The pre-existing AGY conditional must not be weakened by the new one
# ---------------------------------------------------------------------------


def test_agy_gemini_31_pair_still_valid() -> None:
    assert (
        _errors(_audit(auditor_tool="agy", auditor_model="gemini-3.1-pro-high")) == []
    )


def test_gemini_31_rejected_for_grok_cli() -> None:
    assert _errors(_audit(auditor_tool="grok-cli", auditor_model="gemini-3.1-pro-high"))


def test_schema_admits_exactly_one_grok_tool_and_model() -> None:
    """Guard against a later packet quietly widening the Grok surface.

    `grok-4.6` is the runner's current default but is NOT admitted here: this
    packet was authorized for `grok-4.5` only. Admitting another Grok model is
    an operator decision, and changing this test is how that decision becomes
    visible rather than incidental.
    """
    schema = _schema()
    tools = schema["properties"]["auditor_tool"]["enum"]
    models = schema["properties"]["auditor_model"]["enum"]
    assert [t for t in tools if "grok" in t] == ["grok-cli"]
    assert [m for m in models if "grok" in m] == ["grok-4.5"]
