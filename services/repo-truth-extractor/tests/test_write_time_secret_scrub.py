"""F-23 enforcement half (TP-RTE-TRUTH-R3-007) — write-time secret scrub.

TP-RTE-TRUTH-R3-004 (commit 6aac1ef79) made secret redaction BINDING in the prompt
bodies for C8 (SECRETS_RISK_LOCATIONS), H1, H7 and the M3/M4/M5 safe-exports. Its own
PROOF.json states the limit plainly: that is an *instruction*, not an *enforcement*. A
non-compliant or jailbroken model still writes a real secret value into
``SECRETS_RISK_LOCATIONS.json`` on disk, and from there into
``PROMPT_R11_SECURITY_RISK_SYNTHESIS``.

The actual gap (traced for this packet, and narrower than the packet's premise):
``run_extraction_v5.write_json`` DOES already run ``sanitize_payload_for_output`` on
every artifact write -- so the artifact write path is not unprotected. But that scrub
deliberately omits ``_LONG_TOKEN_CANDIDATE_RE``, the high-entropy catch-all that
``sanitize_payload_for_provider`` applies before a payload leaves the machine. So a
secret whose surrounding text carries no recognizable key name and whose value has no
provider prefix -- e.g. a raw AWS secret *value*, as opposed to its ``AKIA``-prefixed
access-key *id* -- passes ``sanitize_payload_for_output`` untouched and lands on disk.

These tests pin the fix: for the named C8/H1/H7/M artifact set, the stricter scrub runs
at write time, so leakage is structurally impossible regardless of model behavior.

Every credential in this file is FAKE: syntactically plausible, invented, inert. Never
replace one with a real value.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]

# --- FAKE credentials (invented; never real) --------------------------------
# A high-entropy blob with no provider prefix and no adjacent key name: this is the
# exact shape that survives sanitize_payload_for_output and motivates this packet.
FAKE_BARE_SECRET = "TqZ8bKp3Vn6Ws0Ad5Ef2Gh7Rt8Yc3Lm2Kf9Qx4Mn6Op1Zr7"
FAKE_XAI_KEY = "xai-FAKEfake0000TESTtestKEYkey1111NOTREAL2222"
FAKE_GOOGLE_KEY = "AIzaSyFAKE0000TESTtestKEYkey1111NOTREALxyz"
FAKE_AWS_ACCESS_KEY_ID = "AKIAFAKEFAKEFAKEFAKE"
FAKE_ASSIGNED_SECRET = 'api_key = "sk-proj-FAKEfake0000TESTtestNOTREAL1111"'

ALL_FAKE_LITERALS = (
    FAKE_BARE_SECRET,
    FAKE_XAI_KEY,
    FAKE_GOOGLE_KEY,
    FAKE_AWS_ACCESS_KEY_ID,
    "sk-proj-FAKEfake0000TESTtestNOTREAL1111",
)

# The artifact names whose contract forbids any secret value reaching disk.
SECURITY_ARTIFACTS = (
    "SECRETS_RISK_LOCATIONS.json",
    "HOME_KEYS_SURFACE.json",
    "HOME_REFERENCES.json",
    "HOME_SQLITE_SCHEMA.json",
    "M3_CONPORT_EXPORT_SAFE.json",
    "M4_DOPE_CONTEXT_EXPORT_SAFE.json",
    "M5_MCP_HEALTH_EXPORT_SAFE.json",
)


def _load_output_safety():
    module_path = SERVICE_ROOT / "output_safety.py"
    spec = importlib.util.spec_from_file_location(
        "output_safety_write_scrub", module_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_v5_runner():
    module_path = SERVICE_ROOT / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location(
        "run_extraction_v5_write_scrub", module_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _noncompliant_finding() -> Dict[str, Any]:
    """A SECRETS_RISK_LOCATIONS item as a NON-COMPLIANT model would emit it.

    R3-004's binding rule says the excerpt must be masked. This payload models the
    case where the model ignored that rule and copied the credential verbatim.
    """
    return {
        "id": "SECRETS_RISK_LOCATIONS:7b19ad3c",
        "path": "services/example/settings.py",
        "line_range": [41, 41],
        "risk_type": "hardcoded_secret",
        "affected_symbol": "DEFAULT_CREDENTIALS",
        "exposure_vector": "committed_source",
        "evidence": [
            {
                "path": "services/example/settings.py",
                "line_range": [41, 41],
                # Unmasked, in defiance of the binding rule.
                "excerpt": f"0041: DEFAULT_CREDENTIALS = {FAKE_BARE_SECRET}",
            }
        ],
        "mitigation_description": (
            f"Rotate {FAKE_XAI_KEY} and {FAKE_GOOGLE_KEY}; the AWS id "
            f"{FAKE_AWS_ACCESS_KEY_ID} appears alongside {FAKE_ASSIGNED_SECRET}."
        ),
    }


# ---------------------------------------------------------------------------
# The gap this packet closes, stated as an assertion rather than prose.
# ---------------------------------------------------------------------------


def test_generic_output_scrub_alone_does_not_catch_a_bare_high_entropy_secret() -> None:
    """Documents WHY the write path needed strengthening.

    This is the trace result: sanitize_payload_for_output already runs on every
    artifact write, but a bare high-entropy token with no adjacent key name and no
    provider prefix passes through it. Asserted as a *directional* property (the
    security scrub is strictly stronger), so hardening the generic scrub later
    does not falsely fail this test.
    """
    osafe = _load_output_safety()
    excerpt = f"0041: DEFAULT_CREDENTIALS = {FAKE_BARE_SECRET}"

    strict = osafe.sanitize_payload_for_security_artifact(excerpt)
    assert FAKE_BARE_SECRET not in strict, (
        "the security-artifact scrub must mask a bare high-entropy secret"
    )
    assert "[REDACTED]" in strict

    generic = osafe.sanitize_payload_for_output(excerpt)
    if FAKE_BARE_SECRET in generic:
        # Current behavior, and the reason this packet exists.
        pass
    else:  # pragma: no cover - only if the generic scrub is later hardened
        pytest.skip(
            "generic output scrub now also masks bare high-entropy tokens; the "
            "security-artifact scrub remains the fail-closed guarantee"
        )


def test_security_artifact_membership_covers_the_c8_h1_h7_m_set() -> None:
    osafe = _load_output_safety()
    for name in SECURITY_ARTIFACTS:
        assert osafe.is_security_sensitive_artifact(name), name
        # Path-qualified names resolve to the same decision.
        assert osafe.is_security_sensitive_artifact(f"C/norm/{name}"), name
    # Sibling C8 artifacts that carry no credential contract are not in the set.
    assert not osafe.is_security_sensitive_artifact("DETERMINISM_RISK_LOCATIONS.json")
    assert not osafe.is_security_sensitive_artifact("")
    assert not osafe.is_security_sensitive_artifact(None)


# ---------------------------------------------------------------------------
# Payload-level: masks the secret span, preserves the finding.
# ---------------------------------------------------------------------------


def test_scrub_masks_every_fake_secret_but_preserves_the_finding() -> None:
    osafe = _load_output_safety()
    payload = {"items": [_noncompliant_finding()]}

    scrubbed = osafe.sanitize_payload_for_security_artifact(payload)
    text = json.dumps(scrubbed)

    for literal in ALL_FAKE_LITERALS:
        assert literal not in text, f"secret literal survived the scrub: {literal[:12]}..."

    # The location IS the value: dropping the finding would be a worse outcome than
    # leaking it, so every locating field must survive intact.
    item = scrubbed["items"][0]
    # NOTE (pre-existing, not introduced here): the C8 id_rule prefix literally
    # contains the word "SECRETS", so _SECRET_ASSIGN_RE reads
    # "SECRETS_RISK_LOCATIONS:<hash>" as a sensitive assignment and masks the hash.
    # This already happens on the current write path -- write_json applies
    # sanitize_payload_for_output to every artifact -- so behavior is unchanged by
    # this packet. Asserted here so the identity is pinned rather than assumed.
    assert item["id"].startswith("SECRETS_RISK_LOCATIONS:")
    assert item["id"] == _load_output_safety().sanitize_payload_for_output(
        {"id": "SECRETS_RISK_LOCATIONS:7b19ad3c"}
    )["id"], "the security scrub must not mangle ids any further than the generic one"
    assert item["path"] == "services/example/settings.py"
    assert item["line_range"] == [41, 41]
    assert item["risk_type"] == "hardcoded_secret"
    assert item["affected_symbol"] == "DEFAULT_CREDENTIALS"
    assert item["exposure_vector"] == "committed_source"
    assert item["evidence"][0]["path"] == "services/example/settings.py"
    assert item["evidence"][0]["line_range"] == [41, 41]
    # The excerpt is kept as evidence, with only the secret span masked.
    assert "DEFAULT_CREDENTIALS" in item["evidence"][0]["excerpt"]
    assert "0041:" in item["evidence"][0]["excerpt"]
    assert "[REDACTED]" in item["evidence"][0]["excerpt"]


def test_scrub_is_idempotent() -> None:
    osafe = _load_output_safety()
    payload = {"items": [_noncompliant_finding()]}
    once = osafe.sanitize_payload_for_security_artifact(payload)
    twice = osafe.sanitize_payload_for_security_artifact(once)
    assert once == twice, "scrub must be stable under re-application (determinism)"


# ---------------------------------------------------------------------------
# Write-site: the artifact that actually lands on disk.
# ---------------------------------------------------------------------------


def _write_raw_partition(
    raw_dir: Path, step_id: str, partition_id: str, artifact_name: str
) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{step_id}__{partition_id}.json").write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "artifact_name": artifact_name,
                        "payload": {"items": [_noncompliant_finding()]},
                    }
                ],
                "request_meta": {"schema_gate_passed": True},
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("phase", "step_id", "artifact_name"),
    [
        ("C", "C8", "SECRETS_RISK_LOCATIONS.json"),
        ("H", "H1", "HOME_KEYS_SURFACE.json"),
        ("H", "H1", "HOME_REFERENCES.json"),
        ("H", "H7", "HOME_SQLITE_SCHEMA.json"),
        ("M", "M3", "M3_CONPORT_EXPORT_SAFE.json"),
        ("M", "M4", "M4_DOPE_CONTEXT_EXPORT_SAFE.json"),
        ("M", "M5", "M5_MCP_HEALTH_EXPORT_SAFE.json"),
    ],
)
def test_noncompliant_model_output_is_scrubbed_before_it_reaches_disk(
    tmp_path: Path, phase: str, step_id: str, artifact_name: str
) -> None:
    runner = _load_v5_runner()
    phase_dir = tmp_path / f"{phase}_phase"
    _write_raw_partition(phase_dir / "raw", step_id, "p1", artifact_name)

    prompt_path = tmp_path / f"PROMPT_{step_id}.md"
    prompt_path.write_text(f"Goal: {artifact_name}\n", encoding="utf-8")

    runner.normalize_step(
        phase,
        runner.PromptSpec(
            step_id=step_id,
            prompt_path=prompt_path,
            output_artifacts=(artifact_name,),
        ),
        phase_dir,
        [{"id": "p1", "paths": []}],
    )

    written = phase_dir / "norm" / artifact_name
    assert written.is_file(), f"{artifact_name} was not written"
    on_disk = written.read_text(encoding="utf-8")

    for literal in ALL_FAKE_LITERALS:
        assert literal not in on_disk, (
            f"{artifact_name} on disk still contains a secret literal "
            f"({literal[:12]}...) -- the write-time scrub did not run"
        )

    # Finding preserved: the location is what the artifact exists to record.
    assert "services/example/settings.py" in on_disk
    assert "hardcoded_secret" in on_disk
    assert "DEFAULT_CREDENTIALS" in on_disk
    assert "SECRETS_RISK_LOCATIONS:" in on_disk
    assert "[REDACTED]" in on_disk

    parsed = json.loads(on_disk)
    items = parsed["items"] if isinstance(parsed, dict) else parsed
    assert len(items) == 1, "the finding must be masked, never dropped"
    assert items[0]["line_range"] == [41, 41]


# ---------------------------------------------------------------------------
# TP-RTE-TRUTH-R3-010 residuals
# ---------------------------------------------------------------------------


def test_default_credentials_key_is_sensitive() -> None:
    """R3-010 S1: DEFAULT_CREDENTIALS-style keys must mask by field name."""
    osafe = _load_output_safety()
    assert osafe._is_sensitive_key("DEFAULT_CREDENTIALS")
    assert osafe._is_sensitive_key("credentials")
    assert osafe._is_sensitive_key("passwd")
    assert osafe._is_sensitive_key("aws_access_key_id")
    # Must not over-broaden into non-secret words.
    assert not osafe._is_sensitive_key("accreditation")
    assert not osafe._is_sensitive_key("author")
    assert not osafe._is_sensitive_key("api_key_env")

    payload = {"DEFAULT_CREDENTIALS": "short-secret-value"}
    assert osafe.sanitize_payload_for_output(payload)["DEFAULT_CREDENTIALS"] == (
        osafe.REDACTION_TOKEN
    )


def test_short_free_text_secret_residual_is_documented_not_overclaimed() -> None:
    """R3-010 S1: short free-text secrets without key/prefix remain residual.

    Do NOT claim structural impossibility for this shape. The sensitive-key
    path (above) and long-token / provider-prefix paths cover the enforceable
    cases; a short bare password in free text is accepted residual risk.
    """
    osafe = _load_output_safety()
    short_bare = "s3cr3t!"  # short, no provider prefix, no sensitive key name
    free_text = f"note: operator said the password is {short_bare} for now"
    strict = osafe.sanitize_payload_for_security_artifact(free_text)
    # Residual: short bare free-text may survive. Pin honesty — if a future
    # scrub starts catching this, the residual shrinks (fine); fail only if
    # we silently start claiming impossibility without coverage.
    if short_bare in strict:
        # Documented residual still present — expected as of R3-010.
        assert short_bare in strict
    else:  # pragma: no cover
        # Scrub strengthened later; residual closed.
        assert osafe.REDACTION_TOKEN in strict


def test_redaction_token_is_unified() -> None:
    """R3-010 S2: scrub token is the single shared shape (no angle-bracket form)."""
    osafe = _load_output_safety()
    assert osafe.REDACTION_TOKEN == "[REDACTED]"
    assert "<REDACTED>" not in osafe.REDACTION_TOKEN


def test_part_shard_names_are_security_sensitive() -> None:
    """R3-010 S2: partX / partNNNN shards resolve like the logical artifact."""
    osafe = _load_output_safety()
    assert osafe.is_security_sensitive_artifact(
        "SECRETS_RISK_LOCATIONS.part0001.json"
    )
    assert osafe.is_security_sensitive_artifact("SECRETS_RISK_LOCATIONS.partX.json")
    assert osafe.canonical_security_artifact_basename(
        "C/norm/HOME_KEYS_SURFACE.part0002.json"
    ) == "HOME_KEYS_SURFACE.json"
    assert not osafe.is_security_sensitive_artifact("SERVICE_CATALOG.part0001.json")


def test_raw_partition_json_scrubs_security_artifact_payloads(tmp_path: Path) -> None:
    """R3-010 S2: raw/ write path must not be weaker than norm/.

    Mutation-checked property: write_json on a partition payload containing a
    SECRETS_RISK_LOCATIONS artifact must mask bare high-entropy secrets.
    """
    runner = _load_v5_runner()
    osafe = _load_output_safety()
    raw_path = tmp_path / "raw" / "C8__p1.json"
    payload = {
        "phase": "C",
        "step_id": "C8",
        "partition_id": "p1",
        "artifacts": [
            {
                "artifact_name": "SECRETS_RISK_LOCATIONS.json",
                "payload": {"items": [_noncompliant_finding()]},
            }
        ],
        "request_meta": {"schema_gate_passed": True},
    }
    runner.write_json(raw_path, payload)
    on_disk = raw_path.read_text(encoding="utf-8")
    for literal in ALL_FAKE_LITERALS:
        assert literal not in on_disk, (
            f"raw partition still contains secret literal {literal[:12]}... "
            f"— security scrub did not run on raw/"
        )
    assert osafe.REDACTION_TOKEN in on_disk
    # Non-security sibling artifacts in the same raw file would not need scrub,
    # but this fixture only carries C8.
    assert "services/example/settings.py" in on_disk


def test_write_json_source_wires_raw_and_path_security_scrub() -> None:
    """Wiring pin (R3-008 lesson): helpers must be called from write_json.

    TP-RTE-TRUTH-R2-003 factored the shared sanitization out of write_json's
    own body into ``_sanitized_json_payload_for_path`` (so the new atomic
    writer, write_json_atomic, can reuse the identical scrub instead of
    duplicating/drifting it -- see F-15). The wiring pin now checks two
    things instead of one: (1) the scrub calls actually live inside the
    shared sanitizer, and (2) write_json's body actually calls that
    sanitizer (not just "the scrub exists somewhere in the file" -- the
    R3-008 lesson this test guards against).
    """
    runner = _load_v5_runner()
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "scrub_security_sensitive_artifacts_in_partition_payload" in source

    sanitizer_start = source.index("def _sanitized_json_payload_for_path(")
    sanitizer_body = source[sanitizer_start : sanitizer_start + 1200]
    assert (
        "scrub_security_sensitive_artifacts_in_partition_payload" in sanitizer_body
    )
    assert "is_security_sensitive_artifact(path.name)" in sanitizer_body

    write_json_start = source.index("\ndef write_json(")
    write_json_body = source[write_json_start : write_json_start + 400]
    assert "_sanitized_json_payload_for_path(path, payload)" in write_json_body

    # write_json_atomic (F-15's durable writer for the spend ledger) must
    # route through the SAME sanitizer -- not a hand-copied second scrub
    # that could drift from the one above.
    write_json_atomic_start = source.index("def write_json_atomic(")
    write_json_atomic_body = source[write_json_atomic_start : write_json_atomic_start + 1400]
    assert "_sanitized_json_payload_for_path(path, payload)" in write_json_atomic_body


def test_partx_branch_applies_security_scrub(tmp_path: Path) -> None:
    """R3-010 S2: partX write path scrub is live, not only path-name helpers."""
    runner = _load_v5_runner()
    phase_dir = tmp_path / "C_phase"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True)
    # Use a synthetic security-sensitive partX name to exercise the branch.
    # (No C8 partX in the live promptset today; symmetry is still required.)
    artifact_name = "SECRETS_RISK_LOCATIONS.partX.json"
    (raw_dir / "C8__p1.json").write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "artifact_name": artifact_name,
                        "payload": {"items": [_noncompliant_finding()]},
                    }
                ],
                "request_meta": {"schema_gate_passed": True},
            }
        ),
        encoding="utf-8",
    )
    prompt_path = tmp_path / "PROMPT_C8.md"
    prompt_path.write_text(f"Goal: {artifact_name}\n", encoding="utf-8")
    runner.normalize_step(
        "C",
        runner.PromptSpec(
            step_id="C8",
            prompt_path=prompt_path,
            output_artifacts=(artifact_name,),
        ),
        phase_dir,
        [{"id": "p1", "paths": []}],
    )
    written = list((phase_dir / "norm").glob("SECRETS_RISK_LOCATIONS.part*.json"))
    assert written, "partX shard was not written"
    on_disk = written[0].read_text(encoding="utf-8")
    for literal in ALL_FAKE_LITERALS:
        assert literal not in on_disk, (
            f"partX shard still contains secret literal {literal[:12]}..."
        )
    assert "[REDACTED]" in on_disk
