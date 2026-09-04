"""Vector-space invariants for dope-context retrieval.

Every named vector must be indexed and queried with the same model, endpoint,
dimension and dtype. Equal dimensionality is NOT evidence of compatibility:
voyage-context-4 and voyage-code-3 both emit 1024-dim vectors, so Qdrant
accepts a cross-family mismatch silently (F-001).
"""

import ast
import sys
import types
from pathlib import Path

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
    DEFAULT_CODE_MODEL,
    DEFAULT_DOC_MODEL,
    env_model,
    get_model_spec,
    resolve_context_model,
)
from src.index_profile import (  # noqa: E402
    build_code_collection_profile,
    build_docs_collection_profile,
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


def test_code_content_index_and_query_models_agree():
    """Code content_vec index model must equal the search_code query model.

    F-001 closed by TP-DOPECONTEXT-VECTOR-SPACE-0004 / D1 (2026-09-04). The
    old shape indexed content_vec with a contextualized model and queried it
    with a flat one; both are 1024-dim, so Qdrant accepted the mismatch
    silently. Both sides now read the single profile below, so the property is
    structural rather than a matching pair of literals.
    """
    code = build_code_collection_profile()
    content = code.content()

    assert content.model == DEFAULT_CODE_MODEL
    assert content.endpoint == "embeddings"
    assert get_model_spec(content.model, endpoint=content.endpoint)
    # The whole point of D1: one vector space for the code collection.
    assert content.model == code.title().model == code.breadcrumb().model
    assert content.endpoint == code.title().endpoint == code.breadcrumb().endpoint


def test_all_six_named_vectors_agree_across_index_and_query():
    """Acceptance criterion: index/query agreement for all six named vectors.

    Index and query differ only in ``input_type``; model, endpoint, dimension
    and dtype must be identical, because those four are what determine the
    vector space a query lands in.
    """
    code = build_code_collection_profile()
    docs = build_docs_collection_profile()

    seen = []
    for collection in (code, docs):
        for name in ("content_vec", "title_vec", "breadcrumb_vec"):
            vector = collection.vectors[name]
            seen.append(vector.vector_role)
            assert vector.index_input_type == "document"
            assert vector.query_input_type == "query"
            # A vector's model must actually be valid on the endpoint it names.
            spec = get_model_spec(vector.model, endpoint=vector.endpoint)
            assert vector.dimension in spec.supported_dimensions
            assert vector.dtype

    assert len(seen) == 6, seen
    assert len(set(seen)) == 6, f"vector roles must be distinct: {seen}"


def test_code_content_vector_is_not_contextualized():
    """Regression guard for the D1 dispatch bug.

    Both the index path (indexing_pipeline) and the query path (mcp/server)
    branch on ``content_profile.endpoint``. If the code content vector ever
    resolves back to a contextualized model without those branches changing,
    the flat model would be sent to ``contextualized_embed``, which rejects
    every model outside the voyage-context family.
    """
    content = build_code_collection_profile().content()
    assert content.endpoint != "contextualized_embeddings"
    assert not content.model.startswith("voyage-context-")


def _src_root() -> Path:
    return Path(__file__).resolve().parents[1] / "src"


def _flat_embed_calls(path: Path):
    """Every ``.embed(...)`` / ``.embed_batch(...)`` call node in a module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"embed", "embed_batch"}
    ]


def _all_flat_embed_calls():
    """(relative path, call node) for every flat embed across the whole tree.

    Round-6 finding NARROW_AST_TESTS: scanning two hardcoded files leaves a
    flat embed added anywhere else unchecked. The embedder modules themselves
    are excluded because they *define* embed/embed_batch rather than call them
    on a profile, and the contextualized embedder is a different endpoint.
    """
    root = _src_root()
    skip = {
        root / "embeddings" / "voyage_embedder.py",
        root / "embeddings" / "contextualized_embedder.py",
    }
    found = []
    for path in sorted(root.rglob("*.py")):
        if path in skip:
            continue
        for call in _flat_embed_calls(path):
            found.append((path.relative_to(root).as_posix(), call))
    return found


def test_flat_embeds_disable_truncation():
    """Every flat embed must pass truncation=False, or oversize input is lost.

    Round-5 audit finding SILENT_TRUNCATION. VoyageEmbedder's per-input guards
    (voyage_embedder.py:293, :373) are both conditioned on ``not truncation``,
    and ``truncation`` DEFAULTS TO TRUE (:273, :333). Relying on the default
    therefore means an oversize chunk is silently truncated by the API and
    embedded as a vector representing only its first ~32K tokens -- no error,
    no log. The call sites must opt out explicitly.

    Asserted over the AST, not by substring search: a grep for a literal can be
    satisfied by an unrelated line elsewhere in the file, whereas this checks
    the keyword on each actual call node.
    """
    calls = _all_flat_embed_calls()
    assert calls, "expected at least one flat embed call in the tree"
    for rel, call in calls:
        if True:
            kwargs = {kw.arg: kw.value for kw in call.keywords}
            assert "truncation" in kwargs, (
                f"{rel}:{call.lineno} embeds without an explicit truncation "
                "argument; the default is True, which silently truncates"
            )
            value = kwargs["truncation"]
            assert isinstance(value, ast.Constant) and value.value is False, (
                f"{rel}:{call.lineno} must pass truncation=False"
            )


def test_flat_embed_models_are_read_from_the_profile():
    """The content/title/breadcrumb model must be an attribute of a profile.

    Stronger than the substring check it replaces: requiring the ``model=``
    argument to be an attribute access ending in ``.model`` rejects both a
    hard-coded string (model="voyage-code-4") and a module constant
    (model=DEFAULT_CODE_MODEL), while still allowing an aliased profile
    (cp = content_profile; cp.model), which is genuinely deriving from it.
    """
    for rel, call in _all_flat_embed_calls():
        if True:
            kwargs = {kw.arg: kw.value for kw in call.keywords}
            model = kwargs.get("model")
            assert model is not None, f"{rel}:{call.lineno} embeds without model="
            assert isinstance(model, ast.Attribute) and model.attr == "model", (
                f"{rel}:{call.lineno} must pass a profile's .model, not a "
                "literal or a module-level constant"
            )
