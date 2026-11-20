"""Failed local admission cannot poison a portfolio journal."""

import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from dopemux.supervisor.runtime import Runtime
from .fixtures import manifest


class AtomicAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.rt = Runtime(self.root / "state", self.root / "returns", "fixture-receiver")
        self.addCleanup(self.rt.close)

    def test_route_labels_are_qualified_to_mandate_and_deadline(self):
        first = manifest(self.project)
        self.rt.admit(first, authorization_ref="fixture-issued")
        other = self.root / "other"
        other.mkdir()
        second = manifest(other, "m2", "p2", first["expires_at"] + 1)
        self.rt.admit(second, authorization_ref="fixture-issued")
        asyncio.run(self.rt.run())
        self.assertTrue((other / "result.txt").exists())
        self.assertTrue((self.project / "result.txt").exists())

    def test_failed_admission_rolls_back_every_stage_and_outbox(self):
        for stage in ["mandate", "grant", "route", "work:implement", "complete"]:
            with self.subTest(stage=stage):

                def fail(name):
                    if name == stage:
                        raise RuntimeError("injected admission interruption")

                self.rt.admission_fault_hook = fail
                with self.assertRaises(RuntimeError):
                    self.rt.admit(manifest(self.project), authorization_ref="fixture-issued")
                self.assertEqual(self.rt._plans(), {})
                self.assertEqual(self.rt.kernel._state()["grants"], {})
                self.assertEqual(self.rt.kernel._state()["works"], {})
                self.assertEqual(self.rt.kernel.pending_returns(), [])
        self.rt.admission_fault_hook = None
        self.rt.admit(manifest(self.project), authorization_ref="fixture-issued")
        asyncio.run(self.rt.run())
        self.assertTrue((self.project / "result.txt").exists())

    def test_historical_incomplete_plan_holds_only_its_project(self):
        plan = manifest(self.project)
        self.rt.kernel.db.execute(
            "INSERT INTO mandates VALUES(?,?,?)", ("m1", json.dumps(plan), "{}")
        )
        other = self.root / "other"
        other.mkdir()
        self.rt.admit(manifest(other, "m2", "p2"), authorization_ref="fixture-issued")
        asyncio.run(self.rt.run())
        self.assertEqual(self.rt.status()["mandates"]["m1"]["status"], "HELD")
        self.assertTrue((other / "result.txt").exists())

    def test_malformed_manifest_never_partially_admits(self):
        for field, value in [("project_root", None), ("success_steps", [{}])]:
            bad = manifest(self.project)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.rt.admit(bad, authorization_ref="fixture-issued")
            self.assertEqual(self.rt._plans(), {})
        for field, value in [("kind", {}), ("effects", [{}]), ("when_failed", [])]:
            bad = manifest(self.project)
            bad["steps"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.rt.admit(bad, authorization_ref="fixture-issued")
            self.assertEqual(self.rt._plans(), {})
