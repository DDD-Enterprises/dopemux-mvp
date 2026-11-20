"""Current local owner narrowing reaches an active fixture coordinator."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from dopemux.supervisor.runtime import Runtime
from .fixtures import manifest


class LiveOwnerControlTests(unittest.TestCase):
    def test_cli_denial_reaches_running_mandate_without_coordinator_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            project = root / "project"
            project.mkdir()
            state, returns = root / "state", root / "returns"
            rt = Runtime(state, returns, "fixture-local")
            plan = manifest(
                project,
                code=(
                    "import time;from pathlib import Path;time.sleep(4);"
                    "Path('result.txt').write_text('done')"
                ),
            )
            rt.admit(plan, authorization_ref="fixture-issued")
            rt.close()
            env = {
                "PATH": "/usr/bin:/bin",
                "HOME": str(root),
                "TMPDIR": str(root),
                "PYTHONPATH": str(Path(__file__).resolve().parents[3] / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHON_DOTENV_DISABLED": "1",
            }
            command = [
                sys.executable,
                "-B",
                "-m",
                "dopemux.supervisor",
                "--state-root",
                str(state),
                "--return-root",
                str(returns),
                "--receiver-ref",
                "fixture-local",
            ]
            process = subprocess.Popen(
                [*command, "run"],
                env=env,
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            native = None
            try:
                until = time.monotonic() + 3
                while time.monotonic() < until:
                    starts = list((state / "evidence").glob("*/START_ACK.json"))
                    if starts:
                        native = json.loads(starts[0].read_text())
                        break
                    time.sleep(0.01)
                self.assertIsNotNone(native)
                denial = subprocess.run(
                    [
                        *command,
                        "control",
                        "m1",
                        "--sequence",
                        "1",
                        "--receipt-ref",
                        "fixture-denial",
                        "--action",
                        "deny",
                        "--gate",
                        "security",
                    ],
                    env=env,
                    cwd=root,
                    capture_output=True,
                    timeout=5,
                )
                self.assertEqual(denial.returncode, 0, denial.stderr)
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 3, stderr)
                self.assertFalse((project / "result.txt").exists())
                work = json.loads(stdout)["works"]["m1:implement"]
                self.assertEqual(work["status"], "EFFECT_UNKNOWN")
                self.assertTrue(work["evidence_refs"])
                settled = Runtime(state, returns, "fixture-local")
                try:
                    control = settled.kernel._state()["grants"]["m1"]["owner_control"]
                    self.assertEqual(control["principal_uid"], os.getuid())
                    self.assertEqual(control["sequence"], 1)
                    self.assertEqual(control["gate"], "security")
                finally:
                    settled.close()
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate(timeout=2)
                if native:
                    try:
                        os.killpg(native["pgid"], signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_ordered_controls_are_idempotent_and_cannot_release_or_widen(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            project = root / "project"
            project.mkdir()
            rt = Runtime(root / "state", root / "returns", "fixture-local")
            try:
                rt.admit(manifest(project), authorization_ref="fixture-issued")
                args = dict(sequence=2, receipt_ref="denial", action="deny", gate="security")
                rt.kernel.control_mandate("m1", **args)
                first = rt.kernel._state()
                rt.kernel.control_mandate("m1", **args)
                self.assertEqual(first, rt.kernel._state())
                for changes in [
                    dict(sequence=1, receipt_ref="stale"),
                    dict(sequence=2, receipt_ref="conflict"),
                    dict(action="allow"),
                    dict(gate="invented"),
                ]:
                    with self.subTest(changes=changes), self.assertRaises(ValueError):
                        rt.kernel.control_mandate("m1", **(args | changes))
                rt.kernel.control_mandate("m1", sequence=3, receipt_ref="revoke", action="revoke")
                self.assertTrue(rt.kernel._state()["grants"]["m1"]["revoked"])
                self.assertEqual(rt.kernel.claim_ready(), [])
            finally:
                rt.close()

    def test_mandate_denial_does_not_block_disjoint_project(self):
        import asyncio

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            one, two = root / "one", root / "two"
            one.mkdir()
            two.mkdir()
            rt = Runtime(root / "state", root / "returns", "fixture-local")
            try:
                rt.admit(manifest(one), authorization_ref="fixture-issued")
                rt.admit(manifest(two, "m2", "p2"), authorization_ref="fixture-issued")
                rt.kernel.control_mandate(
                    "m1", sequence=1, receipt_ref="stop-one", action="deny", gate="workflow"
                )
                asyncio.run(rt.run())
                self.assertEqual(rt.status()["mandates"]["m1"]["status"], "HELD")
                self.assertFalse((one / "result.txt").exists())
                self.assertTrue((two / "result.txt").exists())
            finally:
                rt.close()
