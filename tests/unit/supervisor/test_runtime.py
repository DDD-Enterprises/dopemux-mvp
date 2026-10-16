"""Runnable integration tests: real Python subprocesses, private projects and local returns."""

import asyncio
import importlib
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
import hashlib
import os
import subprocess
from dataclasses import replace
from unittest.mock import patch


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        try:
            self.api = importlib.import_module("dopemux.supervisor.runtime")
            self.transport = importlib.import_module("dopemux.supervisor.transport")
        except ModuleNotFoundError:
            self.fail("Permanent dispatch/return integration is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.deadline = time.time() + 60
        self.rt = self.api.Runtime(
            self.root / "state", self.root / "returns", "master:test"
        )
        self.addCleanup(self.rt.close)

    def step(self, name, code, **extra):
        value = dict(
            step_id=name,
            kind="implementation",
            argv=[sys.executable, "-B", "-c", code],
            effects=["read", "write"],
            write_paths=["capability.py"],
            depends_on=[],
            timeout_seconds=3,
            heavy=False,
        )
        value.update(extra)
        return value

    def manifest(self, **extra):
        data = dict(
            schema_version="dopemux.project_mandate.v1",
            mandate_id="m1",
            issuer_ref="master:test",
            project_id="p1",
            project_root=str(self.project),
            expires_at=self.deadline,
            active_seconds=15,
            spend_limit_micros=0,
            max_parallel=2,
            repair_limit=1,
            stop_conditions=["material-scope", "spend", "security", "public-release"],
            gates={"security": "PASS", "workflow": "PASS", "spending": "PASS"},
            route=dict(
                binding_id="local-python",
                kind="local_command",
                model_class="deterministic",
                executable=sys.executable,
                valid_until=self.deadline,
            ),
            steps=[
                self.step(
                    "implement",
                    "from pathlib import Path;"
                    "Path('capability.py').write_text('def answer(): return 42\\n')",
                ),
                self.step(
                    "test",
                    "from pathlib import Path;from capability import answer;"
                    "assert answer()==42;Path('checks.count').write_text('1')",
                    kind="test",
                    effects=["read", "write", "test"],
                    write_paths=["checks.count"],
                    depends_on=["implement"],
                ),
            ],
            success_steps=["test"],
        )
        data.update(extra)
        return data

    def admit(self, manifest=None):
        manifest = json.loads(json.dumps(manifest or self.manifest()))
        if len(manifest["steps"]) == 1:
            first = manifest["steps"][0]["step_id"]
            manifest["steps"].append(
                self.step(
                    "verify",
                    "assert True",
                    kind="validation",
                    effects=["read"],
                    write_paths=[],
                    depends_on=[first],
                )
            )
            manifest["success_steps"] = ["verify"]
        self.rt.admit(manifest, authorization_ref="master:test")

    def test_real_implementation_test_return_ack_restart_without_reexecution(self):
        self.admit()
        asyncio.run(self.rt.run())
        self.assertEqual((self.project / "checks.count").read_text(), "1")
        self.assertEqual(
            self.rt.status()["mandates"]["m1"]["status"],
            "COMPLETED_PENDING_NATIVE_ACCEPTANCE",
        )
        self.assertGreater(len(self.rt.kernel.pending_returns()), 0)
        receiver = self.transport.ReturnReceiver(self.root / "returns", "master:test")
        first = receiver.receive()
        self.assertGreater(first, 0)
        self.assertEqual(receiver.receive(), 0)
        asyncio.run(self.rt.deliver_returns())
        self.assertEqual(self.rt.kernel.pending_returns(), [])
        self.rt.close()
        self.rt = self.api.Runtime(
            self.root / "state", self.root / "returns", "master:test"
        )
        self.addCleanup(self.rt.close)
        self.admit()
        asyncio.run(self.rt.run())
        self.assertEqual((self.project / "checks.count").read_text(), "1")
        self.assertEqual(self.rt.kernel.metrics("p1")["accepted_capabilities"], 0)
        self.rt.kernel.accept(
            "m1:test", receipt_ref="native:review", capability="answer-42"
        )
        self.assertEqual(self.rt.kernel.metrics("p1")["accepted_capabilities"], 1)

    def test_ordinary_repair_and_retest_stay_in_same_mandate(self):
        m = self.manifest()
        m["steps"][0]["argv"][
            -1
        ] = "from pathlib import Path;Path('capability.py').write_text('def answer(): return 0\\n')"
        m["steps"] += [
            self.step(
                "repair",
                "from pathlib import Path;"
                "Path('capability.py').write_text('def answer(): return 42\\n')",
                kind="repair",
                when_failed="test",
            ),
            self.step(
                "retest",
                "from capability import answer;assert answer()==42",
                kind="test",
                effects=["read", "test"],
                write_paths=[],
                depends_on=["repair"],
                when_failed="test",
            ),
        ]
        m["success_steps"] = ["test", "retest"]
        self.admit(m)
        asyncio.run(self.rt.run())
        states = self.rt.status()["works"]
        self.assertEqual(states["m1:test"]["status"], "FAILED")
        self.assertEqual(states["m1:repair"]["status"], "SUCCEEDED")
        self.assertEqual(states["m1:retest"]["status"], "SUCCEEDED")
        self.assertEqual(self.rt.status()["mandates"]["m1"]["repairs_used"], 1)

    def test_timeout_holds_effects_but_independent_project_completes(self):
        m = self.manifest()
        m["steps"] = [
            self.step("wait", "import time;time.sleep(2)", timeout_seconds=0.1)
        ]
        m["success_steps"] = ["wait"]
        self.admit(m)
        other = self.root / "other"
        other.mkdir()
        self.admit(
            self.manifest(mandate_id="m2", project_id="p2", project_root=str(other))
        )
        asyncio.run(self.rt.run())
        self.assertEqual(
            self.rt.status()["works"]["m1:wait"]["status"], "EFFECT_UNKNOWN"
        )
        self.assertTrue((other / "checks.count").is_file())
        record = self.rt.status()["works"]["m1:wait"]["evidence_refs"]
        native = json.loads(Path(record[-1]).read_text())
        self.assertTrue(native["owned_group_absent"])
        self.assertEqual(native["stop_reason"], "TIMEOUT")

    def test_pending_intent_recovery_holds_without_relaunch(self):
        self.admit()
        self.rt.kernel.claim_ready()
        self.rt.close()
        self.rt = self.api.Runtime(
            self.root / "state", self.root / "returns", "master:test"
        )
        self.addCleanup(self.rt.close)
        asyncio.run(self.rt.run())
        self.assertFalse((self.project / "capability.py").exists())
        self.assertEqual(
            self.rt.status()["works"]["m1:implement"]["status"], "EFFECT_UNKNOWN"
        )

    def test_admission_rejects_unknown_fields_paths_denials_and_route_bypass(self):
        for mutate in [
            lambda m: m.update(unexpected=True),
            lambda m: m["steps"][0].update(write_paths=["../outside"]),
            lambda m: m["gates"].update(security="UNKNOWN"),
            lambda m: m["route"].update(kind="provider_api"),
            lambda m: m["steps"][0].update(
                argv=["claude", "--dangerously-skip-permissions"]
            ),
        ]:
            with self.subTest(mutate=mutate):
                m = self.manifest()
                mutate(m)
                with self.assertRaises(ValueError):
                    self.admit(m)
        with self.assertRaises(ValueError):
            self.rt.admit(self.manifest(), authorization_ref="different")

    def test_same_physical_root_cannot_be_enrolled_as_another_project(self):
        self.admit()
        with self.assertRaises(ValueError):
            self.admit(self.manifest(mandate_id="m2", project_id="p2"))

    def test_environment_is_replacement_and_logs_have_actual_exit(self):
        m = self.manifest()
        m["steps"] = [
            self.step(
                "check",
                "import os;assert 'OPENAI_API_KEY' not in os.environ;print('bounded-output')",
                effects=["read"],
                write_paths=[],
            )
        ]
        m["success_steps"] = ["check"]
        self.admit(m)
        asyncio.run(self.rt.run())
        refs = self.rt.status()["works"]["m1:check"]["evidence_refs"]
        native = json.loads(Path(refs[-1]).read_text())
        self.assertEqual(native["native_exit"], 0)
        self.assertEqual(Path(refs[0]).read_text().strip(), "bounded-output")
        self.assertTrue(native["capture_complete"])

    def test_out_of_scope_write_is_detected_and_not_reported_success(self):
        m = self.manifest()
        m["steps"] = [
            self.step(
                "escape",
                "from pathlib import Path;Path('unlisted.txt').write_text('bad')",
            )
        ]
        m["success_steps"] = ["escape"]
        self.admit(m)
        asyncio.run(self.rt.run())
        self.assertEqual(
            self.rt.status()["works"]["m1:escape"]["status"], "EFFECT_UNKNOWN"
        )
        native = json.loads(
            Path(
                self.rt.status()["works"]["m1:escape"]["evidence_refs"][-1]
            ).read_text()
        )
        self.assertEqual(native["stop_reason"], "WRITE_SCOPE_DRIFT")

    def test_return_digest_conflict_never_acknowledges(self):
        self.admit()
        asyncio.run(self.rt.run())
        path = next((self.root / "returns" / "events").glob("*.json"))
        event = json.loads(path.read_text())
        event["payload"]["status"] = "FORGED"
        path.write_text(json.dumps(event))
        receiver = self.transport.ReturnReceiver(self.root / "returns", "master:test")
        with self.assertRaises(ValueError):
            receiver.receive()
        self.assertGreater(len(self.rt.kernel.pending_returns()), 0)

    def test_changed_inputs_hold_before_any_subprocess(self):
        self.admit()
        (self.project / "external-input.txt").write_text("changed after admission")
        asyncio.run(self.rt.run())
        self.assertFalse((self.project / "capability.py").exists())
        self.assertEqual(self.rt.status()["mandates"]["m1"]["status"], "HELD")

    def test_completed_output_drift_is_not_represented_as_reusable_success(self):
        self.admit()
        asyncio.run(self.rt.run())
        (self.project / "capability.py").write_text("tampered")
        asyncio.run(self.rt.run())
        self.assertEqual(self.rt.status()["mandates"]["m1"]["status"], "HELD")
        self.assertEqual((self.project / "checks.count").read_text(), "1")

    def test_multiple_return_batches_make_progress_past_100(self):
        import hashlib
        from dopemux.supervisor.mandates import canonical

        root = self.root / "large-returns"
        publisher = self.transport.ReturnPublisher(root, "master:test")

        async def publish():
            for n in range(120):
                payload = {"key": str(n), "kind": "test"}
                await publisher(
                    {
                        "key": str(n),
                        "payload": payload,
                        "digest": hashlib.sha256(canonical(payload)).hexdigest(),
                    }
                )

        asyncio.run(publish())
        receiver = self.transport.ReturnReceiver(root, "master:test")
        self.assertEqual(receiver.receive(), 100)
        self.assertEqual(receiver.receive(), 20)
        self.assertEqual(receiver.receive(), 0)

    def test_cli_fresh_process_dispatch_ack_and_restart_no_reexecution(self):
        import subprocess

        manifest = self.root / "mandate.json"
        manifest.write_text(json.dumps(self.manifest()))
        command = [
            sys.executable,
            "-B",
            "-m",
            "dopemux.supervisor",
            "--state-root",
            str(self.root / "cli-state"),
            "--return-root",
            str(self.root / "cli-returns"),
            "--receiver-ref",
            "master:test",
        ]
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.root),
            "PYTHONPATH": str(Path(__file__).resolve().parents[3] / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHON_DOTENV_DISABLED": "1",
        }

        def run(*args):
            process = subprocess.run(
                [*command, *args],
                env=env,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            return json.loads(process.stdout)

        run("admit", str(manifest), "--authorization-ref", "master:test")
        first = run("run")
        self.assertEqual(
            first["mandates"]["m1"]["status"], "COMPLETED_PENDING_NATIVE_ACCEPTANCE"
        )
        run("receive")
        self.assertEqual(run("deliver")["pending_returns"], 0)
        again = run("run")
        self.assertEqual(
            again["works"]["m1:test"]["attempt_id"],
            first["works"]["m1:test"]["attempt_id"],
        )
        self.assertEqual((self.project / "checks.count").read_text(), "1")
        self.assertIsNone(again["works"]["m1:test"]["native_acceptance"])

    def test_coordinator_file_lock_excludes_second_runtime(self):
        other = self.api.Runtime(
            self.root / "state", self.root / "returns", "master:test"
        )
        try:
            with self.rt.coordinator():
                with self.assertRaises(ValueError):
                    with other.coordinator():
                        self.fail("Second coordinator admitted")
        finally:
            other.close()

    def test_shipped_template_schema_and_runtime_contract_agree(self):
        from dopemux.supervisor.mandates import FIELDS, STEP_FIELDS

        repo = Path(__file__).resolve().parents[3]
        schema = json.loads(
            (repo / "schemas/supervisor/project-mandate.v1.schema.json").read_text()
        )
        self.assertEqual(set(schema["required"]), FIELDS)
        self.assertEqual(
            set(schema["properties"]["steps"]["items"]["properties"]), STEP_FIELDS
        )
        plan = json.loads(
            (repo / "examples/supervisor/project-mandate.template.json").read_text()
        )
        with self.assertRaises(ValueError):
            self.admit(plan)
        plan.update(
            mandate_id="m1",
            issuer_ref="master:test",
            project_id="p1",
            project_root=str(self.project),
            expires_at=self.deadline,
        )
        plan["route"].update(
            binding_id="local-python",
            executable=sys.executable,
            valid_until=self.deadline,
        )
        for step in plan["steps"]:
            step["argv"][0] = sys.executable
        self.admit(plan)
        asyncio.run(self.rt.run())
        self.assertEqual(
            self.rt.status()["mandates"]["m1"]["status"],
            "COMPLETED_PENDING_NATIVE_ACCEPTANCE",
        )
        self.assertEqual(self.rt.status()["works"]["m1:repair"]["status"], "READY")

    def test_native_failure_preserves_stderr_and_actual_exit(self):
        m = self.manifest()
        m["steps"] = [
            self.step(
                "fail",
                "import sys;print('native diagnostic',file=sys.stderr);sys.exit(7)",
                effects=["read"],
                write_paths=[],
            )
        ]
        self.admit(m)
        asyncio.run(self.rt.run())
        work = self.rt.status()["works"]["m1:fail"]
        self.assertEqual(work["status"], "FAILED")
        self.assertEqual(
            Path(work["evidence_refs"][1]).read_text().strip(), "native diagnostic"
        )
        record = json.loads(Path(work["evidence_refs"][2]).read_text())
        self.assertEqual(record["native_exit"], 7)
        self.assertTrue(record["owned_group_absent"])

    def test_capture_truncation_retains_bounded_bytes_and_holds(self):
        m = self.manifest()
        m["steps"] = [
            self.step(
                "capture",
                "print('x'*10000)",
                effects=["read"],
                write_paths=[],
                capture_bytes=64,
            )
        ]
        self.admit(m)
        asyncio.run(self.rt.run())
        work = self.rt.status()["works"]["m1:capture"]
        self.assertEqual(work["status"], "EFFECT_UNKNOWN")
        self.assertLessEqual(
            sum(Path(p).stat().st_size for p in work["evidence_refs"][:2]), 64
        )
        record = json.loads(Path(work["evidence_refs"][2]).read_text())
        self.assertFalse(record["capture_complete"])
        self.assertEqual(record["stop_reason"], "CAPTURE_CAP")
        self.assertTrue(record["owned_group_absent"])


class RuntimeCheckpointTests(unittest.TestCase):
    """Actual Runtime.run/process boundaries; optional retained fixture evidence."""

    step = RuntimeTests.step
    manifest = RuntimeTests.manifest
    admit = RuntimeTests.admit

    def setUp(self):
        self.api = importlib.import_module("dopemux.supervisor.runtime")
        self.transport = importlib.import_module("dopemux.supervisor.transport")
        retained = os.environ.get("DMX_CHECKPOINT_TEST_EVIDENCE_ROOT")
        if retained:
            self.root = Path(
                tempfile.mkdtemp(prefix=self._testMethodName + "-", dir=retained)
            )
        else:
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            self.root = Path(temporary.name)
        self.root = self.root.resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.deadline = time.time() + 60
        self.rt = self.api.Runtime(
            self.root / "state", self.root / "returns", "master:test"
        )
        self.addCleanup(lambda: self.rt.close())

    def tearDown(self):
        processes = []
        for path in (self.root / "state/evidence").glob("*/START_ACK.json"):
            ack = json.loads(path.read_text())
            native = json.loads((path.parent / "PROCESS_RESULT.json").read_text())
            try:
                os.killpg(ack["pgid"], 0)
            except ProcessLookupError:
                absent = True
            else:
                absent = False
            processes.append(dict(start_ack=ack, native=native, group_absent=absent))
            self.assertTrue(
                absent, "Real local task process group remains or identity reused"
            )
            self.assertTrue(native["owned_group_absent"])
        (self.root / "PROCESS_CLOSURE.json").write_text(json.dumps(processes, indent=2))

    def _reopen(self):
        self.rt.close()
        self.rt = self.api.Runtime(
            self.root / "state", self.root / "returns", "master:test"
        )

    def _mutated_runner(self, change):
        original = self.api.LocalProcessRunner.__call__

        async def wrapped(runner, dispatch):
            result = await original(runner, dispatch)
            if dispatch.work.work_id == "m1:implement":
                return change(dispatch, result)
            return result

        return patch.object(self.api.LocalProcessRunner, "__call__", wrapped)

    def test_normal_run_checkpoints_actual_evidence_before_finish(self):
        self.admit()
        real_finish = self.rt.kernel.finish
        observed = []

        def finish(dispatch, result, **kwargs):
            work = self.rt.kernel.work_state(dispatch.work.work_id)
            self.assertEqual(work["status"], "RUNNING")
            self.assertEqual(len(work["checkpoints"]), 1)
            artifact = Path(work["checkpoints"][0][0])
            checkpoint = json.loads(artifact.read_text())
            self.assertEqual(checkpoint["attempt_id"], dispatch.attempt_id)
            self.assertEqual(
                checkpoint["input_fingerprint"], dispatch.work.input_fingerprint
            )
            self.assertFalse(checkpoint["mid_command"])
            for row in checkpoint["evidence"]:
                raw = Path(row["path"]).read_bytes()
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            observed.append(dispatch.attempt_id)
            return real_finish(dispatch, result, **kwargs)

        with patch.object(self.rt.kernel, "finish", finish):
            asyncio.run(self.rt.run())
        self.assertEqual(len(observed), 2)
        before = self.rt.kernel._state()
        self._reopen()
        asyncio.run(self.rt.run())
        self.assertEqual(before, self.rt.kernel._state())
        self.assertEqual((self.project / "checks.count").read_text(), "1")

    def test_failed_child_does_not_publish_success_checkpoint(self):
        plan = self.manifest()
        plan["steps"][0]["argv"][
            -1
        ] = "import sys;print('failed child',file=sys.stderr);sys.exit(7)"
        self.admit(plan)
        asyncio.run(self.rt.run())
        work = self.rt.kernel.work_state("m1:implement")
        self.assertEqual(work["status"], "FAILED")
        self.assertEqual(work["checkpoints"], [])
        self.assertFalse(
            list((self.root / "state/evidence").glob("*/STEP_BOUNDARY_CHECKPOINT.json"))
        )

    def test_native_identity_mismatch_is_unknown_without_checkpoint(self):
        self.admit()

        def change(dispatch, result):
            path = Path(result.evidence_refs[-1])
            (path.parent / "ORIGINAL_PROCESS_RESULT.json").write_bytes(
                path.read_bytes()
            )
            native = json.loads(path.read_text())
            native["attempt_id"] = "foreign-attempt"
            path.write_text(json.dumps(native))
            return result

        with self._mutated_runner(change):
            asyncio.run(self.rt.run())
        work = self.rt.kernel.work_state("m1:implement")
        self.assertEqual(work["status"], "EFFECT_UNKNOWN")
        self.assertEqual(work["checkpoints"], [])

    def test_changed_fingerprint_is_unknown_without_checkpoint(self):
        self.admit()

        def change(dispatch, result):
            with self.rt.kernel._transaction() as state:
                state["works"][dispatch.work.work_id]["spec"][
                    "input_fingerprint"
                ] = "changed"
            return result

        with self._mutated_runner(change):
            asyncio.run(self.rt.run())
        work = self.rt.kernel.work_state("m1:implement")
        self.assertEqual(work["status"], "EFFECT_UNKNOWN")
        self.assertEqual(work["checkpoints"], [])

    def test_foreign_evidence_reference_is_unknown_without_checkpoint(self):
        self.admit()

        def change(dispatch, result):
            return replace(
                result,
                evidence_refs=(
                    str(self.root / "foreign.log"),
                    *result.evidence_refs[1:],
                ),
            )

        with self._mutated_runner(change):
            asyncio.run(self.rt.run())
        work = self.rt.kernel.work_state("m1:implement")
        self.assertEqual(work["status"], "EFFECT_UNKNOWN")
        self.assertEqual(work["checkpoints"], [])

    def test_immutable_checkpoint_conflict_is_preserved_and_held(self):
        self.admit()
        conflict = []

        def change(dispatch, result):
            path = (
                Path(result.evidence_refs[-1]).parent / "STEP_BOUNDARY_CHECKPOINT.json"
            )
            path.write_text("conflicting immutable bytes")
            conflict.append(path)
            return result

        with self._mutated_runner(change):
            asyncio.run(self.rt.run())
        work = self.rt.kernel.work_state("m1:implement")
        self.assertEqual(work["status"], "EFFECT_UNKNOWN")
        self.assertEqual(work["checkpoints"], [])
        self.assertEqual(conflict[0].read_text(), "conflicting immutable bytes")

    def test_identical_checkpoint_hook_is_idempotent_while_running(self):
        self.assertTrue(
            hasattr(self.rt, "_checkpoint_step"),
            "Runtime checkpoint integration missing",
        )
        self.admit()
        original = self.rt._checkpoint_step

        def twice(dispatch, result):
            original(dispatch, result)
            original(dispatch, result)

        with patch.object(self.rt, "_checkpoint_step", twice):
            asyncio.run(self.rt.run())
        for work in self.rt.status()["works"].values():
            self.assertEqual(work["status"], "SUCCEEDED")
            self.assertEqual(len(work["checkpoints"]), 1)
        kinds = [
            json.loads(row[0])["kind"]
            for row in self.rt.kernel.db.execute("SELECT payload FROM outbox")
        ]
        self.assertEqual(kinds.count("CHECKPOINT"), 2)

    def _crash_boundary(self, boundary, exit_code, checkpoints):
        self.assertTrue(
            hasattr(self.rt, "_checkpoint_step"),
            "Runtime checkpoint integration missing",
        )
        self.admit()
        script = """import asyncio,json,os,sys
from pathlib import Path
from dopemux.supervisor.runtime import Runtime
root=Path(sys.argv[1]); boundary=sys.argv[2]; code=int(sys.argv[3])
rt=Runtime(root/'state',root/'returns','master:test')
original=rt._checkpoint_step
def checkpoint(dispatch,result):
    if boundary=='after-exit': os._exit(code)
    original(dispatch,result)
    if boundary=='after-checkpoint': os._exit(code)
rt._checkpoint_step=checkpoint
finish=rt.kernel.finish
def terminal(dispatch,result,**kwargs):
    finish(dispatch,result,**kwargs)
    if boundary=='after-finish' and dispatch.work.work_id=='m1:test': os._exit(code)
rt.kernel.finish=terminal
asyncio.run(rt.run())
raise RuntimeError('Fault boundary was not reached')
"""
        env = dict(
            PATH="/usr/bin:/bin",
            HOME=str(self.root),
            PYTHONPATH=str(Path(__file__).resolve().parents[3] / "src"),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONNOUSERSITE="1",
            PYTHON_DOTENV_DISABLED="1",
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-c",
                script,
                str(self.root),
                boundary,
                str(exit_code),
            ],
            cwd=self.root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=15)
        (self.root / "coordinator.stdout").write_bytes(stdout)
        (self.root / "coordinator.stderr").write_bytes(stderr)
        self.assertEqual(process.returncode, exit_code, stderr.decode())
        with self.assertRaises(ProcessLookupError):
            os.killpg(process.pid, 0)
        (self.root / "coordinator-result.json").write_text(
            json.dumps(
                dict(
                    pid=process.pid,
                    pgid=process.pid,
                    native_exit=process.returncode,
                    owned_group_absent=True,
                    boundary=boundary,
                )
            )
        )
        before = self.rt.kernel._state()
        ids = {k: v["attempt_id"] for k, v in before["works"].items()}
        self.assertEqual(
            sum(len(w["checkpoints"]) for w in before["works"].values()), checkpoints
        )
        native_count = len(
            list((self.root / "state/evidence").glob("*/START_ACK.json"))
        )
        self._reopen()
        asyncio.run(self.rt.run())
        after = self.rt.kernel._state()
        self.assertEqual(ids, {k: v["attempt_id"] for k, v in after["works"].items()})
        self.assertEqual(
            native_count,
            len(list((self.root / "state/evidence").glob("*/START_ACK.json"))),
        )
        if boundary != "after-finish":
            self.assertEqual(after["works"]["m1:implement"]["status"], "EFFECT_UNKNOWN")
            self.assertFalse((self.project / "checks.count").exists())
        else:
            self.assertTrue(
                all(w["status"] == "SUCCEEDED" for w in after["works"].values())
            )
            self.assertEqual((self.project / "checks.count").read_text(), "1")
            receiver = self.transport.ReturnReceiver(
                self.root / "returns", "master:test"
            )
            self.assertGreater(receiver.receive(), 0)
            asyncio.run(self.rt.deliver_returns())
            self.assertEqual(receiver.receive(), 0)
            asyncio.run(self.rt.deliver_returns())
            self.assertEqual(self.rt.kernel.pending_returns(), [])
            self.assertEqual(after, self.rt.kernel._state())

    def test_interruption_after_exit_before_checkpoint_holds_without_replay(self):
        self._crash_boundary("after-exit", 71, 0)

    def test_interruption_after_checkpoint_before_finish_holds_without_replay(self):
        self._crash_boundary("after-checkpoint", 72, 1)

    def test_interruption_after_finish_allows_delivery_without_replay(self):
        self._crash_boundary("after-finish", 73, 2)


if __name__ == "__main__":
    unittest.main()
