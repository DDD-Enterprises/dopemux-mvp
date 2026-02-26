"""Determinism tests for hybrid search fusion."""

import asyncio
import sys
import types


def _register_qdrant_stub():
    models_module = types.ModuleType("qdrant_client.http.models")
    for name in [
        "HnswConfigDiff",
        "VectorParams",
        "PointStruct",
        "SearchRequest",
        "NamedVector",
        "Filter",
        "FieldCondition",
        "MatchValue",
        "SearchParams",
    ]:
        setattr(models_module, name, type(name, (), {"__init__": lambda self, *args, **kwargs: None}))
    models_module.PayloadSchemaType = types.SimpleNamespace(KEYWORD="keyword")
    models_module.Distance = types.SimpleNamespace(DOT="dot")

    qdrant_module = types.ModuleType("qdrant_client")
    qdrant_module.AsyncQdrantClient = type(
        "AsyncQdrantClient",
        (),
        {"__init__": lambda self, *args, **kwargs: None},
    )

    http_module = types.ModuleType("qdrant_client.http")
    http_module.models = models_module

    sys.modules.setdefault("qdrant_client", qdrant_module)
    sys.modules.setdefault("qdrant_client.http", http_module)
    sys.modules.setdefault("qdrant_client.http.models", models_module)


_register_qdrant_stub()
sys.modules.setdefault("rank_bm25", types.SimpleNamespace(BM25Okapi=type("BM25Okapi", (), {"__init__": lambda self, corpus: None, "get_scores": lambda self, query: []})))

from src.search.dense_search import SearchProfile, SearchResult
from src.search.hybrid_search import HybridSearch, reciprocal_rank_fusion


class FakeDenseSearch:
    """Dense search stub returning fixed results."""

    async def search(
        self,
        query_content_vector,
        query_title_vector,
        query_breadcrumb_vector,
        profile,
        filter_by=None,
    ):
        return [
            SearchResult(
                id="b",
                score=0.5,
                payload={"id": "b", "file_path": "b.py", "raw_code": "b"},
                file_path="b.py",
                function_name=None,
                language="python",
                content="b",
                context_snippet=None,
            ),
            SearchResult(
                id="a",
                score=0.5,
                payload={"id": "a", "file_path": "a.py", "raw_code": "a"},
                file_path="a.py",
                function_name=None,
                language="python",
                content="a",
                context_snippet=None,
            ),
        ]


class FakeBM25:
    """BM25 stub returning deterministic sparse rankings."""

    def search(self, query, top_k=100):
        return [("a", 1.0), ("b", 1.0)]

    def get_document(self, doc_id):
        return {
            "id": doc_id,
            "file_path": f"{doc_id}.py",
            "raw_code": doc_id,
            "language": "python",
        }


def test_reciprocal_rank_fusion_tie_breaks_by_doc_id():
    rankings = [
        [("b", 1.0), ("a", 0.9)],
        [("a", 1.0), ("b", 0.9)],
    ]
    fused = reciprocal_rank_fusion(rankings=rankings, k=60)
    assert [doc_id for doc_id, _ in fused] == ["a", "b"]


def test_hybrid_search_stable_order_across_repeats():
    async def _run():
        hybrid = HybridSearch(
            dense_search=FakeDenseSearch(),
            bm25_index=FakeBM25(),
        )
        profile = SearchProfile.implementation()
        query_vectors = {
            "content": [0.1] * 4,
            "title": [0.1] * 4,
            "breadcrumb": [0.1] * 4,
        }
        first = await hybrid.search(
            query_vectors=query_vectors,
            query_text="deterministic search",
            profile=profile,
            top_k=2,
        )
        second = await hybrid.search(
            query_vectors=query_vectors,
            query_text="deterministic search",
            profile=profile,
            top_k=2,
        )

        assert [r.id for r in first] == ["a", "b"]
        assert [r.id for r in first] == [r.id for r in second]

    asyncio.run(_run())
