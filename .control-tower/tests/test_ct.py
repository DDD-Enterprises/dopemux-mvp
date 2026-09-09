#!/usr/bin/env python3
"""Adversarial regression tests for the repository-installed Control Tower CLI."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import warnings
import zipfile
from copy import deepcopy
from argparse import Namespace
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
CT_PATH = REPO / ".control-tower" / "bin" / "ct"
LOADER = SourceFileLoader("control_tower_ct_clean_r1", str(CT_PATH))
SPEC = importlib.util.spec_from_loader("control_tower_ct_clean_r1", LOADER)
ct = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ct)


def valid_route(packet_id: str = "TP-TEST-001") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "packet_id": packet_id,
        "stage": "repair",
        "risk_lane": "L2",
        "selection": {
            "runner": "codex",
            "runner_availability": "PROVEN",
            "agent_role": "implementer",
            "custom_agent": None,
            "model": "test-model",
            "effort": "medium",
        },
        "justification": {
            "why_runner": "probe passed",
            "why_model": "authorized",
            "why_effort": "bounded",
            "cost_latency_tradeoff": "unknown",
            "alternatives_considered": [
                {"route": "shell", "disposition": "reserved", "reason": "semantic work"}
            ],
            "evidence": [],
        },
        "fallback": {"runner": None, "model": None, "trigger": None},
        "audit": {
            "required": True,
            "runner": "DEFERRED_NON_CODEX",
            "model": "UNKNOWN_NOT_SELECTED",
            "effort": "UNKNOWN_NOT_SELECTED",
            "independence": "DEFERRED_NOT_INVOKED",
            "rationale": "after freeze",
        },
        "recorded_at": "20260909T000000Z",
    }


class ControlTowerTests(unittest.TestCase):
    def _packaging_repo(self, root: Path, packet_id: str = "TP-PACK-001") -> tuple[Path, Path]:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/DDD-Enterprises/demo.git"], cwd=repo, check=True)
        (repo / ".dopetaskroot").write_text("")
        control = repo / ".control-tower"
        (control / "state" / "routes").mkdir(parents=True)
        (control / "schemas").mkdir()
        (control / "templates").mkdir()
        shutil.copy2(REPO / ".control-tower/schemas/route_decision.schema.json", control / "schemas")
        shutil.copy2(REPO / ".control-tower/schemas/execution_binding.schema.json", control / "schemas")
        shutil.copy2(REPO / ".control-tower/schemas/return_packet.schema.json", control / "schemas")
        shutil.copy2(
            REPO / ".control-tower/templates/ARCHITECTURE_RETURN_PACKET.template.md",
            control / "templates",
        )
        output = root / "output"
        output.mkdir()
        (control / "project.json").write_text(
            json.dumps(
                {
                    "project_name": "demo",
                    "downloads": {"proof": str(output), "return": str(output)},
                }
            )
        )
        (control / "state" / "routes" / f"{packet_id}.json").write_text(
            json.dumps(valid_route(packet_id))
        )
        packet = repo / "packet.json"
        packet.write_text(
            json.dumps(
                {
                    "id": packet_id,
                    "repo_binding": {
                        "project_id": "demo",
                        "repo_marker": ".dopetaskroot",
                        "origin_hint": "DDD-Enterprises/demo",
                        "require_identity_match": True,
                    },
                }
            )
        )
        (repo / "payload.txt").write_text("safe\n")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repo, check=True)
        subprocess.run(["git", "branch", "origin/main"], cwd=repo, check=True)
        return repo, packet

    @staticmethod
    def _pack_args(packet_id: str, packet: Path, **overrides: object) -> Namespace:
        values = {
            "packet_id": packet_id,
            "packet": str(packet),
            "proof_dir": None,
            "include": [],
            "reason": None,
            "decision_needed": None,
        }
        values.update(overrides)
        return Namespace(**values)

    def test_schema_validation_uses_installed_schema_and_rejects_unknown_keywords(self) -> None:
        route = valid_route()
        route["schema_version"] = "9.9"
        self.assertTrue(ct.validate_route_obj(route, REPO))

        absent_property = {
            "type": "object",
            "properties": {"unused": {"futureKeyword": True}},
        }
        self.assertIn("unsupported schema keyword", " ".join(ct.schema_errors({}, absent_property)))

        empty_items = {"type": "array", "items": {"futureKeyword": True}}
        self.assertIn("unsupported schema keyword", " ".join(ct.schema_errors([], empty_items)))

    def test_schema_and_route_policy_are_separate(self) -> None:
        route = valid_route()
        route["risk_lane"] = "L2"
        route["audit"] = {"required": False}
        errors = ct.validate_route_obj(route, REPO)
        self.assertTrue(any("L2 requires audit.required=true" in error for error in errors))

    def test_tool_is_proven_only_after_successful_probe(self) -> None:
        failed = {"returncode": 1, "stdout": "", "stderr": "failed"}
        with mock.patch.object(ct.shutil, "which", return_value="/tmp/tool"), mock.patch.object(
            ct, "run", return_value=failed
        ):
            info = ct.tool_info("tool", ["--version"])
        self.assertEqual("UNKNOWN", info["availability"])
        self.assertEqual(1, info["returncode"])

    def test_runner_inventory_model_discovery_is_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".control-tower" / "state").mkdir(parents=True)
            calls: list[list[str]] = []

            def fake_run(command: list[str], cwd: Path | None = None) -> dict[str, object]:
                calls.append(command)
                return {"returncode": 0, "stdout": "ok", "stderr": ""}

            with mock.patch.object(ct, "repo_root", return_value=root), mock.patch.object(
                ct, "run", side_effect=fake_run
            ), mock.patch.object(ct.shutil, "which", return_value="/tmp/tool"):
                self.assertEqual(0, ct.cmd_runner_inventory(Namespace(probe_models=False)))
            self.assertNotIn(["agy", "models"], calls)

    def test_stream_scan_accepts_clean_large_file_and_blocks_large_secret(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            clean = root / "clean.bin"
            clean.write_bytes(b"x" * 20_000_001)
            digest, size = ct.scan_regular_file(clean)
            self.assertEqual(20_000_001, size)
            self.assertEqual(hashlib.sha256(clean.read_bytes()).hexdigest(), digest)

            secret = root / "secret.bin"
            secret.write_bytes(b"x" * 20_000_001 + b"\n" + b"sk-" + b"A" * 24)
            with self.assertRaisesRegex(ct.PackageBlocked, "OPENAI_KEY"):
                ct.scan_regular_file(secret)

    def test_stream_scan_blocks_secret_across_chunk_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "boundary.bin"
            path.write_bytes(b"x" * (ct.CHUNK_SIZE - 2) + b"\n poetry " + b"sk-" + b"B" * 24)
            with self.assertRaisesRegex(ct.PackageBlocked, "OPENAI_KEY"):
                ct.scan_regular_file(path)

            assignment = Path(raw) / "assignment.bin"
            assignment.write_bytes(
                b"token" + b" " * (ct.CHUNK_SIZE * 2) + b"=" + b" " * ct.CHUNK_SIZE + b"C" * 24
            )
            with self.assertRaisesRegex(ct.PackageBlocked, "SECRET_ASSIGNMENT"):
                ct.scan_regular_file(assignment)

            nested = Path(raw) / "nested-assignment.bin"
            nested.write_bytes(
                b"token=example-token" + b" " * (ct.CHUNK_SIZE * 2) + b"=" + b" " * ct.CHUNK_SIZE + b"N" * 24
            )
            with self.assertRaisesRegex(ct.PackageBlocked, "SECRET_ASSIGNMENT"):
                ct.scan_regular_file(nested)

            long_openai = Path(raw) / "long-openai-token.bin"
            long_openai.write_bytes(b" sk-" + b"-" * (ct.CHUNK_SIZE * 2) + b"A ")
            with self.assertRaisesRegex(ct.PackageBlocked, "OPENAI_KEY"):
                ct.scan_regular_file(long_openai)

    def test_stream_scan_preserves_all_detector_boundaries(self) -> None:
        cases = {
            "private": (b"-----BEGIN OPENSSH " + b"PRIVATE KEY-----", "PRIVATE_KEY"),
            "github": (b"ghp_" + b"A" * 24, "GITHUB_TOKEN"),
            "openai": (b"sk-" + b"B" * 24, "OPENAI_KEY"),
            "aws": (b"AKIA" + b"C" * 16, "AWS_ACCESS_KEY"),
            "hyphen-assignment": (b"x-token = " + b"D" * 24, "SECRET_ASSIGNMENT"),
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name, (candidate, pattern) in cases.items():
                path = root / name
                path.write_bytes(b"x" * (ct.CHUNK_SIZE - 1) + b"\n" + candidate)
                with self.assertRaisesRegex(ct.PackageBlocked, pattern, msg=name):
                    ct.scan_regular_file(path)

            placeholder = root / "placeholder"
            placeholder.write_bytes(b"token = ${EXAMPLE_TOKEN_VALUE}")
            ct.scan_regular_file(placeholder)

    def test_staged_tree_traversal_errors_block(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with mock.patch.object(ct.os, "walk", side_effect=OSError("denied")):
                with self.assertRaisesRegex(ct.PackageBlocked, "traversal"):
                    ct.scan_staged_tree(root)

    def test_stream_scan_blocks_unreadable_and_partial_reads(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "input.bin"
            path.write_bytes(b"safe bytes")
            real_read = os.read

            with mock.patch.object(ct.os, "read", side_effect=OSError("denied")):
                with self.assertRaisesRegex(ct.PackageBlocked, "unreadable"):
                    ct.scan_regular_file(path)

            calls = 0

            def partial_read(fd: int, size: int) -> bytes:
                nonlocal calls
                calls += 1
                return real_read(fd, 4) if calls == 1 else b""

            with mock.patch.object(ct.os, "read", side_effect=partial_read):
                with self.assertRaisesRegex(ct.PackageBlocked, "partial read"):
                    ct.scan_regular_file(path)

    def test_markdown_packet_identity_is_authoritative_and_unambiguous(self) -> None:
        cases = {
            "colon.md": "# Task Packet: `TP-COLON-001`\n",
            "emdash.md": "# Task Packet — `TP-EMDASH-001`\n",
            "hyphen.md": "# Task Packet - TP-HYPHEN-001\n",
            "frontmatter.md": "---\nid: TP-FRONT-001\n---\n# Task Packet: `TP-FRONT-001`\n",
            "packet-id.md": "---\npacket_id: TP-PACKET-ID-001\n---\n# Task Packet: TP-PACKET-ID-001\n",
            "task-packet-id.md": "---\ntask_packet_id: TP-TASK-PACKET-ID-001\n---\n# Task Packet: TP-TASK-PACKET-ID-001\n",
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name, content in cases.items():
                path = root / name
                path.write_text(content)
                self.assertTrue(ct.packet_identity(path).startswith("TP-"))

            real_packet = REPO / "task-packets" / "DMX-DCP-MODEL-ROUTING-MVP-0007T.md"
            self.assertEqual("DMX-DCP-MODEL-ROUTING-MVP-0007T", ct.packet_identity(real_packet))

            conflict = root / "conflict.md"
            conflict.write_text("---\nid: TP-ONE-001\n---\n# Task Packet: `TP-TWO-001`\n")
            with self.assertRaisesRegex(ct.PacketIdentityError, "BLOCK_PACKET_IDENTITY_AMBIGUOUS"):
                ct.packet_identity(conflict)

            metadata_conflict = root / "metadata-conflict.md"
            metadata_conflict.write_text(
                "# Task Packet: TP-ONE-001\n\n## Packet metadata\n\n```text\npacket_id: TP-TWO-001\n```\n"
            )
            with self.assertRaisesRegex(ct.PacketIdentityError, "BLOCK_PACKET_IDENTITY_AMBIGUOUS"):
                ct.packet_identity(metadata_conflict)

            generic = root / "generic.md"
            generic.write_text("# TP-GENERIC-001\n\nPacket metadata: TP-GENERIC-001\n")
            with self.assertRaisesRegex(ct.PacketIdentityError, "BLOCK_PACKET_IDENTITY_MISSING"):
                ct.packet_identity(generic)

    def test_json_packet_identity_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            packet = Path(raw) / "packet.json"
            packet.write_text('{"id":"TP-ONE-001","id":"TP-TWO-001"}')
            with self.assertRaisesRegex(ct.PackageBlocked, "duplicate JSON key"):
                ct.packet_identity(packet)

    def test_json_packet_repository_binding_uses_installed_identity_and_origin(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / ".control-tower").mkdir()
            (repo / ".control-tower" / "project.json").write_text(
                json.dumps({"project_name": "demo"})
            )
            (repo / ".dopetaskroot").write_text("")
            packet = repo / "packet.json"

            def write_binding(project: str, marker: str, origin: str) -> None:
                packet.write_text(
                    json.dumps(
                        {
                            "id": "TP-BIND-001",
                            "repo_binding": {
                                "project_id": project,
                                "repo_marker": marker,
                                "origin_hint": origin,
                                "require_identity_match": True,
                            },
                        }
                    )
                )

            write_binding("demo", ".dopetaskroot", "DDD-Enterprises/demo")
            with mock.patch.object(ct, "git_remote_url", return_value="git@github.com:DDD-Enterprises/demo.git"):
                ct.validate_packet_binding(repo, packet)

            for values in [
                ("wrong", ".dopetaskroot", "DDD-Enterprises/demo"),
                ("demo", ".missing", "DDD-Enterprises/demo"),
                ("demo", ".dopetaskroot", "DDD-Enterprises/wrong"),
            ]:
                write_binding(*values)
                with mock.patch.object(ct, "git_remote_url", return_value="https://github.com/DDD-Enterprises/demo.git"):
                    with self.assertRaisesRegex(ct.PackageBlocked, "BLOCKED_REPO_IDENTITY_MISMATCH"):
                        ct.validate_packet_binding(repo, packet)

            malformed = json.loads(packet.read_text())
            malformed["repo_binding"]["require_identity_match"] = "true"
            packet.write_text(json.dumps(malformed))
            with self.assertRaisesRegex(ct.PackageBlocked, "BLOCKED_REPO_IDENTITY_MISMATCH"):
                ct.validate_packet_binding(repo, packet)

            nested = repo / "config" / "identity.marker"
            nested.parent.mkdir()
            nested.write_text("")
            write_binding("demo", "config/identity.marker", "DDD-Enterprises/demo")
            with mock.patch.object(ct, "git_remote_url", return_value="https://github.com/DDD-Enterprises/demo.git"):
                ct.validate_packet_binding(repo, packet)

    def test_identity_chain_rejects_any_mismatch(self) -> None:
        ct.assert_matching_identities("TP-ONE-001", "TP-ONE-001", "TP-ONE-001")
        with self.assertRaisesRegex(ct.PackageBlocked, "BLOCK_PACKET_IDENTITY_MISMATCH"):
            ct.assert_matching_identities("TP-ONE-001", "TP-TWO-001")

    def test_return_metadata_requires_nonblank_fields_and_matches_schema(self) -> None:
        route = valid_route("TP-RETURN-001")
        state = {"head_sha": "a" * 40, "merge_base_origin_main": "b" * 40, "branch": "topic"}
        with self.assertRaisesRegex(ct.PackageBlocked, "reason"):
            ct.build_return_metadata("TP-RETURN-001", "stamp", "demo", " ", "decide", state, route)
        with self.assertRaisesRegex(ct.PackageBlocked, "decision_needed"):
            ct.build_return_metadata("TP-RETURN-001", "stamp", "demo", "reason", " ", state, route)

        metadata = ct.build_return_metadata(
            "TP-RETURN-001", "stamp", "demo", "reason", "decide", state, route
        )
        self.assertEqual([], ct.validate_return_metadata(metadata, REPO))

    @staticmethod
    def _write_valid_zip(path: Path, packet_id: str = "TP-ZIP-001") -> None:
        root = "PROOF_demo_TP-ZIP-001_stamp"
        files = {
            "TASK_PACKET.json": json.dumps({"id": packet_id}).encode() + b"\n",
            "ROUTING_DECISION.json": json.dumps({"packet_id": packet_id}).encode() + b"\n",
            "MANIFEST.json": json.dumps(
                {
                    "schema_version": "1.0",
                    "kind": "PROOF",
                    "packet_id": packet_id,
                    "project": "demo",
                    "package_root": root,
                    "task_packet_member": "TASK_PACKET.json",
                    "inventory_scope": "all members except FILE_INVENTORY.json and SHA256SUMS.txt",
                    "sha256sums_scope": "all members except SHA256SUMS.txt",
                }
            ).encode()
            + b"\n",
        }
        files["SECRET_SCAN_REPORT.json"] = json.dumps(
            {
                "status": "PASS",
                "files_scanned": len(files),
                "bytes_scanned": sum(len(data) for data in files.values()),
                "files_skipped": 0,
                "files_unreadable": 0,
                "scan_errors": 0,
            }
        ).encode() + b"\n"
        inventory = [
            {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in sorted(files.items())
        ]
        files["FILE_INVENTORY.json"] = json.dumps(inventory, indent=2).encode() + b"\n"
        sums = "".join(
            f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items())
        )
        files["SHA256SUMS.txt"] = sums.encode()
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in files.items():
                archive.writestr(f"{root}/{name}", data)

    @staticmethod
    def _rewrite_valid_zip(
        path: Path,
        mutate,
        *,
        rebuild: bool = True,
        root_override: str | None = None,
        special: tuple[zipfile.ZipInfo | str, bytes] | None = None,
    ) -> None:
        with zipfile.ZipFile(path) as source:
            names = source.namelist()
            old_root = names[0].split("/", 1)[0]
            files = {name.split("/", 1)[1]: source.read(name) for name in names}
        mutate(files)
        root = root_override or old_root
        if root_override:
            manifest = json.loads(files["MANIFEST.json"])
            manifest["package_root"] = root
            files["MANIFEST.json"] = json.dumps(manifest).encode() + b"\n"
        if rebuild:
            files.pop("FILE_INVENTORY.json", None)
            files.pop("SHA256SUMS.txt", None)
            report = json.loads(files["SECRET_SCAN_REPORT.json"])
            primary = {
                name: data
                for name, data in files.items()
                if name != "SECRET_SCAN_REPORT.json"
            }
            report["files_scanned"] = len(primary)
            report["bytes_scanned"] = sum(len(data) for data in primary.values())
            files["SECRET_SCAN_REPORT.json"] = json.dumps(report).encode() + b"\n"
            inventory = [
                {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                for name, data in sorted(files.items())
            ]
            files["FILE_INVENTORY.json"] = json.dumps(inventory, indent=2).encode() + b"\n"
            files["SHA256SUMS.txt"] = "".join(
                f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                for name, data in sorted(files.items())
            ).encode()
        replacement = path.with_suffix(".replacement.zip")
        with zipfile.ZipFile(replacement, "w", zipfile.ZIP_DEFLATED) as output:
            for name, data in files.items():
                output.writestr(f"{root}/{name}", data)
            if special:
                member, data = special
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    output.writestr(member, data)
        replacement.replace(path)

    def test_verify_zip_checks_structure_manifests_inventory_and_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            archive = Path(raw) / "valid.zip"
            self._write_valid_zip(archive)
            rc, message = ct.verify_zip_file(archive)
            self.assertEqual(0, rc, message)
            self.assertIn("manifests", message)

            tampered = Path(raw) / "tampered.zip"
            self._write_valid_zip(tampered)
            self._rewrite_valid_zip(
                tampered,
                lambda files: files.__setitem__("TASK_PACKET.json", b'{"id":"TP-OTHER"}'),
                rebuild=False,
            )
            self.assertIn("mismatch", ct.verify_zip_file(tampered)[1])

            identity = Path(raw) / "identity.zip"
            self._write_valid_zip(identity)
            self._rewrite_valid_zip(
                identity,
                lambda files: files.__setitem__(
                    "ROUTING_DECISION.json", b'{"packet_id":"TP-OTHER-001"}\n'
                ),
            )
            self.assertIn("IDENTITY_MISMATCH", ct.verify_zip_file(identity)[1])

            receipt = Path(raw) / "receipt.zip"
            self._write_valid_zip(receipt)
            self._rewrite_valid_zip(
                receipt,
                lambda files: files.__setitem__(
                    "SECRET_SCAN_REPORT.json",
                    b'{"status":"FAIL","files_skipped":0,"files_unreadable":0,"scan_errors":0}\n',
                ),
            )
            self.assertIn("PASS receipt", ct.verify_zip_file(receipt)[1])

            proof = Path(raw) / "proof.zip"
            self._write_valid_zip(proof)
            self._rewrite_valid_zip(
                proof, lambda files: files.__setitem__("PROOF_REVIEW/PROOF.json", b"{}\n")
            )
            self.assertIn("IDENTITY_MISSING", ct.verify_zip_file(proof)[1])

            root_mismatch = Path(raw) / "root-mismatch.zip"
            self._write_valid_zip(root_mismatch)
            self._rewrite_valid_zip(
                root_mismatch,
                lambda files: None,
                root_override="PROOF_demo_prefix-TP-ZIP-001-suffix_stamp",
            )
            self.assertIn("root identity mismatch", ct.verify_zip_file(root_mismatch)[1])

            missing = Path(raw) / "missing.zip"
            with zipfile.ZipFile(missing, "w") as output:
                output.writestr("root/payload.txt", b"safe")
            self.assertNotEqual(0, ct.verify_zip_file(missing)[0])

    def test_verify_zip_blocks_unsafe_duplicate_and_symlink_members(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            traversal = root / "traversal.zip"
            self._write_valid_zip(traversal)
            self._rewrite_valid_zip(
                traversal,
                lambda files: None,
                special=("PROOF_demo_TP-ZIP-001_stamp/../escape", b"safe"),
            )
            self.assertNotEqual(0, ct.verify_zip_file(traversal)[0])

            backslash = root / "backslash.zip"
            self._write_valid_zip(backslash)
            self._rewrite_valid_zip(
                backslash,
                lambda files: None,
                special=("PROOF_demo_TP-ZIP-001_stamp\\escape", b"safe"),
            )
            self.assertNotEqual(0, ct.verify_zip_file(backslash)[0])

            duplicate = root / "duplicate.zip"
            self._write_valid_zip(duplicate)
            self._rewrite_valid_zip(
                duplicate,
                lambda files: None,
                special=("PROOF_demo_TP-ZIP-001_stamp/TASK_PACKET.json", b"duplicate"),
            )
            self.assertNotEqual(0, ct.verify_zip_file(duplicate)[0])

            symlink = root / "symlink.zip"
            self._write_valid_zip(symlink)
            info = zipfile.ZipInfo("PROOF_demo_TP-ZIP-001_stamp/link")
            info.create_system = 3
            info.external_attr = 0o120777 << 16
            self._rewrite_valid_zip(symlink, lambda files: None, special=(info, b"target"))
            self.assertNotEqual(0, ct.verify_zip_file(symlink)[0])

            extra = root / "extra.zip"
            self._write_valid_zip(extra)
            self._rewrite_valid_zip(
                extra,
                lambda files: files.__setitem__("EXTRA.txt", b"extra"),
                rebuild=False,
            )
            self.assertIn("coverage mismatch", ct.verify_zip_file(extra)[1])

            alias = root / "alias.zip"
            self._write_valid_zip(alias)
            self._rewrite_valid_zip(
                alias,
                lambda files: None,
                special=(
                    "PROOF_demo_TP-ZIP-001_stamp/./TASK_PACKET.json",
                    b'{"id": "TP-ZIP-001"}\n',
                ),
            )
            self.assertIn("unsafe ZIP member path", ct.verify_zip_file(alias)[1])

    def test_final_staged_scan_blocks_generated_diff_secret(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            staged = Path(raw)
            (staged / "TASK_PACKET.json").write_text('{"id":"TP-STAGE-001"}\n')
            (staged / "WORKTREE_DIFF.patch").write_text("+token = " + "D" * 24 + "\n")
            with self.assertRaisesRegex(ct.PackageBlocked, "SECRET_ASSIGNMENT"):
                ct.scan_staged_tree(staged)

    def test_proof_pack_end_to_end_verifies_and_blocks_generated_diff_secret(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, packet = self._packaging_repo(root)
            large = root / "large-clean.bin"
            large.write_bytes(b"x" * 20_000_001)
            with mock.patch.object(ct, "repo_root", return_value=repo):
                self.assertEqual(
                    0,
                    ct.package(
                        "PROOF",
                        self._pack_args("TP-PACK-001", packet, include=[str(large)]),
                    ),
                )
            archives = list((root / "output").glob("*.zip"))
            self.assertEqual(1, len(archives))
            self.assertEqual(0, ct.verify_zip_file(archives[0])[0])

            archives[0].unlink()
            (repo / "payload.txt").write_text("token = " + "E" * 24 + "\n")
            with mock.patch.object(ct, "repo_root", return_value=repo):
                self.assertEqual(3, ct.package("PROOF", self._pack_args("TP-PACK-001", packet)))
            self.assertEqual([], list((root / "output").glob("*.zip")))

    def test_packaging_wires_repository_and_packet_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, packet = self._packaging_repo(root)
            payload = json.loads(packet.read_text())
            payload["repo_binding"]["project_id"] = "foreign"
            packet.write_text(json.dumps(payload))
            with mock.patch.object(ct, "repo_root", return_value=repo):
                self.assertEqual(3, ct.package("PROOF", self._pack_args("TP-PACK-001", packet)))
            self.assertEqual([], list((root / "output").glob("*.zip")))

    def test_return_pack_end_to_end_validates_metadata_before_zip(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, packet = self._packaging_repo(root, "TP-RETURN-001")
            args = self._pack_args(
                "TP-RETURN-001", packet, reason="architecture conflict", decision_needed="choose A or B"
            )
            with mock.patch.object(ct, "repo_root", return_value=repo):
                self.assertEqual(0, ct.package("RETURN", args))
            archive = next((root / "output").glob("*.zip"))
            self.assertEqual(0, ct.verify_zip_file(archive)[0])
            with zipfile.ZipFile(archive) as source:
                metadata_name = next(name for name in source.namelist() if name.endswith("/RETURN_METADATA.json"))
                metadata = json.loads(source.read(metadata_name))
            self.assertEqual([], ct.validate_return_metadata(metadata, repo))

    def test_packaging_revalidates_staged_packet_and_canonical_proof(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, packet = self._packaging_repo(root)
            real_copy = ct._copy_regular

            def tamper_staged_packet(source: Path, destination: Path) -> None:
                real_copy(source, destination)
                if Path(destination).name == "TASK_PACKET.json":
                    payload = json.loads(Path(destination).read_text())
                    payload["repo_binding"]["project_id"] = "foreign"
                    Path(destination).write_text(json.dumps(payload))

            with mock.patch.object(ct, "repo_root", return_value=repo), mock.patch.object(
                ct, "_copy_regular", side_effect=tamper_staged_packet
            ):
                self.assertEqual(3, ct.package("PROOF", self._pack_args("TP-PACK-001", packet)))
            self.assertEqual([], list((root / "output").glob("*.zip")))

            proof = root / "proof"
            proof.mkdir()
            (proof / "PROOF.json").write_text('{"packet_id":"TP-OTHER-001"}\n')
            with mock.patch.object(ct, "repo_root", return_value=repo):
                self.assertEqual(
                    3,
                    ct.package(
                        "PROOF",
                        self._pack_args("TP-PACK-001", packet, proof_dir=str(proof)),
                    ),
                )
            self.assertEqual([], list((root / "output").glob("*.zip")))

    def test_publication_copy_failure_leaves_no_named_or_temporary_archive(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, packet = self._packaging_repo(root)

            def fail_copy(source, destination, length) -> None:
                destination.write(b"partial")
                raise OSError("disk failure")

            with mock.patch.object(ct, "repo_root", return_value=repo), mock.patch.object(
                ct.shutil, "copyfileobj", side_effect=fail_copy
            ):
                self.assertEqual(3, ct.package("PROOF", self._pack_args("TP-PACK-001", packet)))
            self.assertEqual([], list((root / "output").iterdir()))

    def test_cli_names_crc_only_and_requires_return_reason_and_decision(self) -> None:
        missing = subprocess.run(
            [str(CT_PATH), "return-pack", "--packet-id", "TP-X-001", "--packet", "x.json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, missing.returncode)
        self.assertIn("--reason", missing.stderr)
        self.assertIn("--decision-needed", missing.stderr)

        with tempfile.TemporaryDirectory() as raw:
            archive = Path(raw) / "crc.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("root/payload.txt", b"safe")
            result = subprocess.run(
                [str(CT_PATH), "verify-zip", "--zip", str(archive), "--crc-only"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode)
            self.assertIn("CRC-only; manifests not verified", result.stdout)


class MacroPacketTests(unittest.TestCase):
    def binding(self):
        return json.loads((REPO / ".control-tower/templates/EXECUTION_BINDING.template.json").read_text())

    def macro(self, count=2):
        value = json.loads((REPO / ".control-tower/templates/SUPERVISOR_MACRO_PACKET.template.json").read_text())
        child = value["workstreams"][0]
        value["workstreams"] = []
        value["parallelism"]["max_mutating_workstreams"] = count
        for index in range(count):
            current = deepcopy(child)
            key = f"W{index + 1:02}"
            current.update(workstream_id=key, write_surface=[f"src/{key}/**"],
                           canonical_writers=[key], semantic_scope=[key])
            current["task_packet_ref"] = {"path": f"{key}.md", "sha256": str(index + 1) * 64}
            current["execution_route"]["preferred"] = {"runner": "shell", "model": "NONE", "effort": "low"}
            value["workstreams"].append(current)
        return value

    def snapshots(self, macro):
        result = {}
        for child in macro["workstreams"]:
            canonical = {key: deepcopy(child[key]) for key in (
                "allowed_actions", "forbidden_actions", "write_surface", "canonical_writers",
                "semantic_scope", "delivery_risk_lane", "rollback_boundary", "mutating", "execution_route")}
            canonical.update(task_packet_sha256=child["task_packet_ref"]["sha256"], audit_required=child["audit"]["required"])
            result[child["workstream_id"]] = {
                "canonical_authority": canonical, "verified_upstream": True,
                "operator": {"source_ref": "operator/child", "allowed_actions": list(child["allowed_actions"])},
                "repository": {"source_ref": "repository/governance", "allowed_actions": list(child["allowed_actions"])},
                "workflow": {"status": "LEGAL", "blockers": [], "source_ref": "workflow/current",
                             "allowed_actions": list(child["allowed_actions"])},
                "policy": {"required": False, "status": "NOT_APPLICABLE"},
                "status": "NOT_RUN", "write_scope_verified": True, "custody_verified": True,
            }
        return result

    def test_binding_schema_and_independent_risk_taxonomies(self):
        binding = self.binding()
        self.assertEqual([], ct.validate_binding_obj(binding, REPO))
        for key, value in [("dcp_risk_class", "L2"), ("dcp_risk_class", "R2_MEDIUM")]:
            mutant = deepcopy(binding)
            mutant["policy_refs"][key] = value
            self.assertTrue(ct.validate_binding_obj(mutant, REPO))
        mutant = deepcopy(binding)
        mutant["authority"] = "EXECUTE"
        self.assertTrue(ct.validate_binding_obj(mutant, REPO))

    def test_binding_has_exactly_one_packet_or_macro_subject(self):
        binding = self.binding()
        binding["macro_id"] = "SMP-TEST-001"
        self.assertTrue(ct.validate_binding_obj(binding, REPO))
        del binding["packet_id"]
        self.assertEqual([], ct.validate_binding_obj(binding, REPO))
        del binding["macro_id"]
        self.assertTrue(ct.validate_binding_obj(binding, REPO))
        self.assertTrue(ct.schema_errors({}, {"oneOf": [{"required": ["a"]}, {"unknownKeyword": True}]}))

    def test_upstream_l3_audit_cannot_be_weakened_by_l1_or_stage(self):
        binding = self.binding()
        binding["delivery"]["risk_lane"] = "L1"
        binding["stage"] = "investigation"
        binding["audit"]["upstream_obligations"] = [{"source_ref": "upstream/L3", "required": True}]
        binding["audit"]["effective_required"] = False
        self.assertTrue(ct.validate_binding_obj(binding, REPO))
        binding["audit"]["effective_required"] = True
        self.assertTrue(ct.validate_binding_obj(binding, REPO))
        binding["audit"]["effective_requirement_sources"].append("upstream/L3")
        self.assertEqual([], ct.validate_binding_obj(binding, REPO))

    def test_binding_rejects_operator_authority_and_incomplete_fallback(self):
        for action in ("merge", "activate", "mark_ready", "force_push"):
            binding = self.binding()
            binding["constraints"]["allowed_actions"] = [action]
            self.assertTrue(ct.validate_binding_obj(binding, REPO))
        binding = self.binding()
        binding["fallback"]["allowed"] = True
        self.assertTrue(ct.validate_binding_obj(binding, REPO))
        binding["fallback"] = {"allowed": True, "trigger": "runner unavailable",
                               "binding": {"runner": "shell", "model": "NONE", "effort": "low"}}
        self.assertEqual([], ct.validate_binding_obj(binding, REPO))

    def test_legacy_route_preserved_and_new_package_member_canonical(self):
        old = valid_route()
        before = deepcopy(old)
        converted = ct.legacy_execution_binding(old)
        self.assertEqual([], ct.validate_binding_obj(converted, REPO))
        self.assertEqual(before, old)
        self.assertEqual(old, converted["compatibility"]["legacy_record"])
        self.assertEqual("NOT_RUN", converted["policy_refs"]["dcp_risk_class"])
        with tempfile.TemporaryDirectory() as raw:
            fixture = ControlTowerTests()
            repo, packet = fixture._packaging_repo(Path(raw))
            with mock.patch.object(ct, "repo_root", return_value=repo):
                self.assertEqual(0, ct.package("PROOF", fixture._pack_args("TP-PACK-001", packet)))
            archive = next((Path(raw) / "output").glob("*.zip"))
            with zipfile.ZipFile(archive) as source:
                names = source.namelist()
            self.assertTrue(any(name.endswith("/EXECUTION_BINDING.json") for name in names))
            self.assertFalse(any(name.endswith("/ROUTING_DECISION.json") for name in names))

    def test_schema_positive_and_strict_negative_fixtures(self):
        macro = self.macro()
        self.assertEqual([], ct.validate_macro_obj(macro, REPO))
        for key in ("may_merge", "may_activate", "may_create_canonical_packets"):
            mutant = deepcopy(macro)
            mutant["team_lead"][key] = True
            self.assertTrue(ct.validate_macro_obj(mutant, REPO))
        mutant = deepcopy(macro)
        mutant["auto_dispatch"] = True
        self.assertTrue(ct.validate_macro_obj(mutant, REPO))
        mutant = deepcopy(macro)
        mutant["parallelism"]["max_mutating_workstreams"] = True
        self.assertTrue(ct.validate_macro_obj(mutant, REPO))

    def test_legacy_fallback_needs_explicit_effort_rebinding(self):
        old = valid_route()
        old["fallback"] = {"runner": "alternate", "model": "exact", "trigger": "unavailable"}
        self.assertEqual([], ct.validate_route_obj(old, REPO))
        converted = ct.legacy_execution_binding(old)
        self.assertEqual(old, converted["compatibility"]["legacy_record"])
        self.assertTrue(ct.validate_binding_obj(converted, REPO))
        converted["fallback"]["binding"]["effort"] = "low"
        self.assertEqual([], ct.validate_binding_obj(converted, REPO))

    def test_immutable_packet_and_coordinator_refs_block_drift_and_symlinks(self):
        macro = self.macro()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            refs = [macro["team_lead"]["execution_binding_ref"]] + [c["task_packet_ref"] for c in macro["workstreams"]]
            for ref in refs:
                path = root / ref["path"]
                path.write_text("immutable authority\n")
                ref["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            coordinator = self.binding()
            del coordinator["packet_id"]
            coordinator["macro_id"] = macro["macro_id"]
            coordinator_path = root / refs[0]["path"]
            coordinator_path.write_text(json.dumps(coordinator))
            refs[0]["sha256"] = hashlib.sha256(coordinator_path.read_bytes()).hexdigest()
            self.assertEqual([], ct.validate_macro_obj(macro, REPO, root))
            original_bytes = coordinator_path.read_bytes()
            original_scan = ct.scan_regular_file
            scans = []
            def drift_after_scan(path):
                result = original_scan(path)
                if path == coordinator_path:
                    scans.append(path)
                    if len(scans) == 2:
                        changed = deepcopy(coordinator)
                        changed["selection"]["runner"] = "unbound-runner"
                        coordinator_path.write_text(json.dumps(changed))
                return result
            with mock.patch.object(ct, "scan_regular_file", side_effect=drift_after_scan):
                self.assertTrue(ct.validate_macro_obj(macro, REPO, root))
            coordinator_path.write_bytes(original_bytes)
            (root / "W01.md").write_text("changed\n")
            self.assertTrue(ct.validate_macro_obj(macro, REPO, root))
            (root / "W01.md").unlink()
            (root / "W01.md").symlink_to(root / "W02.md")
            self.assertTrue(ct.validate_macro_obj(macro, REPO, root))
            macro["workstreams"][0]["task_packet_ref"]["path"] = "../W01.md"
            self.assertTrue(ct.validate_macro_obj(macro, REPO, root))

    def test_dag_cycle_unknown_dependency_and_unknown_join_block(self):
        for mode in ("cycle", "unknown", "join", "duplicate"):
            macro = self.macro()
            if mode == "cycle":
                macro["workstreams"][0]["dependencies"] = ["W02"]
                macro["workstreams"][1]["dependencies"] = ["W01"]
            elif mode == "unknown": macro["workstreams"][0]["dependencies"] = ["MISSING"]
            elif mode == "join": macro["joins"] = [{"join_id": "J01", "requires": ["MISSING"], "condition": "all"}]
            else: macro["workstreams"][1]["workstream_id"] = "W01"
            self.assertTrue(ct.validate_macro_obj(macro, REPO), mode)

    def test_disjoint_l1_siblings_and_readonly_companion_preview_concurrently(self):
        macro = self.macro()
        snapshot = self.snapshots(macro)
        result = ct.preview_macro(macro, snapshot, REPO)
        self.assertEqual([["W01", "W02"]], result["candidate_batches"])
        self.assertEqual("NONE", result["authority"])
        self.assertEqual("PREVIEW_ONLY", result["status"])
        macro["workstreams"][1].update(mutating=False, write_surface=[])
        result = ct.preview_macro(macro, self.snapshots(macro), REPO)
        self.assertEqual([["W01", "W02"]], result["candidate_batches"])

    def test_preview_is_inert_deterministic_and_requires_custody(self):
        macro = self.macro()
        snapshots = self.snapshots(macro)
        before = deepcopy((macro, snapshots))
        with mock.patch.object(ct, "run", side_effect=AssertionError("must not dispatch")):
            first = ct.preview_macro(macro, snapshots, REPO)
            second = ct.preview_macro(macro, snapshots, REPO)
        self.assertEqual(first, second)
        self.assertEqual(before, (macro, snapshots))
        self.assertEqual("NONE", first["dcp_summary"]["authority"])
        snapshots["W01"]["custody_verified"] = False
        self.assertEqual([["W02"]], ct.preview_macro(macro, snapshots, REPO)["candidate_batches"])

    def test_overlap_shared_writer_and_semantic_collisions_require_explicit_serialization(self):
        for key, value in [("write_surface", ["SRC/W01/child.py"]), ("canonical_writers", ["W01"]), ("semantic_scope", ["W01"])]:
            macro = self.macro()
            macro["workstreams"][1][key] = value
            self.assertTrue(ct.validate_macro_obj(macro, REPO), key)
            macro["workstreams"][1]["dependencies"] = ["W01"]
            self.assertEqual([], ct.validate_macro_obj(macro, REPO), key)
        macro = self.macro()
        macro["workstreams"][1]["write_surface"] = ["src/*/child.py"]
        self.assertTrue(ct.validate_macro_obj(macro, REPO))

    def test_child_authority_cannot_transfer_or_widen_or_hide_writers(self):
        macro = self.macro()
        snapshots = self.snapshots(macro)
        mutations = [("allowed_actions", ["read", "edit", "validate", "publish"]),
                     ("write_surface", ["src/W02/**"]), ("delivery_risk_lane", "L0"),
                     ("canonical_writers", ["W02"]), ("semantic_scope", ["W02"]),
                     ("rollback_boundary", "shared rollback")]
        for key, value in mutations:
            mutant = deepcopy(macro)
            mutant["authority"]["global_allowed_actions"].append("publish")
            mutant["workstreams"][0][key] = value
            result = ct.preview_macro(mutant, snapshots, REPO)
            self.assertFalse(result["children"].get("W01", {}).get("candidate", False), key)
        snapshots["W01"]["canonical_authority"]["audit_required"] = True
        result = ct.preview_macro(macro, snapshots, REPO)
        self.assertIn("CHILD_AUDIT_WAIVED", result["children"]["W01"]["blockers"])

    def test_policy_workflow_operator_and_repository_denials_remain_local(self):
        macro = self.macro()
        for mode in ("DCP_UNKNOWN", "DCP_BLOCKED", "workflow", "operator", "repository", "unverified", "physical"):
            snapshots = self.snapshots(macro)
            mutant = deepcopy(macro)
            first = snapshots["W01"]
            if mode.startswith("DCP_"):
                mutant["workstreams"][0]["dcp_status"] = mode[4:]
                first["policy"] = {"required": True, "status": mode[4:]}
            elif mode == "workflow": first["workflow"]["blockers"] = ["waiting"]
            elif mode in ("operator", "repository"): first[mode]["allowed_actions"] = []
            elif mode == "unverified": first["verified_upstream"] = False
            else: first["write_scope_verified"] = False
            result = ct.preview_macro(mutant, snapshots, REPO)
            self.assertFalse(result["children"]["W01"]["candidate"], mode)
            self.assertEqual([["W02"]], result["candidate_batches"], mode)

    def test_l3_gate_and_upstream_audit_hold_only_affected_child(self):
        macro = self.macro(3)
        macro["workstreams"][0]["delivery_risk_lane"] = "L3"
        macro["workstreams"][0]["audit"]["required"] = True
        snapshots = self.snapshots(macro)
        snapshots["W02"]["policy"]["audit_required"] = True
        result = ct.preview_macro(macro, snapshots, REPO)
        self.assertEqual([["W03"]], result["candidate_batches"])
        self.assertEqual(["W01"], result["operator_gates_needed"])
        self.assertIn("UPSTREAM_AUDIT_REQUIRED", result["children"]["W02"]["blockers"])

    def test_independent_failure_does_not_stop_sibling_but_global_stop_does(self):
        macro = self.macro()
        macro["authority"]["global_stop_conditions"] = ["credential exposure"]
        snapshots = self.snapshots(macro)
        snapshots["W01"]["status"] = "FAIL"
        self.assertEqual([["W02"]], ct.preview_macro(macro, snapshots, REPO)["candidate_batches"])
        snapshots["W01"]["global_stop_triggered"] = True
        self.assertEqual([], ct.preview_macro(macro, snapshots, REPO)["candidate_batches"])

    def test_l3_operator_gate_requires_literal_true(self):
        macro = self.macro()
        macro["workstreams"][0]["delivery_risk_lane"] = "L3"
        macro["workstreams"][0]["audit"]["required"] = True
        for gate in (None, False, "false", "true", 1, [], {}):
            snapshots = self.snapshots(macro)
            snapshots["W01"]["operator_gate_verified"] = gate
            result = ct.preview_macro(macro, snapshots, REPO)
            self.assertEqual([["W02"]], result["candidate_batches"], repr(gate))
        snapshots["W01"]["operator_gate_verified"] = True
        self.assertEqual([["W01", "W02"]], ct.preview_macro(macro, snapshots, REPO)["candidate_batches"])

    def test_dependency_completion_requires_bound_verified_source(self):
        macro = self.macro()
        macro["workstreams"][1]["dependencies"] = ["W01"]
        snapshots = self.snapshots(macro)
        snapshots["W01"].update(status="PASS", completion_verified=True)
        self.assertEqual([], ct.preview_macro(macro, snapshots, REPO)["candidate_batches"])
        snapshots["W01"]["completion_source_ref"] = "workflow/accepted-receipt"
        self.assertEqual([["W02"]], ct.preview_macro(macro, snapshots, REPO)["candidate_batches"])
        snapshots["W01"]["canonical_authority"]["task_packet_sha256"] = "f" * 64
        self.assertEqual([], ct.preview_macro(macro, snapshots, REPO)["candidate_batches"])

    def test_fallback_must_be_exact_pre_authorized_tuple(self):
        macro = self.macro()
        fallback = {"runner": "alternate", "model": "exact", "effort": "low"}
        macro["workstreams"][0]["execution_route"]["allowed_fallbacks"] = [fallback]
        snapshots = self.snapshots(macro)
        snapshots["W01"].update(route_failed=True, selected_fallback=fallback)
        self.assertTrue(ct.preview_macro(macro, snapshots, REPO)["children"]["W01"]["candidate"])
        snapshots["W01"]["selected_fallback"] = dict(fallback, model="different")
        self.assertIn("ROUTE_CEILING_EXCEEDED", ct.preview_macro(macro, snapshots, REPO)["children"]["W01"]["blockers"])

    def test_aggregate_preserves_mixed_status_and_never_mints_finality(self):
        macro = self.macro()
        reports = {child["workstream_id"]: {"status": status, "task_packet_sha256": child["task_packet_ref"]["sha256"],
                    "execution_subject": "a" * 40, "operator_gates_needed": ["audit"], "supervisor_decisions_needed": ["repair"]}
                   for child, status in zip(macro["workstreams"], ["PASS", "FAIL"])}
        result = ct.macro_return(macro, reports)
        self.assertEqual("RETURNED_FOR_SUPERVISOR", result["status"])
        self.assertEqual("NONE", result["authority"])
        self.assertEqual("FAIL", result["children"]["W02"]["status"])
        self.assertEqual(["audit"], result["operator_gates_needed"])
        reports["W01"]["proof"] = {"subject": "b" * 40, "task_packet_sha256": reports["W01"]["task_packet_sha256"]}
        self.assertEqual("BLOCKED", ct.macro_return(macro, reports)["status"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
