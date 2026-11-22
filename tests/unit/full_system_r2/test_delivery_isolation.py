"""Local delivery provenance, publication race and project isolation."""

import asyncio
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from dopemux.supervisor.runtime import Runtime
from dopemux.supervisor import transport
from .fixtures import canonical, manifest


class DeliveryIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def event(self, n=1):
        payload = {"key": str(n), "project_id": "p1", "kind": "fixture-event"}
        return {
            "key": str(n),
            "payload": payload,
            "digest": hashlib.sha256(canonical(payload)).hexdigest(),
        }

    def test_local_record_does_not_assert_native_or_master_ack(self):
        event = self.event()
        publisher = transport.ReturnPublisher(self.root / "returns", "untrusted-master-label")
        asyncio.run(publisher(event))
        receiver = transport.LocalDeliveryRecorder(self.root / "returns", "untrusted-master-label")
        receiver.receive()
        record = json.loads(next((self.root / "returns/records").glob("*.json")).read_text())
        self.assertEqual(record["kind"], "LOCAL_DELIVERY_RECORD")
        self.assertEqual(record["native_acceptance"], "NOT_ASSERTED")
        self.assertEqual(record["master_ack"], "NOT_ASSERTED")
        self.assertEqual(record["recorded_by_uid"], os.getuid())

    def test_forged_legacy_ack_does_not_settle_delivery(self):
        event = self.event()
        publisher = transport.ReturnPublisher(self.root / "returns", "label")
        asyncio.run(publisher(event))
        legacy = self.root / "returns/acks"
        legacy.mkdir(mode=0o700)
        (legacy / transport.name(event["key"])).write_text(
            json.dumps({"key": event["key"], "digest": event["digest"], "receiver_ref": "label"})
        )
        self.assertIsNone(asyncio.run(publisher(event)))

    def test_permissive_existing_directory_is_not_silently_adopted(self):
        bad = self.root / "public"
        bad.mkdir(mode=0o755)
        with self.assertRaises(ValueError):
            transport.ReturnPublisher(bad, "label")

    def test_receiver_read_waits_until_link_publication_is_complete(self):
        target = self.root / "published.json"
        real_link = os.link

        def slow_link(*args, **kwargs):
            real_link(*args, **kwargs)
            time.sleep(0.05)

        with patch.object(transport.os, "link", slow_link):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                writing = pool.submit(transport.exclusive, target, {"value": 1})
                until = time.monotonic() + 2
                while not target.exists() and time.monotonic() < until:
                    time.sleep(0.001)
                reading = pool.submit(transport.read_json, target)
                self.assertEqual(reading.result(timeout=2), {"value": 1})
                self.assertTrue(writing.result(timeout=2))
        self.assertEqual(target.stat().st_nlink, 1)

    def test_transient_publication_failure_does_not_stop_unrelated_work(self):
        rt = Runtime(self.root / "state", self.root / "returns", "label")
        self.addCleanup(rt.close)
        p1, p2 = self.root / "p1", self.root / "p2"
        p1.mkdir()
        p2.mkdir()
        rt.admit(manifest(p1), authorization_ref="fixture-issued")
        rt.admit(manifest(p2, "m2", "p2"), authorization_ref="fixture-issued")

        async def unavailable(event):
            raise OSError("injected transient delivery failure")

        rt.publisher = unavailable
        asyncio.run(rt.run())
        self.assertTrue((p1 / "result.txt").exists())
        self.assertTrue((p2 / "result.txt").exists())
        self.assertEqual(rt.kernel._state()["stops"], {})
        self.assertGreater(len(rt.kernel.pending_returns()), 0)

    def test_actual_return_conflict_holds_only_affected_project(self):
        rt = Runtime(self.root / "state", self.root / "returns", "label")
        self.addCleanup(rt.close)
        one, two = self.root / "one", self.root / "two"
        one.mkdir()
        two.mkdir()
        rt.admit(manifest(one), authorization_ref="fixture-issued")
        rt.admit(manifest(two, "m2", "p2"), authorization_ref="fixture-issued")
        original = rt.publisher

        async def affected(event):
            if event["payload"]["project_id"] == "p1":
                raise transport.ReturnConflict("injected exact-key immutable conflict")
            return await original(event)

        rt.publisher = affected
        asyncio.run(rt.run())
        self.assertEqual(rt.kernel._state()["stops"], {"p1": "RETURN_CONFLICT"})
        self.assertTrue((two / "result.txt").exists())
        self.assertTrue(
            any(e["payload"]["project_id"] == "p1" for e in rt.kernel.pending_returns())
        )

    def test_forged_local_uid_record_is_not_delivery(self):
        event = self.event()
        publisher = transport.ReturnPublisher(self.root / "returns", "label")
        asyncio.run(publisher(event))
        forged = transport.local_record(event, "label")
        forged["recorded_by_uid"] = os.getuid() + 1
        transport.exclusive(publisher.records / transport.name(event["key"]), forged)
        with self.assertRaises(transport.ReturnConflict):
            asyncio.run(publisher(event))

    def test_invalid_published_inode_holds_its_project_without_portfolio_abort(self):
        rt = Runtime(self.root / "state", self.root / "returns", "label")
        self.addCleanup(rt.close)
        one, two = self.root / "one", self.root / "two"
        one.mkdir()
        two.mkdir()
        rt.admit(manifest(one), authorization_ref="fixture-issued")
        rt.admit(manifest(two, "m2", "p2"), authorization_ref="fixture-issued")
        first = next(e for e in rt.kernel.pending_returns() if e["payload"]["project_id"] == "p1")
        path = rt.publisher.events / transport.name(first["key"])
        path.write_bytes(b"x" * 40000)
        path.chmod(0o600)
        asyncio.run(rt.run())
        self.assertEqual(rt.kernel._state()["stops"], {"p1": "RETURN_CONFLICT"})
        self.assertTrue((two / "result.txt").exists())
