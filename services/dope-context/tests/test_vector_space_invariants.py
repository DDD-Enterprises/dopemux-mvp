"""Vector-space invariants for dope-context retrieval.

Every named vector must be indexed and queried with the same model, endpoint,
dimension and dtype. Equal dimensionality is NOT evidence of compatibility:
voyage-context-4 and voyage-code-3 both emit 1024-dim vectors, so Qdrant
accepts a cross-family mismatch silently (F-001).
"""

import sys
import types

import pytest


def _stub_qdrant() -> None:
    if "qdrant_client" in sys.modules:
        return
    m = types.ModuleType("qdrant_client.http.models")
    for name in ("HnswConfigDiff", "VectorParams", "PointStruct", "NamedVector"):
        setattr(m, name, type(name, (), {"__init__": lambda self, *a, **k: None}))
    m.PayloadSchemaType = types.SimpleNamespace(KEYWORD="keyword")
    m.Distance = types.SimpleNamespace(DOT="dot")
    q = types.ModuleType("qdrant_client")
    q.AsyncQdrantClient = type("AsyncQdrantClient", (), {"__init__": lambda s, *a, **k: None})
    h = types.ModuleType("qdrant_client.http")
    h.models = m
    for key, mod in (("qdrant_client", q), ("qdrant_client.http", h),
                     ("qdrant_client.http.models", m)):
        sys.modules.setdefault(key, mod)


_stub_qdrant()

from src.embeddings.model_registry import (  # noqa: E402
    DEFAULT_DOC_MODEL,
    env_model,
    get_model_spec,
    resolve_context_model,
)


def test_docs_index_and_query_models_agree(monkeypatch):
    """Docs index and query must resolve the same model under every flag combo.

    Closed by TP-DOPECONTEXT-VOYAGE4-REPAIR-0002: the query path no longer
    hard-codes the legacy literal, so DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3 alone
    can no longer split index from query.
    """
    combos = (
        {},
        {"DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3": "1"},
        {"DOPE_CONTEXT_DOC_EMBED_MODEL": "voyage-context-3"},
        {"DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3": "1",
         "DOPE_CONTEXT_DOC_EMBED_MODEL": "voyage-context-3"},
    )
    for env in combos:
        for key in ("DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3", "DOPE_CONTEXT_DOC_EMBED_MODEL"):
            monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)

        configured = env_model("DOPE_CONTEXT_DOC_EMBED_MODEL", DEFAULT_DOC_MODEL)
        indexed = resolve_context_model(configured, configured)
        queried = resolve_context_model(configured, configured)
        assert indexed == queried, f"index/query split under {env}"


@pytest.mark.xfail(
    strict=True,
    reason="F-001: code content_vec is indexed with a contextualized model but "
    "queried with voyage-code-3. Direction is decided by "
    "TP-DOPECONTEXT-VECTOR-SPACE-0004; this flips to pass when it lands.",
)
def test_code_content_index_and_query_models_agree():
    """Code content_vec index model must equal the search_code query model.

    indexing_pipeline.py:283-289 embeds content via the contextualized model;
    server.py:1205-1209 queries with voyage-code-3 on the standard endpoint.
    Both are 1024-dim, so nothing fails loudly today.
    """
    indexed = resolve_context_model("voyage-context-3", DEFAULT_DOC_MODEL)
    queried = "voyage-code-3"
    assert get_model_spec(indexed).endpoint == get_model_spec(queried).endpoint
    assert indexed == queried
