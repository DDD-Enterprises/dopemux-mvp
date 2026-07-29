"""Contract tests between dope-context and the installed qdrant-client.

Every other test in this suite stubs the Qdrant client, so none of them can
notice when the real SDK drops a method we call. That is exactly how
``AsyncQdrantClient.search`` went missing: it was removed in favour of
``query_points`` while ``pyproject.toml`` pinned only ``qdrant-client>=1.15.0``,
so the whole dense-search path raised AttributeError at runtime -- in the repo
environment, in the built image, and in the running container -- with no test
failing anywhere.

These tests deliberately import the REAL client, never the stub.
"""

import importlib
import inspect
import os
import sys

import pytest

# The suite-wide conftest installs a fake qdrant_client before any test module
# imports. Drop it for this module so we introspect the genuine SDK.
_STUBBED = [name for name in sys.modules if name.startswith("qdrant_client")]
for _name in _STUBBED:
    if getattr(sys.modules[_name], "_dope_context_test_stub", False):
        del sys.modules[_name]
for _name in list(sys.modules):
    if _name.startswith("qdrant_client"):
        del sys.modules[_name]

real_qdrant = importlib.import_module("qdrant_client")
RealAsyncClient = real_qdrant.AsyncQdrantClient


# Methods dope-context calls on the async client. Keep in sync with
# src/search/dense_search.py.
REQUIRED_ASYNC_CLIENT_METHODS = (
    "get_collections",
    "get_collection",
    "create_collection",
    "create_payload_index",
    "delete_collection",
    "upsert",
    "retrieve",
    "delete",
    "scroll",
    "query_points",
)


@pytest.mark.parametrize("method", REQUIRED_ASYNC_CLIENT_METHODS)
def test_required_client_method_exists(method):
    assert hasattr(RealAsyncClient, method), (
        f"AsyncQdrantClient has no '{method}'. dense_search.py calls it; the "
        f"installed qdrant-client is {real_qdrant.__file__}. Either the SDK "
        "removed it or the pin drifted."
    )


def test_query_points_accepts_the_arguments_we_pass():
    """A method existing is not enough; the keywords must match too."""

    sig = inspect.signature(RealAsyncClient.query_points)
    for keyword in ("collection_name", "query", "using", "query_filter",
                    "limit", "search_params", "with_payload"):
        assert keyword in sig.parameters, (
            f"query_points has no '{keyword}' parameter: {sig}"
        )


def test_removed_search_method_is_not_reintroduced_by_accident():
    """Guards the reverse direction.

    If a future SDK restores ``.search`` this test fails, prompting a
    deliberate decision rather than two code paths drifting apart.
    """

    assert not hasattr(RealAsyncClient, "search"), (
        "AsyncQdrantClient.search exists again. dense_search.py now uses "
        "query_points; decide explicitly which API to standardise on."
    )


@pytest.mark.skipif(
    not os.getenv("DOPE_CONTEXT_LIVE_QDRANT"),
    reason="set DOPE_CONTEXT_LIVE_QDRANT=1 with a reachable Qdrant to run",
)
def test_dense_search_round_trip_against_live_qdrant():
    """End-to-end proof: index two points, search, check ranking.

    Opt-in because it needs a real Qdrant. It creates and deletes its own
    throwaway collection and touches nothing else.
    """

    import asyncio

    from src.embeddings.model_registry import build_collection_manifest
    from src.search.dense_search import MultiVectorSearch, SearchProfile

    name = "__dopectx_sdk_contract_probe__"

    def unit(index: int):
        vector = [0.0] * 1024
        vector[index] = 1.0
        return vector

    async def _run():
        search = MultiVectorSearch(
            collection_name=name,
            manifest=build_collection_manifest(
                model="voyage-context-4",
                output_dimension=1024,
                output_dtype="float",
                chunker_version="v2",
            ),
        )
        existing = [c.name for c in (await search.client.get_collections()).collections]
        assert name not in existing, "probe collection name collides"
        try:
            await search.create_collection()
            await search.insert_points_batch(
                [
                    (unit(0), unit(0), unit(0),
                     {"file_path": "a.py", "raw_code": "alpha"}, None),
                    (unit(1), unit(1), unit(1),
                     {"file_path": "b.py", "raw_code": "beta"}, None),
                ]
            )
            results = await search.search(
                unit(0), unit(0), unit(0), profile=SearchProfile.implementation()
            )
            assert results, "dense search returned nothing"
            assert results[0].file_path == "a.py"
            assert {r.file_path for r in results} == {"a.py", "b.py"}, (
                "manifest sentinel leaked into search results"
            )
        finally:
            await search.client.delete_collection(collection_name=name)

    asyncio.run(_run())
