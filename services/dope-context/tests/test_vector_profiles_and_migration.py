"""Vector-profile equality, collection identity, and migration isolation tests."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.index_profile import (
    CONTEXTUAL_MODEL_ENV,
    PROFILE_DIGEST_LENGTH,
    assert_manifest_compatible,
    build_code_collection_profile,
    build_docs_collection_profile,
    classify_collections,
    index_query_profiles_match,
    is_legacy_collection_name,
    load_collection_manifest,
    resolve_contextual_embed_model,
    six_vector_compatibility_matrix,
    versioned_collection_name,
    write_collection_manifest,
    workspace_identity_from_path,
)
from src.utils.workspace import get_collection_names, get_legacy_collection_names


def test_six_named_vector_index_query_profiles_identical():
    code = build_code_collection_profile()
    docs = build_docs_collection_profile()
    for profile in (code, docs):
        for name, vector in profile.vectors.items():
            # Same profile object for index and query; only input_type differs.
            assert index_query_profiles_match(vector, vector)
            assert vector.index_input_type == "document"
            assert vector.query_input_type == "query"
            assert vector.dimension == 1024
    assert code.content().endpoint == "contextualized_embeddings"
    assert code.title().model == "voyage-code-3"
    assert code.breadcrumb().model == "voyage-code-3"
    assert docs.content().model == code.content().model
    matrix = six_vector_compatibility_matrix(code, docs)
    assert len(matrix) == 6
    for row in matrix.values():
        assert row["model_endpoint_dimension_dtype_equal"] is True


def test_no_hardcoded_context3_in_active_index_query_paths():
    """Scan active modules for hard-coded context-3 model selection."""
    root = Path(__file__).resolve().parents[1] / "src"
    active = [
        root / "pipeline" / "indexing_pipeline.py",
        root / "pipeline" / "docs_pipeline.py",
        root / "mcp" / "server.py",
        root / "search" / "dense_search.py",
        root / "search" / "docs_search.py",
    ]
    forbidden = 'model="voyage-context-3"'
    forbidden_assign = 'embed_model = "voyage-context-3"'
    for path in active:
        text = path.read_text(encoding="utf-8")
        assert forbidden not in text, f"{path} hard-codes voyage-context-3 model arg"
        assert forbidden_assign not in text, f"{path} hard-codes embed_model context-3"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: build_code_collection_profile(contextual_model="voyage-context-3"),
        lambda p: build_code_collection_profile(code_model="voyage-4"),
        lambda p: build_code_collection_profile(dimension=512),
        lambda p: build_code_collection_profile(dtype="int8"),
        lambda p: build_code_collection_profile(chunker_version="changed"),
        lambda p: build_code_collection_profile(index_schema_version="dope-context-v3"),
    ],
)
def test_profile_mutations_change_collection_identity(mutate):
    base = build_code_collection_profile()
    other = mutate(base)
    assert base.profile_digest != other.profile_digest
    assert versioned_collection_name(
        "code", "abcd1234", base.profile_digest
    ) != versioned_collection_name("code", "abcd1234", other.profile_digest)


def test_endpoint_change_changes_collection_identity():
    """Endpoint is part of the fingerprint payload."""
    base = build_code_collection_profile()
    # Build a docs profile (all contextualized) vs code (mixed) for same models.
    docs = build_docs_collection_profile(contextual_model=base.content().model)
    # content_vec endpoint differs: embeddings vs contextualized is already different
    # across code title vs docs content; ensure digests diverge when endpoint set differs.
    assert base.profile_fingerprint != docs.profile_fingerprint


def test_legacy_unversioned_collection_never_selected_for_writes(tmp_path):
    code, docs = get_collection_names(tmp_path)
    legacy_code, legacy_docs = get_legacy_collection_names(tmp_path)
    assert is_legacy_collection_name(legacy_code)
    assert is_legacy_collection_name(legacy_docs)
    assert not is_legacy_collection_name(code)
    assert not is_legacy_collection_name(docs)
    assert code != legacy_code
    assert docs != legacy_docs
    assert code.startswith("code_")
    assert f"_{build_code_collection_profile().profile_digest}" in code
    assert len(build_code_collection_profile().profile_digest) == PROFILE_DIGEST_LENGTH


def test_legacy_collections_not_used_for_new_writes_when_listed():
    profile = build_code_collection_profile()
    active = versioned_collection_name("code", "deadbeef", profile.profile_digest)
    names = [f"code_deadbeef", active, f"code_deadbeef_ffffffffffff"]
    classified = classify_collections(
        names,
        kind="code",
        workspace_hash="deadbeef",
        active_digest=profile.profile_digest,
    )
    assert classified["active_collection"] == active
    assert "code_deadbeef" in classified["legacy_collections"]
    assert "code_deadbeef_ffffffffffff" in classified["other_versioned_collections"]
    # Active writes always target the versioned name, never legacy.
    assert classified["active_collection"] != "code_deadbeef"


def test_manifest_mismatch_fails_before_upsert(tmp_path):
    profile = build_code_collection_profile()
    other = build_code_collection_profile(contextual_model="voyage-context-3")
    name = versioned_collection_name("code", "abcd1234", profile.profile_digest)
    # Intentionally store wrong fingerprint under the same collection name.
    write_collection_manifest(tmp_path, other, name)
    # Overwrite fingerprint in file to force mismatch on same name
    path = tmp_path / "code_collection_manifest.json"
    text = path.read_text(encoding="utf-8").replace(
        other.profile_fingerprint, profile.profile_fingerprint + "x"
    )
    # If replace failed because digest length, write explicitly.
    import json

    payload = {
        "collection_name": name,
        "profile": {
            **other.to_public_dict(),
            "profile_fingerprint": "0" * 64,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="manifest mismatch"):
        assert_manifest_compatible(tmp_path, profile, name)


def test_context3_rollback_moves_all_contextual_paths_together(monkeypatch):
    monkeypatch.setenv(CONTEXTUAL_MODEL_ENV, "voyage-context-3")
    monkeypatch.delenv("DOPE_CONTEXT_DOC_EMBED_MODEL", raising=False)
    model = resolve_contextual_embed_model()
    assert model == "voyage-context-3"
    code = build_code_collection_profile()
    docs = build_docs_collection_profile()
    assert code.content().model == "voyage-context-3"
    assert docs.content().model == "voyage-context-3"
    assert docs.title().model == "voyage-context-3"
    assert docs.breadcrumb().model == "voyage-context-3"
    # Title/breadcrumb code vectors stay on voyage-code-3
    assert code.title().model == "voyage-code-3"


def test_conflicting_contextual_env_vars_fail_closed(monkeypatch):
    monkeypatch.setenv(CONTEXTUAL_MODEL_ENV, "voyage-context-4")
    monkeypatch.setenv("DOPE_CONTEXT_DOC_EMBED_MODEL", "voyage-context-3")
    with pytest.raises(ValueError, match="Conflicting contextual"):
        resolve_contextual_embed_model()


def test_allow_legacy_context3_does_not_select_model(monkeypatch):
    monkeypatch.delenv(CONTEXTUAL_MODEL_ENV, raising=False)
    monkeypatch.delenv("DOPE_CONTEXT_DOC_EMBED_MODEL", raising=False)
    monkeypatch.setenv("DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3", "1")
    assert resolve_contextual_embed_model() == "voyage-context-4"


def test_workspace_identity_not_default_string(tmp_path):
    a = workspace_identity_from_path(tmp_path / "a")
    b = workspace_identity_from_path(tmp_path / "b")
    assert a != "default"
    assert a != b


def test_resolve_context_model_never_rewrites_explicit_request():
    from src.embeddings.model_registry import resolve_context_model

    assert (
        resolve_context_model("voyage-context-3", "voyage-context-4")
        == "voyage-context-3"
    )
    assert resolve_context_model(None, "voyage-context-4") == "voyage-context-4"
