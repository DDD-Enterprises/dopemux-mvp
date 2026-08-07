"""Shared pytest fixtures/bootstrap for the dope-context test suite.

TP-DOPECONTEXT-TEST-HARNESS-0005
---------------------------------
Two unrelated problems previously made nine tests in test_mcp_server.py fail:

1. FastMCP 2.14.0 wraps every @mcp.tool()-decorated function in a
   fastmcp.tools.tool.FunctionTool (a pydantic model), which is not itself
   callable. The original coroutine function is exposed as a plain pydantic
   field, FunctionTool.fn (see fastmcp/tools/tool.py::FunctionTool in the
   installed package -- the class declares "fn: Callable[..., Any]"
   directly, it is not a private or internal attribute). Tests that invoked
   the decorated name itself (e.g. "await search_code(...)") raised
   "TypeError: 'FunctionTool' object is not callable". The resolve_tool
   fixture below is the single place that knows this.

2. Three test modules in this directory (test_docs_pipeline_invariants.py,
   test_hybrid_determinism.py, and this suite's own test_mcp_server.py) each
   register a fake qdrant_client module via
   sys.modules.setdefault("qdrant_client", ...) so that importing
   src.search.dense_search (which does
   "from qdrant_client import AsyncQdrantClient" at module scope) never
   pulls in the real, network-calling SDK. setdefault means whichever file's
   stub is registered first wins for the rest of the process -- and pytest
   collects test files alphabetically, so test_docs_pipeline_invariants.py
   (a bare class with no methods beyond __init__) used to win the race over
   test_mcp_server.py's more complete stub. That produced real, but
   accidental, failures: AttributeError: 'AsyncQdrantClient' object has no
   attribute 'get_collections' (uncaught, in test_index_workspace_tool) and
   a caught-and-swallowed version of the same thing that surfaced as
   KeyError: 'file_path' / KeyError: 'reranked' two tests later, because
   _search_code_impl's collection-existence check treats any exception from
   the client as "collection not found" and returns an error payload
   instead of reaching the embedder/reranker mocks.

   pytest always imports a directory's conftest.py before it imports any
   test module in that directory, so registering the complete stub here
   makes it win the setdefault race unconditionally, regardless of which
   test file pytest happens to collect first. This does not change what the
   three files that already register their own (weaker) stub see: their
   registration calls just become no-ops for the already-populated
   qdrant_client key, and the shape of what they get is a superset of what
   they defined (extra methods, no behaviour removed).

Every method on the stub below matches the corresponding method's name and
call shape on the real qdrant_client.AsyncQdrantClient (checked against the
installed qdrant-client package, currently 1.18.0). One real-SDK method used
by src/search/dense_search.py -- .search() -- has no match at all: it was
removed from the SDK in favour of .query_points(). That stub method has
deliberately been left out here rather than faked, per the packet invariant
that a stub must not paper over a method that does not exist on the real
client; none of the fixed tests exercise that code path (they mock
_hybrid_search/_pipeline/the _*_impl functions directly, never a real
MultiVectorSearch.search() call).

3. A second, previously-invisible instance of the exact same pollution
   pattern exists for ``voyageai``: ``src/embeddings/contextualized_embedder.py``
   does ``from voyageai import AsyncClient`` at module scope, and
   ``test_docs_pipeline_invariants.py`` imports that module (via
   ``DocIndexingPipeline``) *without* stubbing ``voyageai`` first — so the
   real, network-calling ``voyageai.AsyncClient`` gets bound before
   ``test_mcp_server.py``'s own ``voyageai`` stub (registered at its module
   top) ever gets a chance to win the ``setdefault`` race. This was
   invisible before this packet's fix because ``test_search_code_tool`` and
   ``test_search_code_without_reranking`` used to fail earlier, on the
   qdrant collection check, and never reached the embedding call. Once that
   was fixed, they reached ``_get_cached_embedder(...)`` — which
   unconditionally constructs a **real** ``VoyageEmbedder`` regardless of
   the test's ``patch("src.mcp.server._embedder", ...)`` (that patch target
   is never consulted by ``_get_cached_embedder``; contrast
   ``_get_cached_reranker``, which does check ``if _reranker:`` first) — and
   attempted a real embed call with the placeholder key ``"test"``, which is
   exactly the live-call risk this packet's hard constraints forbid.
   Registering a real-signature-matching ``voyageai`` stub here, first,
   closes that gap the same way as the qdrant one: the real
   ``VoyageEmbedder``/``ContextualizedEmbedder``/``VoyageReranker`` objects
   still get constructed for real, but their ``self.client`` is our fake,
   offline ``AsyncClient``, so no network call ever happens and the affected
   tests' assertions (which never depend on specific embedding values) are
   satisfied by whatever placeholder vector the stub returns.

   The stub's ``embed``/``contextualized_embed``/``rerank`` methods
   deliberately do **not** accept ``**kwargs`` — the installed voyageai
   AsyncClient's real methods do not either (introspected via
   ``inspect.signature``), and ``src/embeddings/voyage_embedder.py`` /
   ``contextualized_embedder.py`` / ``src/rerank/voyage_reranker.py`` all
   rely on a genuine ``TypeError`` from an unsupported keyword (e.g.
   ``voyage_reranker.py`` passes ``return_documents``, which the real SDK
   has never accepted) to fall back to a legacy call shape. A stub with a
   permissive ``**kwargs`` catch-all would silently swallow that mismatch
   and never exercise the fallback path the real client forces.
"""

