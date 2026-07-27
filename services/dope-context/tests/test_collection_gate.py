"""Collection compatibility gate (F-002).

The gate must fail closed on an incompatible collection, stay idempotent
across the double create_collection() call every index run makes, and keep the
manifest sentinel out of both reader paths.
"""

import asyncio
import types

import pytest

from src.embeddings.model_registry import (
    COLLECTION_MANIFEST_KEY,
    CollectionCompatibilityError,
    build_collection_manifest,
    compare_collection_manifests,
)
from src.search.dense_search import MultiVectorSearch, manifest_point_id


def _manifest(**overrides):
    base = dict(
        model="voyage-context-4",
        output_dimension=1024,
        output_dtype="float",
        chunker_version="v2",
    )
    base.update(overrides)
    return build_collection_manifest(**base)


class _FakeQdrant:
    """Minimal Qdrant double with real upsert/retrieve/scroll semantics."""

    def __init__(self, existing=None, points=None):
        self.collections = list(existing or [])
        self.points = dict(points or {})
        self.created = []

    async def get_collections(self):
        return types.SimpleNamespace(
            collections=[types.SimpleNamespace(name=n) for n in self.collections]
        )

    async def get_collection(self, collection_name):
        return types.SimpleNamespace(points_count=len(self.points), status="green")

    async def create_collection(self, collection_name, vectors_config=None, **kw):
        self.collections.append(collection_name)
        self.created.append(collection_name)
        return True

    async def create_payload_index(self, **kw):
        return types.SimpleNamespace(status="completed")

    async def upsert(self, collection_name, points):
        for point in points:
            self.points[str(point.id)] = point
        return types.SimpleNamespace(status="completed")

    async def retrieve(self, collection_name, ids, **kw):
        found = [self.points[str(i)] for i in ids if str(i) in self.points]
        return [types.SimpleNamespace(id=p.id, payload=p.payload) for p in found]

    async def scroll(self, collection_name, limit=100, offset=None, **kw):
        records = [
            types.SimpleNamespace(id=p.id, payload=p.payload)
            for p in self.points.values()
        ]
        return records, None


def _search(client, manifest=None, name="code_test"):
    s = MultiVectorSearch(collection_name=name, manifest=manifest)
    s.client = client
    return s


def test_create_writes_manifest_then_second_call_is_idempotent():
    """server.py and IndexingPipeline both call create_collection each run."""

    async def _run():
        client = _FakeQdrant()
        search = _search(client, _manifest())
        await search.create_collection()
        assert manifest_point_id("code_test") in client.points

        # second call, fresh instance so the in-process cache cannot mask it
        again = _search(client, _manifest())
        await again.create_collection()
        assert client.created == ["code_test"], "collection recreated"

    asyncio.run(_run())


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "voyage-context-3"),
        ("output_dimension", 512),
        ("output_dtype", "int8"),
        ("chunker_version", "v1"),
    ],
)
def test_incompatible_manifest_fails_closed_and_names_the_field(field, value):
    async def _run():
        client = _FakeQdrant()
        await _search(client, _manifest()).create_collection()

        conflicting = _search(client, _manifest(**{field: value}))
        with pytest.raises(CollectionCompatibilityError) as exc:
            await conflicting.insert_points_batch([])
        assert field in str(exc.value)

    asyncio.run(_run())


def test_write_without_a_manifest_is_refused():
    async def _run():
        client = _FakeQdrant(existing=["code_test"])
        with pytest.raises(CollectionCompatibilityError):
            await _search(client, None).insert_points_batch([])

    asyncio.run(_run())


def test_populated_collection_without_a_manifest_is_refused():
    """Vectors from an unknown configuration must not be written into."""

    async def _run():
        legacy = types.SimpleNamespace(id="legacy-1", payload={"text": "old"})
        client = _FakeQdrant(existing=["code_test"], points={"legacy-1": legacy})
        with pytest.raises(CollectionCompatibilityError) as exc:
            await _search(client, _manifest()).insert_points_batch([])
        assert "no compatibility manifest" in str(exc.value)

    asyncio.run(_run())


def test_empty_collection_without_a_manifest_is_adopted():
    async def _run():
        client = _FakeQdrant(existing=["code_test"])
        search = _search(client, _manifest())
        await search.insert_points_batch([])
        assert manifest_point_id("code_test") in client.points

    asyncio.run(_run())


def test_manifest_never_reaches_get_all_payloads():
    """It feeds BM25, docs stale reconciliation and sync."""

    async def _run():
        client = _FakeQdrant()
        search = _search(client, _manifest())
        await search.create_collection()
        client.points["real-1"] = types.SimpleNamespace(
            id="real-1", payload={"text": "a real chunk"}
        )

        payloads = await search.get_all_payloads()
        assert [p["id"] for p in payloads] == ["real-1"]
        assert not any(p.get(COLLECTION_MANIFEST_KEY) for p in payloads)

    asyncio.run(_run())


def test_compare_reports_every_disagreeing_field():
    stored = _manifest()
    active = _manifest(model="voyage-context-3", output_dimension=512)
    with pytest.raises(CollectionCompatibilityError) as exc:
        compare_collection_manifests(stored, active, collection_name="code_test")
    message = str(exc.value)
    assert "model" in message and "output_dimension" in message
