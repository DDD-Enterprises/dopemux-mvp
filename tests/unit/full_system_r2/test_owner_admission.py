"""Native authority is not supplied by schema, digest or caller strings."""

import dataclasses
import json
from pathlib import Path
import tempfile
import unittest

from .fixtures import owner_fixture, write_json


class OwnerAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / "owner"
        from dopemux.governed_execution.admission.owner_admission import (
            OwnerAdmitter,
            AdmissionError,
        )
        from dopemux.governed_execution.admission.local_owner import LocalOwnerResolver

        self.Error = AdmissionError
        self.scope, self.ref, self.config = owner_fixture(self.root)
        self.resolver = LocalOwnerResolver(self.root, fixture_mode=True)
        self.admitter = OwnerAdmitter("NATIVE_CT", self.resolver)

    def admit(self, **changes):
        values = dict(
            receipt_ref=self.ref,
            principal_ref="fixture-actor",
            expected_scope=self.scope,
            expected_generation=1,
        )
        values.update(changes)
        return self.admitter.admit(**values)

    def test_forged_matching_shape_has_no_admission(self):
        with self.assertRaises(self.Error) as caught:
            self.admit(principal_ref="forged-principal")
        self.assertEqual(caught.exception.code, "E_AUTHENTICITY")

    def test_genuine_fixture_maps_original_canonical_schema_without_authority(self):
        result = self.admit()
        self.assertEqual(result.projection["decision"], "ADMITTED")
        self.assertEqual(result.projection["authority"], "NONE")
        self.assertTrue(result.fixture_only)
        self.assertTrue(
            result.canonical_receipt.provenance.verified_by.startswith("SYNTHETIC_FIXTURE:")
        )
        self.assertEqual(result.canonical_receipt.kind, "dispatch_input_receipt.v1")

    def test_wrong_role_cannot_supply_native_receipt(self):
        self.config["owner_domain"] = "MASTER"
        write_json(self.root / "owner.json", self.config)
        with self.assertRaises(self.Error) as caught:
            self.admit()
        self.assertEqual(caught.exception.code, "E_ROLE")

    def test_revocation_after_validation_blocks_recheck(self):
        result = self.admit()
        self.config["revoked"] = True
        write_json(self.root / "owner.json", self.config)
        with self.assertRaises(self.Error) as caught:
            self.admitter.recheck(result)
        self.assertEqual(caught.exception.code, "E_REVOKED")

    def test_generation_and_identity_drift_fail_closed(self):
        for field, value in [
            ("project_id", "foreign-project"),
            ("worktree", "/tmp"),
            ("subject_digest", "9" * 64),
            ("trust_digest", "9" * 64),
        ]:
            with self.subTest(field=field), self.assertRaises(self.Error):
                self.admit(expected_scope=dataclasses.replace(self.scope, **{field: value}))
        with self.assertRaises(self.Error) as caught:
            self.admit(expected_generation=2)
        self.assertEqual(caught.exception.code, "E_STALE")

    def test_delegation_cannot_widen_effects_resources_funding_time_or_attempts(self):
        for update in [
            {"effects": ("publish",)},
            {"resources": ("foreign",)},
            {"route_refs": ("unqualified-route",)},
            {"active_seconds": 61},
            {"wall_seconds": 91},
            {"spend_limit_micros": 1},
            {"max_attempts": 5},
            {"repair_limit": 2},
            {"delegation_depth": 3},
        ]:
            with self.subTest(update=update), self.assertRaises(self.Error):
                self.admit(expected_scope=dataclasses.replace(self.scope, **update))
        narrowed = dataclasses.replace(self.scope, effects=("read",), active_seconds=30)
        self.assertEqual(self.admit(expected_scope=narrowed).scope, narrowed)

    def test_expired_and_tampered_owner_records_rejected(self):
        self.config["expires_at"] = 1
        write_json(self.root / "owner.json", self.config)
        with self.assertRaises(self.Error):
            self.admit()
        self.config["expires_at"] = self.scope.expires_at
        write_json(self.root / "owner.json", self.config)
        (self.root / "receipt.json").write_text('{"scope_status":"PASS"}')
        with self.assertRaises(self.Error):
            self.admit()

    def test_unconfigured_live_owner_cannot_be_replaced_by_fixture(self):
        from dopemux.governed_execution.admission.local_owner import LocalOwnerResolver

        with self.assertRaises(self.Error):
            LocalOwnerResolver(self.root).resolve(self.ref, "fixture-actor")

    def test_permissive_root_and_duplicate_keys_are_rejected(self):
        self.root.chmod(0o755)
        with self.assertRaises(self.Error):
            self.admit()
        self.root.chmod(0o700)
        (self.root / "owner.json").write_text('{"fixture_only":true,"fixture_only":false}')
        with self.assertRaises(self.Error):
            self.admit()

    def test_unknown_native_kind_duplicate_keys_and_nonfinite_are_rejected(self):
        from dopemux.governed_execution.admission.owner_admission import strict_json

        for raw in [b'{"x":1,"x":2}', b'{"value":NaN}', b'{"value":Infinity}']:
            with self.subTest(raw=raw), self.assertRaises(self.Error):
                strict_json(raw)
        self.config["receipts"][self.ref["ref_id"]]["kind"] = "unknown.v999"
        write_json(self.root / "owner.json", self.config)
        with self.assertRaises(self.Error):
            self.admit()

    def test_malformed_typed_input_does_not_reach_owner_port(self):
        class ForbiddenPort:
            def resolve(self, *args):
                raise AssertionError("Malformed input reached owner I/O")

        from dopemux.governed_execution.admission.owner_admission import OwnerAdmitter

        admitter = OwnerAdmitter("NATIVE_CT", ForbiddenPort())
        for arguments in [
            (self.ref, [], self.scope, 1),
            (self.ref, "fixture-actor", self.scope, True),
            (self.ref, "fixture-actor", {}, 1),
            ({"ref_id": "bad"}, "fixture-actor", self.scope, 1),
        ]:
            with self.subTest(arguments=arguments), self.assertRaises(self.Error):
                admitter.admit(*arguments)

    def test_malformed_nested_owner_data_returns_typed_errors(self):
        import copy

        cases = []
        for field, value in [
            ("principals", []),
            ("receipts", []),
            ("generation", True),
            ("registry_file", None),
            ("revoked", "false"),
        ]:
            changed = copy.deepcopy(self.config)
            changed[field] = value
            cases.append(changed)
        changed = copy.deepcopy(self.config)
        changed["receipts"][self.ref["ref_id"]]["delegation_depth_limit"] = "unlimited"
        cases.append(changed)
        for changed in cases:
            write_json(self.root / "owner.json", changed)
            with self.subTest(changed=changed), self.assertRaises(self.Error):
                self.admit()

    def test_fixture_cli_cannot_authorize_execution(self):
        import subprocess
        import sys
        from .fixtures import canonical

        request = {
            "receipt_ref": self.ref,
            "principal_ref": "fixture-actor",
            "expected_scope": dataclasses.asdict(self.scope),
            "expected_generation": 1,
            "owner_domain": "NATIVE_CT",
        }
        request_path = self.root / "request.json"
        request_path.write_bytes(canonical(request))
        command = [
            sys.executable,
            "-B",
            "-m",
            "dopemux.governed_execution.admission",
            "check-fixture",
            "--owner-root",
            str(self.root),
            "--request",
            str(request_path),
        ]
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.root),
            "TMPDIR": str(self.root),
            "PYTHONPATH": str(Path(__file__).resolve().parents[3] / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHON_DOTENV_DISABLED": "1",
        }
        result = subprocess.run(command, capture_output=True, timeout=10, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertIs(envelope["execution_authorized"], False)
        self.assertIs(envelope["fixture_only"], True)
        self.assertEqual(envelope["admission"]["authority"], "NONE")
        request_path.write_text('{"owner_domain":"NATIVE_CT","owner_domain":"MASTER"}')
        invalid = subprocess.run(command, capture_output=True, timeout=10, env=env)
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(json.loads(invalid.stderr)["code"], "E_SCHEMA")

    def test_unsupported_original_version_rejects_even_with_matching_source_hash(self):
        import hashlib

        source = json.loads((self.root / "receipt.json").read_bytes())
        source["schema_version"] = "dopemux.governed_execution.dispatch_input_receipt.v999"
        write_json(self.root / "receipt.json", source)
        self.ref["sha256"] = hashlib.sha256((self.root / "receipt.json").read_bytes()).hexdigest()
        self.config["receipts"][self.ref["ref_id"]]["evidence"] = self.ref
        write_json(self.root / "owner.json", self.config)
        with self.assertRaises(self.Error) as caught:
            self.admit()
        self.assertEqual(caught.exception.code, "E_UNSUPPORTED_VERSION")

    def test_unmapped_reference_cannot_be_authenticated_by_matching_bytes(self):
        forged = dict(self.ref, ref_id="foreign-mapped-looking-receipt")
        with self.assertRaises(self.Error) as caught:
            self.admit(receipt_ref=forged)
        self.assertEqual(caught.exception.code, "E_AUTHENTICITY")

    def test_bare_pass_and_foreign_waiver_are_not_native_scope_authority(self):
        import hashlib

        original = json.loads((self.root / "receipt.json").read_bytes())
        waiver = dict(original, waiver={"issuer": "MASTER", "grant": "all"})
        for source in [
            {"scope_status": "PASS", "allowlist_digest": original["allowlist_digest"]},
            waiver,
        ]:
            write_json(self.root / "receipt.json", source)
            self.ref["sha256"] = hashlib.sha256(
                (self.root / "receipt.json").read_bytes()
            ).hexdigest()
            self.config["receipts"][self.ref["ref_id"]]["evidence"] = self.ref
            write_json(self.root / "owner.json", self.config)
            with self.subTest(source=source), self.assertRaises(self.Error):
                self.admit()
