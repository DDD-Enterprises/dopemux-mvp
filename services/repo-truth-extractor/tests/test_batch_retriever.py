from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "lib" / "batch_retriever.py"
    service_dir = module_path.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))
    spec = importlib.util.spec_from_file_location("batch_retriever_test", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _Content:
    def __init__(self, text: str) -> None:
        self.text = text


class _OpenAICompatClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = type(
            "_Client",
            (),
            {"files": type("_Files", (), {"content": staticmethod(lambda file_id: _Content('{"ok":true}\n'))})()},
        )()

    def get_batch_info(self, job_id: str):
        return {
            "id": job_id,
            "status": "completed",
            "output_file_id": "file-1",
            "error_file_id": "",
            "created_at": "",
            "completed_at": "2026-03-26T00:00:00Z",
            "failed_at": "",
            "expired_at": "",
        }

    def fetch_results(self, job_id: str):
        return [
            type(
                "_Result",
                (),
                {
                    "custom_id": "part-1",
                    "output_text": '{"artifacts": []}',
                    "error": None,
                    "meta": {"job_id": job_id},
                },
            )()
        ]


class _GeminiClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def poll(self, job_id: str) -> str:
        return "completed"

    def fetch_results(self, job_id: str):
        return [
            type(
                "_Result",
                (),
                {
                    "custom_id": "part-1",
                    "output_text": '{"artifacts": []}',
                    "error": None,
                    "meta": {"job_id": job_id},
                },
            )()
        ]


class _EventStore:
    def __init__(self) -> None:
        self.insert_calls = []
        self.run_events = []

    def insert_webhook_event_if_absent(self, **kwargs):
        self.insert_calls.append(kwargs)
        return True

    def fetch_webhook_event_id(self, provider: str, event_id: str):
        return f"{provider}:{event_id}"

    def append_run_event(self, row):
        self.run_events.append(row)


def test_retrieve_batches_dispatches_openai_and_xai(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "OpenAIBatchClient", _OpenAICompatClient)
    monkeypatch.setattr(module, "XAIBatchClient", _OpenAICompatClient)

    openai_results = module.retrieve_batches("openai", "key", ["job-openai"], tmp_path)
    xai_results = module.retrieve_batches("xai", "key", ["job-xai"], tmp_path)

    assert openai_results["job-openai"]["provider"] == "openai"
    assert openai_results["job-openai"]["output_file"].endswith("job-openai_output.jsonl")
    assert xai_results["job-xai"]["provider"] == "xai"
    assert xai_results["job-xai"]["output_file"].endswith("job-xai_output.jsonl")


def test_retrieve_batches_dispatches_gemini(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "GeminiBatchClient", _GeminiClient)

    results = module.retrieve_batches("gemini", "key", ["job-gemini"], tmp_path)

    assert results["job-gemini"]["provider"] == "gemini"
    assert results["job-gemini"]["output_file"].endswith("job-gemini_output.json")


def test_retrieve_batches_rejects_openrouter(tmp_path: Path) -> None:
    module = _load_module()

    try:
        module.retrieve_batches("openrouter", "key", ["job-openrouter"], tmp_path)
    except Exception as exc:
        assert "OpenRouter is not supported for live batch execution" in str(exc)
    else:
        raise AssertionError("Expected openrouter retrieval rejection")


def test_integrate_batch_results_uses_provider_argument(monkeypatch) -> None:
    module = _load_module()
    store = _EventStore()

    class _RunEventInsert:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setitem(sys.modules, "ledger.interface", type("_LedgerModule", (), {"RunEventInsert": _RunEventInsert})())

    integrated = module.integrate_batch_results_with_webhook(
        batch_results={
            "job-xai": {
                "status": "completed",
                "completed_at": "2026-03-26T00:00:00Z",
            }
        },
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="job-xai",
        provider="xai",
    )

    assert integrated == 1
    assert store.insert_calls[0]["provider"] == "xai"
    payload = json.loads(store.insert_calls[0]["payload_json"])
    assert payload["provider"] == "xai"
