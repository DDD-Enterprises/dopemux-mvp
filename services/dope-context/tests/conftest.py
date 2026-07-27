"""Shared pytest fixtures and import-order stubs for dope-context tests."""

from __future__ import annotations

import sys
import types


def _install_qdrant_stub() -> None:
    """Install a minimal AsyncQdrantClient stub before dense_search binds the real one."""

    class _StubAsyncQdrantClient:
        def __init__(self, *args, **kwargs):
            pass

        async def get_collections(self):
            return types.SimpleNamespace(collections=[])

        async def get_collection(self, collection_name, **kwargs):
            return types.SimpleNamespace(
                config=types.SimpleNamespace(name=collection_name),
                points_count=1,
                status="green",
            )

        async def create_collection(self, *args, **kwargs):
            return

        async def create_payload_index(self, *args, **kwargs):
            return

        async def delete(self, *args, **kwargs):
            return

        async def delete_collection(self, *args, **kwargs):
            return

        async def scroll(self, *args, **kwargs):
            return [], None

        async def search(self, *args, **kwargs):
            return []

        async def upsert(self, *args, **kwargs):
            return

    models_module = types.ModuleType("qdrant_client.http.models")

    class _StubStruct:
        def __init__(self, *args, **kwargs):
            self.__dict__.update(kwargs)

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
        "PointIdsList",
        "Distance",
    ]:
        setattr(models_module, name, type(name, (_StubStruct,), {}))

    models_module.PayloadSchemaType = types.SimpleNamespace(KEYWORD="keyword")
    models_module.Distance = types.SimpleNamespace(DOT="dot")

    qdrant_module = types.ModuleType("qdrant_client")
    qdrant_module.AsyncQdrantClient = _StubAsyncQdrantClient  # type: ignore

    http_module = types.ModuleType("qdrant_client.http")
    http_module.models = models_module

    sys.modules["qdrant_client"] = qdrant_module
    sys.modules["qdrant_client.http"] = http_module
    sys.modules["qdrant_client.http.models"] = models_module


# Apply before test modules import production search code.
_install_qdrant_stub()
