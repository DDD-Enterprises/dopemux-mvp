"""Contract tests for dope-context schemas."""

import json
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[4]
SCHEMAS = ROOT / "contracts" / "dope-context"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_docs_grouped_embed_request_schema_valid():
    schema = _load_schema("docs_grouped_embed.request.schema.json")
    payload = {
        "model": "voyage-context-3",
        "documents": [
            {
                "doc_id": "doc-1",
                "source_uri": "docs/ADR-0001.md",
                "chunks": [
                    {"chunk_id": "c0", "ordinal": 0, "text": "Title\n\nContext..."},
                    {"chunk_id": "c1", "ordinal": 1, "text": "Decision..."},
                ],
            }
        ],
    }
    jsonschema.validate(instance=payload, schema=schema)


def test_docs_grouped_embed_request_schema_rejects_wrong_model():
    schema = _load_schema("docs_grouped_embed.request.schema.json")
    payload = {
        "model": "voyage-3-large",
        "documents": [
            {
                "doc_id": "doc-1",
                "source_uri": "docs/ADR-0001.md",
                "chunks": [
                    {"chunk_id": "c0", "ordinal": 0, "text": "Context..."},
                ],
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=payload, schema=schema)


def test_search_response_schema_valid():
    schema = _load_schema("search.response.schema.json")
    payload = {
        "lane_used": "docs",
        "fusion_strategy": "hybrid_rrf",
        "rerank_used": True,
        "embed_model_used": "voyage-context-3",
        "results": [
            {
                "rank": 1,
                "score": 0.99,
                "source_uri": "docs/ADR-0001.md",
                "chunk_id": "c1",
                "snippet": "Decision...",
            }
        ],
        "timings_ms": {"embed": 12.0, "search": 8.0, "fuse": 1.0, "rerank": 20.0},
    }
    jsonschema.validate(instance=payload, schema=schema)


def test_search_response_schema_requires_provenance_fields():
    schema = _load_schema("search.response.schema.json")
    payload = {
        "fusion_strategy": "hybrid_rrf",
        "rerank_used": True,
        "results": [
            {
                "rank": 1,
                "score": 0.99,
                "source_uri": "docs/ADR-0001.md",
                "chunk_id": "c1",
                "snippet": "Decision...",
            }
        ],
        "timings_ms": {"embed": 12.0, "search": 8.0, "fuse": 1.0, "rerank": 20.0},
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=payload, schema=schema)
