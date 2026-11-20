"""Contract tests: private SQLite, fake runners, no services or provider calls."""

import asyncio
import importlib
import tempfile
import unittest
from pathlib import Path


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        try:
            self.api = importlib.import_module("dopemux.supervisor.kernel")
        except ModuleNotFoundError:
            self.fail("Project supervisor kernel is not implemented")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = 100.0
        self.path = Path(self.tmp.name) / "supervisor.sqlite"
        self.s = self.api.Supervisor(self.path, clock=lambda: self.now, slots=2)
        self.addCleanup(self.s.close)
        self.s.bind_route("sol-binding", model_class="sol", valid_until=1000)
        self.s.bind_route("astra-binding", model_class="astra", valid_until=1000)
        self.grant("p1", "g1")

    def grant(self, project, grant, **changes):
        values = dict(
            grant_id=grant,
            project_id=project,
            issuer_ref="master:issued",
            scopes=("local",),
            effects=("read", "write", "test"),
            expires_at=1000,
            active_seconds=100,
            spend_limit_micros=100,
            max_parallel=2,
            harness_repairs=2,
            stop_conditions=("owner-stop",),
        )
        values.update(changes)
        self.s.admit(self.api.Grant(**values))

    def work(self, work_id="w1", **changes):
        values = dict(
            work_id=work_id,
            project_id="p1",
            grant_id="g1",
            input_fingerprint="input-v1" if work_id == "w1" else "input:" + work_id,
            scope="local",
            effects=("read",),
            writer_keys=(),
            depends_on=(),
            context_refs=("source:one",),
            route_refs=("astra-binding", "sol-binding"),
            max_spend_micros=10,
            timeout_seconds=5,
            gates={"security": "PASS", "spending": "PASS", "workflow": "PASS"},
        )
        values.update(changes)
        return self.api.Work(**values)

    def result(self, **changes):
        values = dict(status="SUCCEEDED", evidence_refs=("proof:one",), spent_micros=3)
        values.update(changes)
        return self.api.Result(**values)

    def test_independent_project_runs_while_another_is_held(self):
        self.grant("p2", "g2")
        self.s.enqueue(self.work("blocked", gates={"security": "DENIED"}))
        self.s.enqueue(self.work("ready", project_id="p2", grant_id="g2"))
        calls = []

        async def runner(dispatch):
            calls.append(dispatch.work.work_id)
            return self.result()

        asyncio.run(self.s.run_ready(runner))
        self.assertEqual(calls, ["ready"])
        self.assertEqual(self.s.work_state("blocked")["status"], "READY")

    def test_ready_work_backfills_without_waiting_for_slow_peer(self):
        self.s.enqueue(self.work("slow"))
        self.s.enqueue(self.work("fast"))
        self.s.enqueue(self.work("third"))

        async def scenario():
            release = asyncio.Event()

            async def runner(d):
                if d.work.work_id == "slow":
                    await asyncio.wait_for(release.wait(), 0.5)
                if d.work.work_id == "third":
                    release.set()
                return self.result()

            await self.s.run_ready(runner)

        asyncio.run(scenario())
        self.assertEqual(self.s.work_state("slow")["status"], "SUCCEEDED")
        self.assertEqual(self.s.work_state("third")["status"], "SUCCEEDED")

    def test_unknown_effect_survives_restart_and_holds_writer_without_replay(self):
        self.s.enqueue(self.work(writer_keys=("shared-output",)))
        dispatch = self.s.claim_ready()[0]
        self.s.finish(
            dispatch,
            self.result(status="EFFECT_UNKNOWN", spent_micros=None),
            elapsed_seconds=1,
        )
        self.s.close()
        self.s = self.api.Supervisor(self.path, clock=lambda: self.now, slots=2)
        self.addCleanup(self.s.close)
        self.grant("p2", "g2")
        self.s.enqueue(
            self.work(
                "other", project_id="p2", grant_id="g2", writer_keys=("shared-output",)
            )
        )
        self.assertEqual(self.s.claim_ready(), [])
        self.assertEqual(self.s.work_state("w1")["reserved_spend_micros"], 10)

    def test_crashed_running_intent_is_not_reclaimed(self):
        self.s.enqueue(self.work())
        self.s.claim_ready()
        self.s.close()
        self.s = self.api.Supervisor(self.path, clock=lambda: self.now)
        self.addCleanup(self.s.close)
        self.assertEqual(self.s.claim_ready(), [])
        self.s.recover_interrupted()
        self.assertEqual(self.s.work_state("w1")["status"], "EFFECT_UNKNOWN")

    def test_deadline_spend_and_active_budget_never_reset_on_reopen(self):
        self.grant("p3", "g3", active_seconds=2, spend_limit_micros=10)
        self.s.enqueue(self.work(project_id="p3", grant_id="g3", timeout_seconds=2))
        d = self.s.claim_ready()[0]
        self.s.finish(d, self.result(spent_micros=10), elapsed_seconds=2)
        self.s.close()
        self.s = self.api.Supervisor(self.path, clock=lambda: self.now)
        self.addCleanup(self.s.close)
        self.assertEqual(self.s._state()["grants"]["g3"]["active"], 2)
        self.assertEqual(self.s._state()["grants"]["g3"]["spent"], 10)
        self.s.enqueue(
            self.work("next", project_id="p3", grant_id="g3", max_spend_micros=1)
        )
        self.assertEqual(self.s.claim_ready(), [])
        self.now = 1001
        self.s.enqueue(self.work("expired"))
        self.assertEqual(self.s.claim_ready(), [])

    def test_one_writer_and_dependencies_require_native_acceptance(self):
        self.s.enqueue(self.work("first", writer_keys=("same",)))
        self.s.enqueue(self.work("second", writer_keys=("same",)))
        self.s.enqueue(self.work("child", depends_on=("first",)))
        ds = self.s.claim_ready()
        self.assertEqual([d.work.work_id for d in ds], ["first"])
        self.s.finish(ds[0], self.result(), elapsed_seconds=1)
        ds = self.s.claim_ready()
        self.assertEqual([d.work.work_id for d in ds], ["second"])
        self.s.accept(
            "first", receipt_ref="native:accepted", capability="first-capability"
        )
        self.assertEqual([d.work.work_id for d in self.s.claim_ready()], ["child"])

    def test_duplicate_input_and_evidence_reuse_and_return_acks_are_idempotent(self):
        w = self.work()
        self.s.enqueue(w)
        self.s.enqueue(w)
        d = self.s.claim_ready()[0]
        self.s.checkpoint(d, fingerprint="input-v1", evidence_refs=("proof:stage",))
        n = len(self.s.pending_returns())
        self.s.checkpoint(d, fingerprint="input-v1", evidence_refs=("proof:stage",))
        self.assertEqual(len(self.s.pending_returns()), n)
        self.s.finish(d, self.result(), elapsed_seconds=1)
        self.s.enqueue(w)
        self.assertEqual(self.s.claim_ready(), [])
        e = self.s.pending_returns()[0]
        self.now += 4
        self.s.ack(e["key"], e["digest"])
        self.s.ack(e["key"], e["digest"])
        with self.assertRaises(self.api.Conflict):
            self.s.ack(e["key"], "different-payload")
        self.assertNotIn(e["key"], [x["key"] for x in self.s.pending_returns()])
        with self.assertRaises(self.api.Conflict):
            self.s.enqueue(self.work(input_fingerprint="changed"))

    def test_sol_preference_pinned_route_and_invalidated_binding(self):
        self.s.enqueue(self.work())
        self.assertEqual(self.s.claim_ready()[0].route_ref, "sol-binding")
        self.s.enqueue(self.work("pinned", route_refs=("astra-binding",)))
        self.assertEqual(self.s.claim_ready()[0].route_ref, "astra-binding")
        self.s.invalidate_route("sol-binding")
        self.s.enqueue(self.work("invalid", route_refs=("sol-binding",)))
        self.assertEqual(self.s.claim_ready(), [])

    def test_scope_security_publication_and_no_vm_are_real_holds(self):
        bad = [
            self.work("scope", scope="outside"),
            self.work(
                "security",
                gates={"security": "UNKNOWN", "spending": "PASS", "workflow": "PASS"},
            ),
            self.work("publish", effects=("publish",)),
            self.work("vm", effects=("vm",)),
        ]
        for w in bad:
            self.s.enqueue(w)
        self.assertEqual(self.s.claim_ready(), [])
        self.s.stop_project("p1", "owner-stop")
        self.s.enqueue(self.work("stopped"))
        self.assertEqual(self.s.claim_ready(), [])

    def test_reserved_spend_prevents_parallel_oversubscription(self):
        self.s.enqueue(self.work("a", max_spend_micros=60))
        self.s.enqueue(self.work("b", max_spend_micros=60))
        self.assertEqual([d.work.work_id for d in self.s.claim_ready()], ["a"])

    def test_publication_requires_its_own_gate_even_inside_granted_effect_scope(self):
        self.grant("public", "public", effects=("publish",))
        self.s.enqueue(
            self.work(
                "missing-public-gate",
                project_id="public",
                grant_id="public",
                effects=("publish",),
                writer_keys=("public-output",),
            )
        )
        self.assertEqual(self.s.claim_ready(), [])
        gates = {
            "security": "PASS",
            "spending": "PASS",
            "workflow": "PASS",
            "public_release": "PASS",
        }
        self.s.enqueue(
            self.work(
                "approved-public-gate",
                project_id="public",
                grant_id="public",
                effects=("publish",),
                writer_keys=("public-output",),
                gates=gates,
            )
        )
        self.assertEqual(
            [d.work.work_id for d in self.s.claim_ready()], ["approved-public-gate"]
        )

    def test_no_vm_remains_a_global_exclusion_even_if_a_grant_lists_it(self):
        self.grant("vm", "vm", effects=("vm",))
        self.s.enqueue(self.work(project_id="vm", grant_id="vm", effects=("vm",)))
        self.assertEqual(self.s.claim_ready(), [])

    def test_timeout_or_runner_exception_is_unknown_not_retryable_failure(self):
        self.s.enqueue(self.work("timeout", timeout_seconds=0.01))

        async def runner(d):
            await asyncio.sleep(0.05)
            return self.result()

        asyncio.run(self.s.run_ready(runner))
        self.assertEqual(self.s.work_state("timeout")["status"], "EFFECT_UNKNOWN")
        self.assertEqual(self.s.claim_ready(), [])

    def test_finite_harness_repair_does_not_relaunch_or_reset(self):
        self.s.enqueue(self.work())
        self.assertTrue(self.s.record_harness_failure("w1", "parser-shape"))
        self.assertFalse(self.s.record_harness_failure("w1", "parser-shape"))
        self.assertEqual(self.s.work_state("w1")["harness_repairs"], 1)
        self.assertEqual(self.s.work_state("w1")["status"], "HELD")

    def test_metrics_separate_accepted_capability_from_completion_and_unknown_spend(
        self,
    ):
        self.s.enqueue(self.work())
        d = self.s.claim_ready()[0]
        self.s.finish(d, self.result(), elapsed_seconds=2)
        self.assertEqual(self.s.metrics("p1")["accepted_capabilities"], 0)
        self.s.accept("w1", receipt_ref="native:one", capability="usable-capability")
        self.s.accept("w1", receipt_ref="native:one", capability="usable-capability")
        m = self.s.metrics("p1")
        self.assertEqual(m["accepted_capabilities"], 1)
        self.assertEqual(m["spent_micros"], 3)
        self.assertEqual(m["active_seconds"], 2)
        self.assertIsNone(m["coordination_wait_seconds"])
        e = self.s.pending_returns()[0]
        self.now += 7
        self.s.ack(e["key"], e["digest"])
        self.assertEqual(self.s.metrics("p1")["coordination_wait_seconds"], 7)

    def test_unknown_spend_is_not_zero_even_with_zero_cash_reservation(self):
        self.s.enqueue(self.work(max_spend_micros=0))
        d = self.s.claim_ready()[0]
        self.s.finish(d, self.result(spent_micros=None), elapsed_seconds=1)
        self.assertIsNone(self.s.metrics("p1")["spent_micros"])
        self.s.enqueue(self.work("next"))
        self.assertEqual(self.s.claim_ready(), [])

    def test_running_harness_fault_cannot_release_writer_or_allocate_repair(self):
        self.s.enqueue(self.work(writer_keys=("shared",)))
        d = self.s.claim_ready()[0]
        self.assertFalse(self.s.record_harness_failure("w1", "parser"))
        self.assertEqual(self.s.work_state("w1")["status"], "RUNNING")
        self.s.enqueue(self.work("peer", writer_keys=("shared",)))
        self.assertEqual(self.s.claim_ready(), [])
        self.s.finish(d, self.result(), elapsed_seconds=1)

    def test_exhausted_harness_allowance_holds_affected_stage(self):
        self.grant("none", "no-repairs", harness_repairs=0)
        self.s.enqueue(self.work(project_id="none", grant_id="no-repairs"))
        self.assertFalse(self.s.record_harness_failure("w1", "parser"))
        self.assertEqual(self.s.work_state("w1")["status"], "HELD")

    def test_harness_repair_cannot_outlive_active_time_envelope(self):
        self.grant("small", "small", active_seconds=1)
        self.s.enqueue(self.work(project_id="small", grant_id="small"))
        d = self.s.claim_ready()[0]
        self.s.finish(d, self.result(), elapsed_seconds=1)
        self.assertFalse(self.s.record_harness_failure("w1", "parse"))
        self.assertEqual(self.s.work_state("w1")["harness_repairs"], 0)

    def test_mutation_requires_writer_and_heavy_work_is_serialized(self):
        self.s.enqueue(self.work("unowned", effects=("write",)))
        self.s.enqueue(self.work("heavy1", heavy=True))
        self.s.enqueue(self.work("heavy2", heavy=True))
        self.assertEqual([d.work.work_id for d in self.s.claim_ready()], ["heavy1"])

    def test_revocation_survives_identical_readmission(self):
        self.s.revoke("g1")
        self.grant("p1", "g1")
        self.s.enqueue(self.work())
        self.assertEqual(self.s.claim_ready(), [])

    def test_separate_coordinators_cannot_claim_same_work_or_budget(self):
        self.s.enqueue(self.work())
        other = self.api.Supervisor(self.path, clock=lambda: self.now)
        self.addCleanup(other.close)
        self.assertEqual(len(self.s.claim_ready()), 1)
        self.assertEqual(other.claim_ready(), [])

    def test_return_delivery_loss_reuses_payload_without_workload_replay(self):
        self.s.enqueue(self.work())
        d = self.s.claim_ready()[0]
        self.s.finish(d, self.result(), elapsed_seconds=1)
        delivered = []

        async def lost_ack(e):
            delivered.append(e)
            raise ConnectionError("ACK lost")

        with self.assertRaises(ConnectionError):
            asyncio.run(self.s.flush_returns(lost_ack))

        async def ack(e):
            delivered.append(e)
            return e["digest"]

        asyncio.run(self.s.flush_returns(ack))
        self.assertEqual(delivered[0], delivered[1])
        self.assertEqual(self.s.pending_returns(), [])
        self.assertEqual(self.s.claim_ready(), [])

    def test_malformed_runner_result_is_effect_unknown(self):
        self.s.enqueue(self.work())

        async def malformed(d):
            return self.result(spent_micros=-1)

        asyncio.run(self.s.run_ready(malformed))
        self.assertEqual(self.s.work_state("w1")["status"], "EFFECT_UNKNOWN")

    def test_project_stop_cancels_cooperative_runner_without_claiming_no_effect(self):
        self.s.enqueue(self.work())

        async def scenario():
            async def runner(d):
                self.s.stop_project("p1", "owner-stop")
                await asyncio.sleep(0.4)
                return self.result()

            await self.s.run_ready(runner)

        asyncio.run(scenario())
        self.assertEqual(self.s.work_state("w1")["status"], "EFFECT_UNKNOWN")

    def test_binding_invalidation_stops_running_stage_without_fallback_replay(self):
        self.s.enqueue(self.work())

        async def scenario():
            async def runner(d):
                self.s.invalidate_route("sol-binding")
                await asyncio.sleep(0.4)
                return self.result()

            await self.s.run_ready(runner)

        asyncio.run(scenario())
        self.assertEqual(self.s.work_state("w1")["status"], "EFFECT_UNKNOWN")
        self.assertEqual(self.s.work_state("w1")["route_ref"], "sol-binding")

    def test_running_and_recovered_spend_is_not_reported_as_settled_zero(self):
        self.s.enqueue(self.work())
        self.s.claim_ready()
        self.assertIsNone(self.s.metrics("p1")["spent_micros"])
        self.s.recover_interrupted()
        self.assertIsNone(self.s.metrics("p1")["spent_micros"])

    def test_duplicate_worker_result_reuses_transition_without_recharging(self):
        self.s.enqueue(self.work())
        d = self.s.claim_ready()[0]
        r = self.result()
        self.s.finish(d, r, elapsed_seconds=2)
        n = len(self.s.pending_returns())
        self.s.finish(d, r, elapsed_seconds=2)
        self.assertEqual(len(self.s.pending_returns()), n)
        self.assertEqual(self.s.metrics("p1")["spent_micros"], 3)
        self.assertEqual(self.s.metrics("p1")["active_seconds"], 2)
        with self.assertRaises(self.api.Conflict):
            self.s.finish(d, self.result(spent_micros=4), elapsed_seconds=2)

    def test_gate_changed_inside_immediate_return_is_rechecked(self):
        self.s.enqueue(self.work())

        async def runner(d):
            self.s.stop_project("p1", "owner-stop")
            return self.result()

        asyncio.run(self.s.run_ready(runner))
        self.assertEqual(self.s.work_state("w1")["status"], "EFFECT_UNKNOWN")

    def test_checkpoint_return_is_bounded(self):
        self.s.enqueue(self.work())
        d = self.s.claim_ready()[0]
        with self.assertRaises(ValueError):
            self.s.checkpoint(d, fingerprint="input-v1", evidence_refs=("x" * 17000,))
        self.assertEqual(self.s.work_state("w1")["checkpoints"], [])

    def test_invalid_numeric_limits_and_oversized_context_are_rejected(self):
        for value in [float("nan"), float("inf"), -1, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.grant("bad", "bad", active_seconds=value)
        with self.assertRaises(ValueError):
            self.s.enqueue(self.work(context_refs=("x" * 17000,)))


if __name__ == "__main__":
    unittest.main()
