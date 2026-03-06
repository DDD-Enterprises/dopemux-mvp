from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence


@dataclass(frozen=True)
class BatchRequest:
    custom_id: str
    model_id: str
    system_prompt: str
    user_content: str
    force_json_output: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchResult:
    custom_id: str
    output_text: str
    error: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchRoute:
    provider: str
    model_id: str
    api_key_env: str
    base_url: Optional[str] = None


class BatchClient(Protocol):
    def submit(
        self,
        requests: Sequence[BatchRequest],
        route: BatchRoute,
        step_context: Dict[str, Any],
    ) -> str:
        ...

    def poll(self, job_id: str) -> str:
        ...

    def fetch_results(self, job_id: str) -> List[BatchResult]:
        ...

    def cancel(self, job_id: str) -> None:
        ...


class OpenAIBatchClient:
    def __init__(self, api_key: str, base_url: Optional[str] = None) -> None:
        from openai import OpenAI

        kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)

    def submit(
        self,
        requests: Sequence[BatchRequest],
        route: BatchRoute,
        step_context: Dict[str, Any],
    ) -> str:
        payload_rows: List[Dict[str, Any]] = []
        for req in requests:
            body: Dict[str, Any] = {
                "model": req.model_id,
                "messages": [
                    {"role": "system", "content": req.system_prompt},
                    {"role": "user", "content": req.user_content},
                ],
                "temperature": 0.1,
            }
            if req.force_json_output:
                # v4/TP-008: Default to strict mode for batch JSON output if supported.
                # In a full implementation, we'd check if the model supports it.
                body["response_format"] = {"type": "json_object"}
                # If strict is explicitly requested in metadata or implied by lane
                if req.metadata.get("strict") == "true":
                    # Placeholder for actual JSON Schema if using json_schema type
                    pass
            payload_rows.append(
                {
                    "custom_id": req.custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body,
                }
            )

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".jsonl", delete=False) as handle:
            for row in payload_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            payload_path = Path(handle.name)
        try:
            with payload_path.open("rb") as upload:
                file_obj = self._client.files.create(file=upload, purpose="batch")
            metadata = {
                "provider": route.provider,
                "phase": str(step_context.get("phase", "")),
                "step_id": str(step_context.get("step_id", "")),
            }
            batch_obj = self._client.batches.create(
                completion_window="24h",
                endpoint="/v1/chat/completions",
                input_file_id=str(file_obj.id),
                metadata=metadata,
            )
            return str(batch_obj.id)
        finally:
            try:
                payload_path.unlink(missing_ok=True)
            except Exception:
                pass

    def poll(self, job_id: str) -> str:
        batch_obj = self._client.batches.retrieve(job_id)
        return str(getattr(batch_obj, "status", "") or "").lower()

    def get_batch_info(self, job_id: str) -> Dict[str, Any]:
        """Retrieve batch information including status and file IDs."""
        batch_obj = self._client.batches.retrieve(job_id)
        return {
            "id": str(getattr(batch_obj, "id", "")),
            "status": str(getattr(batch_obj, "status", "") or "").lower(),
            "output_file_id": str(getattr(batch_obj, "output_file_id", "") or ""),
            "error_file_id": str(getattr(batch_obj, "error_file_id", "") or ""),
            "created_at": str(getattr(batch_obj, "created_at", "")),
            "completed_at": str(getattr(batch_obj, "completed_at", "")),
            "failed_at": str(getattr(batch_obj, "failed_at", "")),
            "expired_at": str(getattr(batch_obj, "expired_at", "")),
        }

    def fetch_results(self, job_id: str) -> List[BatchResult]:
        batch_obj = self._client.batches.retrieve(job_id)
        output_file_id = getattr(batch_obj, "output_file_id", None)
        if not output_file_id:
            return []
        content_obj = self._client.files.content(str(output_file_id))
        if hasattr(content_obj, "text"):
            raw_text = str(content_obj.text)
        elif hasattr(content_obj, "read"):
            value = content_obj.read()
            raw_text = value.decode("utf-8", errors="replace") if isinstance(value, (bytes, bytearray)) else str(value)
        else:
            raw_text = str(content_obj)

        results: List[BatchResult] = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            custom_id = str(row.get("custom_id") or "")
            response = row.get("response") if isinstance(row.get("response"), dict) else {}
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            output_text = ""
            choices = body.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0] if isinstance(choices[0], dict) else {}
                message = first.get("message") if isinstance(first.get("message"), dict) else {}
                output_text = str(message.get("content") or "")
            error_row = row.get("error")
            error = None
            if isinstance(error_row, dict):
                error = str(error_row.get("message") or error_row.get("code") or "batch_error")
            results.append(BatchResult(custom_id=custom_id, output_text=output_text, error=error, meta=row))
        return results

    def cancel(self, job_id: str) -> None:
        self._client.batches.cancel(job_id)


class XAIBatchClient(OpenAIBatchClient):
    def __init__(self, api_key: str, base_url: str = "https://api.x.ai/v1") -> None:
        super().__init__(api_key=api_key, base_url=base_url)


class OpenRouterBatchClient(OpenAIBatchClient):
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1") -> None:
        super().__init__(api_key=api_key, base_url=base_url)


class GeminiBatchClient:
    def __init__(self, api_key: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)

    def submit(
        self,
        requests: Sequence[BatchRequest],
        route: BatchRoute,
        step_context: Dict[str, Any],
    ) -> str:
        inlined_requests: List[Dict[str, Any]] = []
        for req in requests:
            config: Dict[str, Any] = {"temperature": 0.1, "system_instruction": req.system_prompt}
            if req.force_json_output:
                config["response_mime_type"] = "application/json"
            inlined_requests.append(
                {
                    "model": req.model_id,
                    "contents": req.user_content,
                    "metadata": {"custom_id": req.custom_id, **req.metadata},
                    "config": config,
                }
            )
        batch_job = self._client.batches.create(
            model=route.model_id,
            src=inlined_requests,
            config={
                "display_name": f"{step_context.get('phase','')}_{step_context.get('step_id','')}",
            },
        )
        return str(getattr(batch_job, "name", "") or "")

    def poll(self, job_id: str) -> str:
        batch_job = self._client.batches.get(name=job_id)
        state = getattr(batch_job, "state", None)
        return str(state).lower() if state is not None else ""

    def fetch_results(self, job_id: str) -> List[BatchResult]:
        batch_job = self._client.batches.get(name=job_id)
        dest = getattr(batch_job, "dest", None)
        inlined_responses = getattr(dest, "inlined_responses", None) if dest is not None else None
        if not isinstance(inlined_responses, list):
            return []
        results: List[BatchResult] = []
        for row in inlined_responses:
            metadata = getattr(row, "metadata", None)
            metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
            custom_id = str(metadata_dict.get("custom_id") or "")
            response_obj = getattr(row, "response", None)
            output_text = str(getattr(response_obj, "text", "") or "")
            error_obj = getattr(row, "error", None)
            error = str(getattr(error_obj, "message", "") or "") if error_obj is not None else None
            results.append(
                BatchResult(
                    custom_id=custom_id,
                    output_text=output_text,
                    error=error,
                    meta={
                        "metadata": metadata_dict,
                        "state": str(getattr(batch_job, "state", "")),
                    },
                )
            )
        return results

    def cancel(self, job_id: str) -> None:
        self._client.batches.cancel(name=job_id)