import sys
import types
from typing import Any, Callable, List, Optional


def _install_qdrant_stub() -> None:
    """Register a complete, signature-matching qdrant_client stub.

    Uses sys.modules.setdefault (not a hard assignment) so that if a real
    qdrant_client import has somehow already happened before this conftest
    loads, we do not clobber it -- but under normal pytest collection
    nothing has imported it yet, so this call wins.
    """
    if "qdrant_client" in sys.modules and hasattr(
        sys.modules["qdrant_client"], "_dope_context_test_stub"
    ):
        return  # already installed by this function in this process

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
        "PointIdsList",
    ]:
        # Retain constructor kwargs as attributes. A stub that silently drops
        # what it was given cannot be asserted against, and would let a caller
        # pass a field the real model does not have without anyone noticing.
        def _init(self, *args, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        setattr(models_module, name, type(name, (), {"__init__": _init}))
    models_module.PayloadSchemaType = types.SimpleNamespace(KEYWORD="keyword")
    models_module.Distance = types.SimpleNamespace(DOT="dot")

    class _StubAsyncQdrantClient:
        """Test double for qdrant_client.AsyncQdrantClient.

        Every method here mirrors the name and keyword shape of the real
        method on the installed SDK (introspected via
        inspect.signature(qdrant_client.AsyncQdrantClient.<name>)), so a
        caller that passes an argument the real client would accept is
        accepted here too, and nothing is invented that the real client does
        not have.
        """

        def __init__(self, *args, **kwargs):
            pass

        async def get_collections(self, **kwargs: Any):
            return types.SimpleNamespace(collections=[])

        async def get_collection(self, collection_name: str, **kwargs: Any):
            return types.SimpleNamespace(
                config=types.SimpleNamespace(name=collection_name),
                points_count=1,
                status="green",
            )

        async def create_collection(
            self,
            collection_name: str,
            vectors_config: Any = None,
            **kwargs: Any,
        ) -> bool:
            return True

        async def create_payload_index(
            self,
            collection_name: str,
            field_name: str,
            field_schema: Any = None,
            wait: bool = True,
            **kwargs: Any,
        ):
            return types.SimpleNamespace(operation_id=0, status="completed")

        async def delete_collection(
            self, collection_name: str, timeout: Optional[int] = None, **kwargs: Any
        ) -> bool:
            return True

        async def delete(
            self,
            collection_name: str,
            points_selector: Any = None,
            wait: bool = True,
            **kwargs: Any,
        ):
            return types.SimpleNamespace(operation_id=0, status="completed")

        async def scroll(
            self,
            collection_name: str,
            scroll_filter: Any = None,
            limit: int = 10,
            offset: Any = None,
            with_payload: Any = True,
            with_vectors: Any = False,
            **kwargs: Any,
        ):
            return [], None

    qdrant_module = types.ModuleType("qdrant_client")
    qdrant_module.AsyncQdrantClient = _StubAsyncQdrantClient  # type: ignore[attr-defined]
    qdrant_module._dope_context_test_stub = True  # type: ignore[attr-defined]

    http_module = types.ModuleType("qdrant_client.http")
    http_module.models = models_module

    sys.modules.setdefault("qdrant_client", qdrant_module)
    sys.modules.setdefault("qdrant_client.http", http_module)
    sys.modules.setdefault("qdrant_client.http.models", models_module)


_install_qdrant_stub()


def _install_voyageai_stub() -> None:
    """Register a complete, signature-matching voyageai stub.

    See the module docstring, point 3, for why this exists. Uses
    sys.modules.setdefault for the same reason as the qdrant stub: this
    conftest.py loads before every test module in this directory, so it
    wins the race regardless of collection order.
    """
    if "voyageai" in sys.modules and hasattr(
        sys.modules["voyageai"], "_dope_context_test_stub"
    ):
        return  # already installed by this function in this process

    class _StubVoyageAsyncClient:
        """Test double for voyageai.AsyncClient.

        Method signatures match the installed voyageai AsyncClient exactly
        (introspected via inspect.signature) -- no catch-all **kwargs,
        because the real SDK has none either and src/embeddings/*.py depends
        on a genuine TypeError to detect an unsupported keyword and retry
        with a legacy call shape.
        """

        def __init__(
            self,
            api_key: Optional[str] = None,
            max_retries: int = 0,
            timeout: Optional[float] = None,
            base_url: Optional[str] = None,
        ) -> None:
            pass

        async def embed(
            self,
            texts: List[str],
            model: Optional[str] = None,
            input_type: Optional[str] = None,
            truncation: bool = True,
            output_dtype: Optional[str] = None,
            output_dimension: Optional[int] = None,
        ):
            return types.SimpleNamespace(
                embeddings=[[0.0] * 4 for _ in texts],
                total_tokens=len(texts),
            )

        async def contextualized_embed(
            self,
            inputs: List[List[str]],
            model: str,
            input_type: Optional[str] = None,
            output_dtype: Optional[str] = None,
            output_dimension: Optional[int] = None,
            chunk_fn: Optional[Callable[[str], List[str]]] = None,
        ):
            return types.SimpleNamespace(
                results=[
                    types.SimpleNamespace(
                        embeddings=[[0.0] * 4 for _ in chunk_group],
                        chunk_texts=list(chunk_group),
                    )
                    for chunk_group in inputs
                ],
            )

        async def rerank(
            self,
            query: str,
            documents: List[str],
            model: str,
            top_k: Optional[int] = None,
            truncation: bool = True,
        ):
            return types.SimpleNamespace(results=[])

    class _StubVoyageClient:
        """Test double for the SYNCHRONOUS voyageai.Client.

        The real module exposes both Client and AsyncClient, and
        src/utils/model_tokenizer.py resolves the sync one via
        getattr(voyageai, "Client", None) for tokenize(). A stub that omitted
        it made VoyageTokenCounter fall back to _client = None, which silently
        disables the model-aware tokenizer path this suite means to exercise.
        """

        def __init__(
            self,
            api_key: Optional[str] = None,
            max_retries: int = 0,
            timeout: Optional[float] = None,
            base_url: Optional[str] = None,
        ) -> None:
            pass

        def tokenize(self, texts: List[str], model: Optional[str] = None) -> List[Any]:
            # Mirrors tokenizers.Encoding: only .ids is consumed.
            return [
                types.SimpleNamespace(ids=list(range(max(1, len(t) // 4))))
                for t in texts
            ]

        def count_tokens(self, texts: List[str], model: Optional[str] = None) -> int:
            return sum(max(1, len(t) // 4) for t in texts)

    voyageai_module = types.ModuleType("voyageai")
    voyageai_module.AsyncClient = _StubVoyageAsyncClient  # type: ignore[attr-defined]
    voyageai_module.Client = _StubVoyageClient  # type: ignore[attr-defined]
    voyageai_module._dope_context_test_stub = True  # type: ignore[attr-defined]

    sys.modules.setdefault("voyageai", voyageai_module)


_install_voyageai_stub()


import pytest  # noqa: E402  (must follow the stub installation above)


@pytest.fixture
def resolve_tool():
    """Return a helper that unwraps a FastMCP FunctionTool to its coroutine.

    Usage::

        async def test_something(resolve_tool):
            result = await resolve_tool(some_mcp_tool)(arg=1)

    Plain (already-unwrapped) callables are returned unchanged, so it is
    always safe to call regardless of whether tool went through
    @mcp.tool().
    """

    def _resolve(tool):
        return getattr(tool, "fn", tool)

    return _resolve
