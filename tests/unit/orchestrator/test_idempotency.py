import os
import shutil
import tempfile
import sqlite3
import pytest

from dopemux.orchestrator.idempotency import IdempotencyStore, IdempotencyState


class TestIdempotencyStore:
    @pytest.fixture(autouse=True)
    def setup_temp_xdg(self):
        # Redirect HOME to avoid writing to real XDG share in tests
        self.temp_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get("HOME")
        os.environ["HOME"] = self.temp_dir
        
        yield
        
        shutil.rmtree(self.temp_dir)
        if self.original_home is not None:
            os.environ["HOME"] = self.original_home
        else:
            os.environ.pop("HOME", None)

    def test_db_path_and_pragmas(self):
        store = IdempotencyStore()
        db_path = store.db_path
        
        # Verify db is inside XDG path
        expected_dir = os.path.expanduser("~/.local/share/dopemux")
        assert os.path.dirname(db_path) == expected_dir
        assert os.path.basename(db_path) == "idempotency.db"
        
        # Check pragmas
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0].lower()
        assert journal_mode == "wal"
        
        cursor.execute("PRAGMA busy_timeout;")
        timeout = cursor.fetchone()[0]
        assert timeout == 5000
        
        conn.close()

    def test_state_transitions(self):
        store = IdempotencyStore()
        
        idem_key = "key-abc-123"
        
        # Phase 1: record intent
        store.record_intent(
            idempotency_key=idem_key,
            project_id="proj-1",
            workflow_id="wf-1",
            transition_name="start"
        )
        
        record = store.get_record(idem_key)
        assert record is not None
        assert record["status"] == IdempotencyState.INTENT.value
        assert record["project_id"] == "proj-1"
        assert record["workflow_id"] == "wf-1"
        
        # Phase 2: transition in progress
        store.update_status(idem_key, IdempotencyState.TRANSITIONING)
        record = store.get_record(idem_key)
        assert record["status"] == IdempotencyState.TRANSITIONING.value
        
        # Phase 3: completed
        store.update_status(idem_key, IdempotencyState.COMPLETED)
        record = store.get_record(idem_key)
        assert record["status"] == IdempotencyState.COMPLETED.value

    def test_recovery_sweep(self):
        store = IdempotencyStore()
        
        store.record_intent("key-1", "proj-1", "wf-1", "start")
        store.record_intent("key-2", "proj-1", "wf-2", "resolve")
        store.update_status("key-2", IdempotencyState.TRANSITIONING)
        store.record_intent("key-3", "proj-1", "wf-3", "close")
        store.update_status("key-3", IdempotencyState.COMPLETED)
        
        # Sweep should find key-1 (intent) and key-2 (transitioning)
        incomplete = store.get_incomplete_records()
        assert len(incomplete) == 2
        
        keys = {r["idempotency_key"] for r in incomplete}
        assert keys == {"key-1", "key-2"}

    def test_sync_adapter_transition_idempotency(self, monkeypatch):
        from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter
        
        captured_request = []
        def mock_request(method, path, **kwargs):
            # Simulate a successful HTTP call
            captured_request.append((method, path, kwargs))
            class Response:
                def raise_for_status(self): pass
                def json(self): return {"status": "success"}
            return Response()
            
        adapter = SyncTaskOrchestratorAdapter()
        monkeypatch.setattr(adapter, "_request", mock_request)
        
        idem_key = "idem-test-999"
        # Call transition
        adapter.transition(
            project_id="proj-9",
            workflow_id="wf-9",
            transition_name="start",
            idempotency_key=idem_key
        )
        
        # Verify the record status is COMPLETED in the store
        record = adapter.idempotency_store.get_record(idem_key)
        assert record is not None
        assert record["status"] == "completed"
        assert record["project_id"] == "proj-9"
        assert record["workflow_id"] == "wf-9"
        assert record["transition_name"] == "start"

    def test_sync_adapter_cached_response_payload(self, monkeypatch):
        import json
        from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter
        
        call_count = 0
        def mock_request(method, path, **kwargs):
            nonlocal call_count
            call_count += 1
            class Response:
                def raise_for_status(self): pass
                def json(self): return {"status": "real-call"}
            return Response()
            
        adapter = SyncTaskOrchestratorAdapter()
        monkeypatch.setattr(adapter, "_request", mock_request)
        
        idem_key = "idem-cache-hit"
        # Manually seed a completed record in the database with a cached response
        adapter.idempotency_store.record_intent(idem_key, "proj-1", "wf-1", "start")
        adapter.idempotency_store.update_status(
            idem_key, 
            IdempotencyState.COMPLETED, 
            response_json=json.dumps({"status": "cached-hit", "data": 42})
        )
        
        # Call transition
        result = adapter.transition(
            project_id="proj-1",
            workflow_id="wf-1",
            transition_name="start",
            idempotency_key=idem_key
        )
        
        # Verify that mock_request was NEVER called and cached payload was returned
        assert call_count == 0
        assert result == {"status": "cached-hit", "data": 42}

    def test_sync_adapter_transitioning_raises_error(self, monkeypatch):
        from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter
        
        def mock_request(method, path, **kwargs):
            class Response:
                def raise_for_status(self): pass
                def json(self): return {"status": "success"}
            return Response()
            
        adapter = SyncTaskOrchestratorAdapter()
        monkeypatch.setattr(adapter, "_request", mock_request)
        
        idem_key = "idem-transitioning"
        # Seed transitioning state
        adapter.idempotency_store.record_intent(idem_key, "proj-1", "wf-1", "start")
        adapter.idempotency_store.update_status(idem_key, IdempotencyState.TRANSITIONING)
        
        # Call transition should raise RuntimeError
        with pytest.raises(RuntimeError, match="Transition already in progress"):
            adapter.transition(
                project_id="proj-1",
                workflow_id="wf-1",
                transition_name="start",
                idempotency_key=idem_key
            )

    def test_sync_adapter_rollback_on_failure(self, monkeypatch):
        from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter
        
        def mock_request_fail(method, path, **kwargs):
            raise RuntimeError("Network failure simulation")
            
        adapter = SyncTaskOrchestratorAdapter()
        monkeypatch.setattr(adapter, "_request", mock_request_fail)
        
        idem_key = "idem-rollback-key"
        
        with pytest.raises(RuntimeError, match="Network failure simulation"):
            adapter.transition(
                project_id="proj-1",
                workflow_id="wf-1",
                transition_name="start",
                idempotency_key=idem_key
            )
            
        # Verify it has rolled back to INTENT
        record = adapter.idempotency_store.get_record(idem_key)
        assert record is not None
        assert record["status"] == IdempotencyState.INTENT.value

    def test_sync_adapter_concurrent_transitions(self, monkeypatch):
        import threading
        import time
        from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter
        
        # We simulate a slow downstream transition call (network latency of 0.2s)
        request_called = 0
        def mock_request(method, path, **kwargs):
            nonlocal request_called
            request_called += 1
            time.sleep(0.2)
            class Response:
                def raise_for_status(self): pass
                def json(self): return {"status": "success", "call_count": request_called}
            return Response()
            
        adapter = SyncTaskOrchestratorAdapter()
        monkeypatch.setattr(adapter, "_request", mock_request)
        
        idem_key = "concurrent-key-xyz"
        
        results = []
        errors = []
        
        def run_transition():
            try:
                res = adapter.transition(
                    project_id="proj-1",
                    workflow_id="wf-1",
                    transition_name="start",
                    idempotency_key=idem_key
                )
                results.append(res)
            except Exception as e:
                errors.append(e)
                
        # Spawn 3 threads concurrently calling the exact same key
        threads = [threading.Thread(target=run_transition) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        # ASSERTION 1: Only ONE thread bypassed the guard to hit mock_request
        assert request_called == 1
        
        # ASSERTION 2: Other threads got the cached result or raised the correct exception
        assert len(results) >= 1
        for err in errors:
            assert isinstance(err, RuntimeError)
            assert "Transition already in progress" in str(err)

    def test_idempotency_store_lease_expiration(self):
        from datetime import datetime, timezone, timedelta
        
        store = IdempotencyStore()
        idem_key = "lease-expired-key"
        
        # Seed record as TRANSITIONING but with an expired timestamp (e.g. 40 seconds ago)
        expired_time = (datetime.now(timezone.utc) - timedelta(seconds=40)).isoformat()
        
        with store._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                INSERT INTO idempotency_records 
                (idempotency_key, project_id, workflow_id, transition_name, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (idem_key, "proj-1", "wf-1", "start", IdempotencyState.TRANSITIONING.value, expired_time, expired_time)
            )
            conn.execute("COMMIT;")
            
        # Calling claim_transition should hijack the transition and return PROCEED
        claim = store.claim_transition(
            idempotency_key=idem_key,
            project_id="proj-1",
            workflow_id="wf-1",
            transition_name="start",
            lease_timeout_seconds=30.0
        )
        
        assert claim["action"] == "PROCEED"
        
        # Verify the record status is updated to transitioning and the updated_at is fresh
        record = store.get_record(idem_key)
        assert record["status"] == IdempotencyState.TRANSITIONING.value
        
        # Verify it has a fresh timestamp
        updated_at = datetime.fromisoformat(record["updated_at"])
        assert (datetime.now(timezone.utc) - updated_at).total_seconds() < 5.0
