"""Regressions for the frozen candidate's independent L2 findings F1–F10."""

import asyncio
import unittest
import test_kernel as fixtures


class ReviewRegressions(unittest.TestCase):
    setUp = fixtures.SupervisorTests.setUp
    grant = fixtures.SupervisorTests.grant
    work = fixtures.SupervisorTests.work
    result = fixtures.SupervisorTests.result

    def test_enforced_timeout_does_not_stop_project_and_records_cause(self):
        self.s.enqueue(self.work(timeout_seconds=0.01))

        async def slow(d):
            await asyncio.sleep(1)

        asyncio.run(self.s.run_ready(slow))
        self.assertNotIn("p1", self.s._state()["stops"])
        self.assertIn("kernel:timeout", self.s.work_state("w1")["evidence_refs"])

    def test_finite_attempt_cap_survives_reopen(self):
        self.grant("p2", "limited", max_attempts=1)
        self.s.enqueue(self.work("one", project_id="p2", grant_id="limited"))
        d = self.s.claim_ready()[0]
        self.s.finish(d, self.result(), elapsed_seconds=1)
        self.s.close()
        self.s = self.api.Supervisor(self.path, clock=lambda: self.now)
        self.addCleanup(self.s.close)
        self.s.enqueue(
            self.work(
                "two", project_id="p2", grant_id="limited", input_fingerprint="new"
            )
        )
        self.assertEqual(self.s.claim_ready(), [])
        self.assertEqual(self.s._state()["grants"]["limited"]["attempts"], 1)

    def test_equivalent_successor_is_held_for_verified_reuse(self):
        self.s.enqueue(self.work())
        self.s.finish(self.s.claim_ready()[0], self.result(), elapsed_seconds=1)
        self.s.enqueue(self.work("successor", input_fingerprint="input-v1"))
        self.assertEqual(self.s.claim_ready(), [])
        self.assertEqual(self.s.work_state("successor")["reuse_source"], "w1")
        self.s.reuse_success("successor", receipt_ref="adapter:verified-unchanged")
        self.assertEqual(self.s.work_state("successor")["status"], "SUCCEEDED")
        self.assertIsNone(self.s.work_state("successor")["native_acceptance"])

    def test_unknowns_retain_writers_but_do_not_starve_unrelated_project(self):
        for name in ("a", "b"):
            self.s.enqueue(self.work(name, input_fingerprint=name, writer_keys=(name,)))
        for d in self.s.claim_ready():
            self.s.finish(
                d,
                self.result(status="EFFECT_UNKNOWN", spent_micros=None),
                elapsed_seconds=1,
            )
        self.grant("p2", "g2")
        self.s.enqueue(self.work("other", project_id="p2", grant_id="g2"))
        self.assertEqual([d.work.work_id for d in self.s.claim_ready()], ["other"])
        self.s.resolve_unknown(
            "a",
            outcome="FAILED",
            spent_micros=2,
            elapsed_seconds=1,
            evidence_refs=("native:closed",),
            receipt_ref="adapter:reconciled",
            process_closed=True,
        )
        self.s.resolve_unknown(
            "a",
            outcome="FAILED",
            spent_micros=2,
            elapsed_seconds=1,
            evidence_refs=("native:closed",),
            receipt_ref="adapter:reconciled",
            process_closed=True,
        )
        self.assertEqual(self.s.work_state("a")["reserved_spend_micros"], 0)
        self.assertEqual(self.s.work_state("a")["status"], "FAILED")

    def test_gate_updates_are_receipt_bound_and_invalidate_running_work(self):
        self.s.enqueue(self.work(gates={"security": "DENIED"}))
        self.assertEqual(self.s.claim_ready(), [])
        gates = {"security": "PASS", "workflow": "PASS", "spending": "PASS"}
        self.s.update_gates("w1", gates=gates, receipt_ref="native:gate1")

        async def runner(d):
            self.s.update_gates(
                "w1", gates={"security": "DENIED"}, receipt_ref="native:gate2"
            )
            return self.result(evidence_refs=("proof:observed",), spent_micros=2)

        asyncio.run(self.s.run_ready(runner))
        w = self.s.work_state("w1")
        self.assertEqual(w["status"], "EFFECT_UNKNOWN")
        self.assertIn("proof:observed", w["evidence_refs"])
        self.assertFalse(w["spend_unknown"])
        with self.assertRaises(self.api.Conflict):
            self.s.update_gates("w1", gates=gates, receipt_ref="native:gate2")

    def test_new_preferred_binding_does_not_invalidate_running_route(self):
        self.s.enqueue(self.work(route_refs=("astra-binding", "new-sol")))

        async def runner(d):
            self.s.bind_route("new-sol", model_class="sol", valid_until=1000)
            return self.result()

        asyncio.run(self.s.run_ready(runner))
        self.assertEqual(self.s.work_state("w1")["status"], "SUCCEEDED")
        self.assertEqual(self.s.work_state("w1")["route_ref"], "astra-binding")

    def test_harness_hold_never_clobbers_terminal_result(self):
        self.s.enqueue(self.work())
        self.s.finish(self.s.claim_ready()[0], self.result(), elapsed_seconds=1)
        self.s.record_harness_failure("w1", "parse")
        self.s.record_harness_failure("w1", "parse")
        self.assertEqual(self.s.work_state("w1")["status"], "SUCCEEDED")
        self.s.accept("w1", receipt_ref="native:accept", capability="working")

    def test_declared_stop_conditions_and_real_overruns(self):
        with self.assertRaises(ValueError):
            self.s.stop_project("p1", "undeclared-condition")
        self.s.enqueue(self.work())
        with self.assertRaises(self.api.Conflict):
            self.s.accept("w1", receipt_ref="native:early", capability="no")
        d = self.s.claim_ready()[0]
        self.s.finish(d, self.result(spent_micros=11), elapsed_seconds=6)
        self.assertEqual(self.s._state()["stops"]["p1"], "ACTIVE_TIME_OVERRUN")
        self.assertGreater(self.s.metrics("p1")["spent_micros"], 10)

    def test_restarted_intent_requires_actual_custody_settlement(self):
        self.s.enqueue(self.work())
        self.s.claim_ready()
        self.s.recover_interrupted()
        self.s.resolve_unknown(
            "w1",
            outcome="FAILED",
            spent_micros=0,
            elapsed_seconds=1,
            evidence_refs=("native:no-owned-process",),
            receipt_ref="native:closed",
            process_closed=True,
        )
        self.assertEqual(self.s.work_state("w1")["status"], "FAILED")
        self.assertEqual(self.s.metrics("p1")["spent_micros"], 0)

    def test_parallel_cap_stale_attempt_and_spend_overrun(self):
        from dataclasses import replace

        self.grant("p2", "serial", max_parallel=1)
        self.s.enqueue(self.work("one", project_id="p2", grant_id="serial"))
        self.s.enqueue(self.work("two", project_id="p2", grant_id="serial"))
        dispatches = self.s.claim_ready()
        self.assertEqual(len(dispatches), 1)
        with self.assertRaises(self.api.Conflict):
            self.s.finish(
                replace(dispatches[0], attempt_id="stale"),
                self.result(),
                elapsed_seconds=1,
            )
        self.s.finish(dispatches[0], self.result(spent_micros=11), elapsed_seconds=1)
        self.assertEqual(self.s._state()["stops"]["p2"], "SPEND_OVERRUN")

    def test_two_connections_race_one_dispatch_intent(self):
        import concurrent.futures
        import threading

        self.s.enqueue(self.work())
        barrier = threading.Barrier(2)

        def claim():
            connection = self.api.Supervisor(self.path, clock=lambda: self.now)
            try:
                barrier.wait(timeout=2)
                return connection.claim_ready()
            finally:
                connection.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            claims = [
                f.result(timeout=3) for f in [pool.submit(claim), pool.submit(claim)]
            ]
        self.assertEqual(sum(map(len, claims)), 1)

    def test_expiry_mid_run_preserves_observed_diagnostics(self):
        self.s.enqueue(self.work())

        async def runner(d):
            self.now = 1001
            return self.result(evidence_refs=("native:stderr",), spent_micros=2)

        asyncio.run(self.s.run_ready(runner))
        self.assertEqual(self.s.work_state("w1")["status"], "EFFECT_UNKNOWN")
        self.assertIn("native:stderr", self.s.work_state("w1")["evidence_refs"])
