"""
Tests for the de-Dopemux boundary repair on schemas/project_control_plane/project_evidence_export.schema.json.

Covers:
- Schema meta-validates (Draft 2020-12).
- dcp_extension schemas (dopetask_packet_mapping, orchestrator_item) exist + meta-validate AND
  are absent from schemas/project_control_plane/.
- A real-runtime minimal export (generated_from_fixture=False, non-null head_sha) validates.
- The same instance with head_sha=None is REJECTED (runtime head_sha gate).
- An instance using old key names (dopetask_executed / live_task_orchestrator_written) is REJECTED.
- Each of the 3 fixture evidence_export.json files validates against the schema.
"""

import json
import pathlib

from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Path setup — resolved from this file so it works from any CWD.
# Repository root: tests/project_control_plane/test_*.py → 3 levels up.
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_PCP_SCHEMA_DIR = _REPO_ROOT / "schemas" / "project_control_plane"
_DCP_SCHEMA_DIR = _REPO_ROOT / "schemas" / "dcp_extension"
_EVIDENCE_SCHEMA_PATH = _PCP_SCHEMA_DIR / "project_evidence_export.schema.json"
_FIXTURE_DIR = _REPO_ROOT / "reports" / "project-control-plane" / "fixtures"


def _load_json(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


EVIDENCE_SCHEMA = _load_json(_EVIDENCE_SCHEMA_PATH)


def _errors(schema, instance):
    """Return all Draft 2020-12 validation errors for *instance* against *schema*."""
    return list(Draft202012Validator(schema).iter_errors(instance))


# ---------------------------------------------------------------------------
# Module-level helper: minimal valid real-runtime instance.
# generated_from_fixture=False so the head_sha gate activates.
# ---------------------------------------------------------------------------
def _minimal_runtime_instance(head_sha: str | None = "abc123def456") -> dict:
    """
    Build a fresh minimal instance that satisfies every required field.

    The schema's `required` list:
        schema_version, project_id, generated_from_fixture, profile_ref,
        repo_state, authority_docs, active_packet, status_ledger,
        proof_manifest, workflow_list, pr_review_state, red_lane_results,
        unknowns, dirty_state, forbidden_action_confirmation
    """
    return {
        "schema_version": "pcp.project_evidence_export.v0",
        "project_id": "test-runtime-project",
        "generated_from_fixture": False,
        "profile_ref": "reports/test/project_profile.json",
        "repo_state": {
            "root_verified": True,
            "worktree_state": "CLEAN",
            "head_sha": head_sha,
            "branch": "main",
        },
        "authority_docs": [
            {"path": "AGENTS.md", "state": "PRESENT"},
        ],
        "active_packet": {
            "state": "PRESENT",
            "packet_id": "TP-TEST-0001",
            "path": "task-packets/TP-TEST-0001.json",
        },
        "status_ledger": {
            "state": "PRESENT",
            "path": "status/ledger.json",
            "entries": [{"id": "entry-001", "status": "READY_FOR_REVIEW"}],
        },
        "proof_manifest": {
            "state": "PRESENT",
            "path": "proof/TP-TEST-0001/PROOF.json",
            "freshness": "CURRENT",
        },
        "workflow_list": [
            {"id": "wf-001", "status": "DRY_RUN_ONLY", "source": "fixture"},
        ],
        "pr_review_state": {
            "state": "PRESENT",
            "authority_allowed": False,
            "open_prs": [],
        },
        "red_lane_results": [
            {"lane_id": "test-lane", "result": "PASS", "evidence": "test evidence"},
        ],
        "unknowns": [],
        "dirty_state": {
            "state": "CLEAN",
            "paths": [],
        },
        "forbidden_action_confirmation": {
            "external_workflow_written": False,
            "external_runner_executed": False,
            "github_mutated": False,
            "runtime_written": False,
        },
    }


# ---------------------------------------------------------------------------
# 1. Schema meta-validates (Draft 2020-12).
# ---------------------------------------------------------------------------
class TestSchemaMetaValidation:
    def test_evidence_export_schema_meta_validates(self):
        """project_evidence_export.schema.json must be a valid Draft 2020-12 schema."""
        Draft202012Validator.check_schema(EVIDENCE_SCHEMA)


# ---------------------------------------------------------------------------
# 2. DCP extension schemas exist + meta-validate AND are absent from pcp core dir.
# ---------------------------------------------------------------------------
class TestDcpExtensionSchemaPlacement:
    def test_dopetask_packet_mapping_exists_in_dcp_extension(self):
        path = _DCP_SCHEMA_DIR / "dopetask_packet_mapping.schema.json"
        assert path.exists(), f"Expected {path} to exist"

    def test_orchestrator_item_exists_in_dcp_extension(self):
        path = _DCP_SCHEMA_DIR / "orchestrator_item.schema.json"
        assert path.exists(), f"Expected {path} to exist"

    def test_dopetask_packet_mapping_meta_validates(self):
        schema = _load_json(_DCP_SCHEMA_DIR / "dopetask_packet_mapping.schema.json")
        Draft202012Validator.check_schema(schema)

    def test_orchestrator_item_meta_validates(self):
        schema = _load_json(_DCP_SCHEMA_DIR / "orchestrator_item.schema.json")
        Draft202012Validator.check_schema(schema)

    def test_dopetask_packet_mapping_absent_from_pcp_core(self):
        path = _PCP_SCHEMA_DIR / "dopetask_packet_mapping.schema.json"
        assert not path.exists(), (
            f"{path} must NOT exist in schemas/project_control_plane/ "
            "(it belongs in schemas/dcp_extension/)"
        )

    def test_orchestrator_item_absent_from_pcp_core(self):
        path = _PCP_SCHEMA_DIR / "orchestrator_item.schema.json"
        assert not path.exists(), (
            f"{path} must NOT exist in schemas/project_control_plane/ "
            "(it belongs in schemas/dcp_extension/)"
        )


# ---------------------------------------------------------------------------
# 3. A real-runtime minimal export validates.
# ---------------------------------------------------------------------------
class TestRuntimeMinimalExport:
    def test_runtime_instance_with_valid_head_sha_validates(self):
        """generated_from_fixture=False with a non-empty head_sha must produce zero errors."""
        inst = _minimal_runtime_instance(head_sha="abc123def456")
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs == [], f"Unexpected errors: {errs}"


# ---------------------------------------------------------------------------
# 4. head_sha=None with generated_from_fixture=False is REJECTED.
# ---------------------------------------------------------------------------
class TestRuntimeHeadShaGate:
    def test_runtime_instance_with_null_head_sha_is_rejected(self):
        """Runtime head_sha gate: generated_from_fixture=False, head_sha=None must be rejected."""
        inst = _minimal_runtime_instance(head_sha=None)
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs, (
            "Expected at least one validation error when generated_from_fixture=False "
            "and head_sha=None, but got zero errors"
        )

    def test_runtime_instance_with_missing_head_sha_key_is_rejected(self):
        """Hardened gate: a runtime export must include repo_state.head_sha (key present)."""
        inst = _minimal_runtime_instance()
        del inst["repo_state"]["head_sha"]
        assert _errors(EVIDENCE_SCHEMA, inst), (
            "Expected rejection when generated_from_fixture=False and repo_state.head_sha is absent"
        )

    def test_runtime_instance_with_missing_repo_state_is_rejected(self):
        """Hardened gate: a runtime export must include repo_state."""
        inst = _minimal_runtime_instance()
        del inst["repo_state"]
        assert _errors(EVIDENCE_SCHEMA, inst), (
            "Expected rejection when generated_from_fixture=False and repo_state is absent"
        )


# ---------------------------------------------------------------------------
# 5. Old key names (dopetask_executed / live_task_orchestrator_written) are REJECTED.
# ---------------------------------------------------------------------------
class TestOldKeyNamesRejected:
    def test_old_dopetask_executed_key_is_rejected(self):
        """forbidden_action_confirmation.dopetask_executed (old name) must be rejected."""
        inst = _minimal_runtime_instance()
        inst["forbidden_action_confirmation"] = {
            "dopetask_executed": False,
            "external_workflow_written": False,
            "github_mutated": False,
            "runtime_written": False,
        }
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs, (
            "Expected rejection for old key name 'dopetask_executed' in "
            "forbidden_action_confirmation"
        )

    def test_old_live_task_orchestrator_written_key_is_rejected(self):
        """forbidden_action_confirmation.live_task_orchestrator_written (old name) must be rejected."""
        inst = _minimal_runtime_instance()
        inst["forbidden_action_confirmation"] = {
            "live_task_orchestrator_written": False,
            "external_runner_executed": False,
            "github_mutated": False,
            "runtime_written": False,
        }
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs, (
            "Expected rejection for old key name 'live_task_orchestrator_written' in "
            "forbidden_action_confirmation"
        )

    def test_both_old_key_names_together_are_rejected(self):
        """Using both old key names must be rejected (additionalProperties + missing required)."""
        inst = _minimal_runtime_instance()
        inst["forbidden_action_confirmation"] = {
            "dopetask_executed": False,
            "live_task_orchestrator_written": False,
            "github_mutated": False,
            "runtime_written": False,
        }
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs, (
            "Expected rejection when both old key names are present in "
            "forbidden_action_confirmation"
        )


# ---------------------------------------------------------------------------
# 6. Each of the 3 fixture evidence_export.json files validates.
# ---------------------------------------------------------------------------
class TestFixtureFilesValidate:
    def test_dnh_crm_fixture_validates(self):
        inst = _load_json(_FIXTURE_DIR / "dnh_crm_fixture" / "evidence_export.json")
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs == [], f"dnh_crm_fixture/evidence_export.json errors: {errs}"

    def test_dopemux_fixture_validates(self):
        inst = _load_json(_FIXTURE_DIR / "dopemux_fixture" / "evidence_export.json")
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs == [], f"dopemux_fixture/evidence_export.json errors: {errs}"

    def test_minimal_fixture_validates(self):
        inst = _load_json(_FIXTURE_DIR / "minimal_fixture" / "evidence_export.json")
        errs = _errors(EVIDENCE_SCHEMA, inst)
        assert errs == [], f"minimal_fixture/evidence_export.json errors: {errs}"
