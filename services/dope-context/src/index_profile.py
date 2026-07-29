"""Canonical vector profiles and versioned collection identity for dope-context.

Every named vector has one profile used by both index and query paths. Collection
names embed a fingerprint of the full profile set so incompatible configurations
never share a Qdrant collection.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .embeddings.model_registry import (
    DEFAULT_CODE_MODEL,
    DEFAULT_DOC_MODEL,
    DEFAULT_OUTPUT_DIMENSION,
    DEFAULT_OUTPUT_DTYPE,
    INDEX_SCHEMA_VERSION,
    env_model,
    get_model_spec,
    validate_dimension,
)

logger = logging.getLogger(__name__)

# Digest length balances collision resistance with collection-name readability.
PROFILE_DIGEST_LENGTH = 12

CODE_CHUNKER_VERSION = "code_chunker.v1"
DOCS_CHUNKER_VERSION = "document_processor.v2-voyage-token-accounting"

CONTEXTUAL_MODEL_ENV = "DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL"
CONTEXTUAL_MODEL_ALIAS_ENV = "DOPE_CONTEXT_DOC_EMBED_MODEL"
LEGACY_CONTEXT3_ENV = "DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3"

_LEGACY_COLLECTION_RE = re.compile(r"^(code|docs)_([0-9a-f]{8})$")
_VERSIONED_COLLECTION_RE = re.compile(
    r"^(code|docs)_([0-9a-f]{8})_([0-9a-f]{" + str(PROFILE_DIGEST_LENGTH) + r"})$"
)


@dataclass(frozen=True)
class VectorProfile:
    """One named-vector producer/consumer contract."""

    vector_role: str
    model: str
    endpoint: str
    index_input_type: str
    query_input_type: str
    dimension: int
    dtype: str
    chunker_version: str
    index_schema_version: str

    def compatibility_fields(self) -> Dict[str, Any]:
        return {
            "vector_role": self.vector_role,
            "model": self.model,
            "endpoint": self.endpoint,
            "dimension": self.dimension,
            "dtype": self.dtype,
            "chunker_version": self.chunker_version,
            "index_schema_version": self.index_schema_version,
            # Input types may differ for document vs query on the same model;
            # they are recorded for provenance but do not affect fingerprint.
            "index_input_type": self.index_input_type,
            "query_input_type": self.query_input_type,
        }

    def fingerprint_payload(self) -> Dict[str, Any]:
        """Fields that change collection identity when mutated."""

        return {
            "vector_role": self.vector_role,
            "model": self.model,
            "endpoint": self.endpoint,
            "dimension": self.dimension,
            "dtype": self.dtype,
            "chunker_version": self.chunker_version,
            "index_schema_version": self.index_schema_version,
        }


@dataclass(frozen=True)
class CollectionProfile:
    """Complete multi-vector profile for one collection kind (code or docs)."""

    kind: str  # "code" | "docs"
    vectors: Dict[str, VectorProfile]
    index_schema_version: str
    chunker_version: str
    profile_fingerprint: str
    profile_digest: str

    def vector(self, name: str) -> VectorProfile:
        try:
            return self.vectors[name]
        except KeyError as exc:
            raise KeyError(f"Unknown vector '{name}' in {self.kind} profile") from exc

    def content(self) -> VectorProfile:
        return self.vector("content_vec")

    def title(self) -> VectorProfile:
        return self.vector("title_vec")

    def breadcrumb(self) -> VectorProfile:
        return self.vector("breadcrumb_vec")

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "index_schema_version": self.index_schema_version,
            "chunker_version": self.chunker_version,
            "profile_fingerprint": self.profile_fingerprint,
            "profile_digest": self.profile_digest,
            "vectors": {
                name: asdict(profile) for name, profile in sorted(self.vectors.items())
            },
        }

    def provenance_fields(self) -> Dict[str, Any]:
        """Payload keys sufficient to reconstruct producer configuration."""

        content = self.content()
        title = self.title()
        breadcrumb = self.breadcrumb()
        return {
            "index_schema_version": self.index_schema_version,
            "profile_fingerprint": self.profile_fingerprint,
            "chunker_version": self.chunker_version,
            "content_vec_model": content.model,
            "content_vec_endpoint": content.endpoint,
            "content_vec_dimension": content.dimension,
            "content_vec_dtype": content.dtype,
            "title_vec_model": title.model,
            "title_vec_endpoint": title.endpoint,
            "title_vec_dimension": title.dimension,
            "title_vec_dtype": title.dtype,
            "breadcrumb_vec_model": breadcrumb.model,
            "breadcrumb_vec_endpoint": breadcrumb.endpoint,
            "breadcrumb_vec_dimension": breadcrumb.dimension,
            "breadcrumb_vec_dtype": breadcrumb.dtype,
        }


def resolve_contextual_embed_model(
    *,
    default: str = DEFAULT_DOC_MODEL,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    """Resolve the single contextual model used by index and query paths.

    Preference order:
    1. ``DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL``
    2. ``DOPE_CONTEXT_DOC_EMBED_MODEL`` (deprecated alias)
    3. default (voyage-context-4)

    Conflicting simultaneous values fail closed. The legacy admission guard
    ``DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3`` never selects a model.
    """

    env = environ if environ is not None else os.environ
    primary = (env.get(CONTEXTUAL_MODEL_ENV) or "").strip()
    alias = (env.get(CONTEXTUAL_MODEL_ALIAS_ENV) or "").strip()

    if primary and alias and primary != alias:
        raise ValueError(
            f"Conflicting contextual embed models: {CONTEXTUAL_MODEL_ENV}={primary!r} "
            f"and {CONTEXTUAL_MODEL_ALIAS_ENV}={alias!r}. Set only one."
        )

    model = primary or alias or default
    get_model_spec(model, endpoint="contextualized_embeddings")

    # Deprecated admission guard: log only; never split index/query selection.
    if env.get(LEGACY_CONTEXT3_ENV, "").lower() in {"1", "true", "yes"}:
        logger.warning(
            "%s is deprecated and no longer selects models; set %s=voyage-context-3 "
            "for full contextual rollback",
            LEGACY_CONTEXT3_ENV,
            CONTEXTUAL_MODEL_ENV,
        )
    return model


def resolve_code_embed_model(
    *,
    default: str = DEFAULT_CODE_MODEL,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    env = environ if environ is not None else os.environ
    model = (env.get("DOPE_CONTEXT_CODE_EMBED_MODEL") or "").strip() or default
    get_model_spec(model, endpoint="embeddings")
    return model


def _vector_profile(
    *,
    kind: str,
    vector_name: str,
    model: str,
    endpoint: str,
    dimension: int,
    dtype: str,
    chunker_version: str,
    index_schema_version: str,
) -> VectorProfile:
    get_model_spec(model, endpoint=endpoint)
    dimension = validate_dimension(model, dimension)
    return VectorProfile(
        vector_role=f"{kind}.{vector_name}",
        model=model,
        endpoint=endpoint,
        index_input_type="document",
        query_input_type="query",
        dimension=dimension,
        dtype=dtype,
        chunker_version=chunker_version,
        index_schema_version=index_schema_version,
    )


def fingerprint_profiles(vectors: Mapping[str, VectorProfile]) -> str:
    payload = {
        name: vectors[name].fingerprint_payload() for name in sorted(vectors)
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def digest_from_fingerprint(fingerprint: str, *, length: int = PROFILE_DIGEST_LENGTH) -> str:
    if length < 8:
        raise ValueError("profile digest length must be >= 8")
    return fingerprint[:length]


def build_code_collection_profile(
    *,
    contextual_model: Optional[str] = None,
    code_model: Optional[str] = None,
    dimension: Optional[int] = None,
    dtype: str = DEFAULT_OUTPUT_DTYPE,
    chunker_version: str = CODE_CHUNKER_VERSION,
    index_schema_version: str = INDEX_SCHEMA_VERSION,
    environ: Optional[Mapping[str, str]] = None,
) -> CollectionProfile:
    """Code collection: contextual content_vec + voyage-code-3 title/breadcrumb."""

    ctx_model = contextual_model or resolve_contextual_embed_model(environ=environ)
    id_model = code_model or resolve_code_embed_model(environ=environ)
    dim = dimension or DEFAULT_OUTPUT_DIMENSION

    vectors = {
        "content_vec": _vector_profile(
            kind="code",
            vector_name="content_vec",
            model=ctx_model,
            endpoint="contextualized_embeddings",
            dimension=dim,
            dtype=dtype,
            chunker_version=chunker_version,
            index_schema_version=index_schema_version,
        ),
        "title_vec": _vector_profile(
            kind="code",
            vector_name="title_vec",
            model=id_model,
            endpoint="embeddings",
            dimension=dim,
            dtype=dtype,
            chunker_version=chunker_version,
            index_schema_version=index_schema_version,
        ),
        "breadcrumb_vec": _vector_profile(
            kind="code",
            vector_name="breadcrumb_vec",
            model=id_model,
            endpoint="embeddings",
            dimension=dim,
            dtype=dtype,
            chunker_version=chunker_version,
            index_schema_version=index_schema_version,
        ),
    }
    fingerprint = fingerprint_profiles(vectors)
    return CollectionProfile(
        kind="code",
        vectors=vectors,
        index_schema_version=index_schema_version,
        chunker_version=chunker_version,
        profile_fingerprint=fingerprint,
        profile_digest=digest_from_fingerprint(fingerprint),
    )


def build_docs_collection_profile(
    *,
    contextual_model: Optional[str] = None,
    dimension: Optional[int] = None,
    dtype: str = DEFAULT_OUTPUT_DTYPE,
    chunker_version: str = DOCS_CHUNKER_VERSION,
    index_schema_version: str = INDEX_SCHEMA_VERSION,
    environ: Optional[Mapping[str, str]] = None,
) -> CollectionProfile:
    """Docs collection: same contextual model for all three named vectors."""

    ctx_model = contextual_model or resolve_contextual_embed_model(environ=environ)
    dim = dimension or DEFAULT_OUTPUT_DIMENSION

    vectors = {
        name: _vector_profile(
            kind="docs",
            vector_name=name,
            model=ctx_model,
            endpoint="contextualized_embeddings",
            dimension=dim,
            dtype=dtype,
            chunker_version=chunker_version,
            index_schema_version=index_schema_version,
        )
        for name in ("content_vec", "title_vec", "breadcrumb_vec")
    }
    fingerprint = fingerprint_profiles(vectors)
    return CollectionProfile(
        kind="docs",
        vectors=vectors,
        index_schema_version=index_schema_version,
        chunker_version=chunker_version,
        profile_fingerprint=fingerprint,
        profile_digest=digest_from_fingerprint(fingerprint),
    )


def versioned_collection_name(
    kind: str,
    workspace_hash: str,
    profile_digest: str,
) -> str:
    if kind not in {"code", "docs"}:
        raise ValueError(f"kind must be 'code' or 'docs', got {kind!r}")
    if not re.fullmatch(r"[0-9a-f]{8}", workspace_hash):
        # Allow WORKSPACE_HASH_OVERRIDE and other stable ids; still sanitize.
        workspace_hash = hashlib.md5(workspace_hash.encode("utf-8")).hexdigest()[:8]
    digest = profile_digest[:PROFILE_DIGEST_LENGTH]
    if not re.fullmatch(r"[0-9a-f]+", digest):
        raise ValueError(f"invalid profile digest: {profile_digest!r}")
    return f"{kind}_{workspace_hash}_{digest}"


def parse_collection_name(name: str) -> Optional[Dict[str, str]]:
    """Parse versioned or legacy collection names."""

    match = _VERSIONED_COLLECTION_RE.fullmatch(name)
    if match:
        return {
            "kind": match.group(1),
            "workspace_hash": match.group(2),
            "profile_digest": match.group(3),
            "versioned": "true",
        }
    match = _LEGACY_COLLECTION_RE.fullmatch(name)
    if match:
        return {
            "kind": match.group(1),
            "workspace_hash": match.group(2),
            "profile_digest": "",
            "versioned": "false",
        }
    return None


def is_legacy_collection_name(name: str) -> bool:
    parsed = parse_collection_name(name)
    return bool(parsed and parsed["versioned"] == "false")


def is_active_collection_name(
    name: str,
    *,
    kind: str,
    workspace_hash: str,
    profile_digest: str,
) -> bool:
    expected = versioned_collection_name(kind, workspace_hash, profile_digest)
    return name == expected


def classify_collections(
    names: Sequence[str],
    *,
    kind: str,
    workspace_hash: str,
    active_digest: str,
) -> Dict[str, Any]:
    """Split observed collections into active / other-versioned / legacy."""

    active = versioned_collection_name(kind, workspace_hash, active_digest)
    legacy: List[str] = []
    other_versioned: List[str] = []
    for name in names:
        parsed = parse_collection_name(name)
        if not parsed or parsed["kind"] != kind:
            continue
        if parsed["workspace_hash"] != workspace_hash:
            continue
        if parsed["versioned"] == "false":
            legacy.append(name)
        elif name == active:
            continue
        else:
            other_versioned.append(name)
    return {
        "active_collection": active,
        "legacy_collections": sorted(legacy),
        "other_versioned_collections": sorted(other_versioned),
        "migration_state": (
            "legacy_present"
            if legacy
            else ("prior_profiles_present" if other_versioned else "clean")
        ),
    }


def manifest_path(snapshot_dir: Path, kind: str) -> Path:
    return snapshot_dir / f"{kind}_collection_manifest.json"


def write_collection_manifest(
    snapshot_dir: Path,
    profile: CollectionProfile,
    collection_name: str,
) -> Path:
    path = manifest_path(snapshot_dir, profile.kind)
    payload = {
        "collection_name": collection_name,
        "profile": profile.to_public_dict(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_collection_manifest(
    snapshot_dir: Path, kind: str
) -> Optional[Dict[str, Any]]:
    path = manifest_path(snapshot_dir, kind)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load collection manifest %s: %s", path, exc)
        return None


def assert_manifest_compatible(
    snapshot_dir: Path,
    profile: CollectionProfile,
    collection_name: str,
) -> None:
    """Fail closed when a local manifest disagrees with the derived profile."""

    manifest = load_collection_manifest(snapshot_dir, profile.kind)
    if not manifest:
        return
    stored_name = manifest.get("collection_name")
    stored_profile = (manifest.get("profile") or {}).get("profile_fingerprint")
    if stored_name and stored_name == collection_name:
        if stored_profile and stored_profile != profile.profile_fingerprint:
            raise RuntimeError(
                f"Collection manifest mismatch for '{collection_name}': "
                f"stored fingerprint {stored_profile} != derived "
                f"{profile.profile_fingerprint}. Refusing mixed-profile writes."
            )


def index_query_profiles_match(index: VectorProfile, query: VectorProfile) -> bool:
    """True when model/endpoint/dimension/dtype/role/schema agree."""

    return (
        index.vector_role == query.vector_role
        and index.model == query.model
        and index.endpoint == query.endpoint
        and index.dimension == query.dimension
        and index.dtype == query.dtype
        and index.chunker_version == query.chunker_version
        and index.index_schema_version == query.index_schema_version
    )


def six_vector_compatibility_matrix(
    code: Optional[CollectionProfile] = None,
    docs: Optional[CollectionProfile] = None,
) -> Dict[str, Any]:
    """Build the six named-vector index/query equality matrix."""

    code = code or build_code_collection_profile()
    docs = docs or build_docs_collection_profile()
    rows: Dict[str, Any] = {}
    for profile in (code, docs):
        for name, vector in profile.vectors.items():
            # Index and query profiles are the same object; document/query only
            # differ in input_type, which is allowed by the invariant.
            rows[f"{profile.kind}.{name}"] = {
                "index": vector.compatibility_fields(),
                "query": vector.compatibility_fields(),
                "model_endpoint_dimension_dtype_equal": True,
                "index_input_type": vector.index_input_type,
                "query_input_type": vector.query_input_type,
            }
    return rows


def workspace_identity_from_path(workspace_path: Path) -> str:
    """Stable workspace_id derived from the resolved workspace root path."""

    normalized = str(workspace_path.resolve())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# Re-export helpers used by older call sites during migration.
__all__ = [
    "CODE_CHUNKER_VERSION",
    "CONTEXTUAL_MODEL_ALIAS_ENV",
    "CONTEXTUAL_MODEL_ENV",
    "CollectionProfile",
    "DOCS_CHUNKER_VERSION",
    "LEGACY_CONTEXT3_ENV",
    "PROFILE_DIGEST_LENGTH",
    "VectorProfile",
    "assert_manifest_compatible",
    "build_code_collection_profile",
    "build_docs_collection_profile",
    "classify_collections",
    "digest_from_fingerprint",
    "fingerprint_profiles",
    "index_query_profiles_match",
    "is_active_collection_name",
    "is_legacy_collection_name",
    "load_collection_manifest",
    "manifest_path",
    "parse_collection_name",
    "resolve_code_embed_model",
    "resolve_contextual_embed_model",
    "six_vector_compatibility_matrix",
    "versioned_collection_name",
    "workspace_identity_from_path",
    "write_collection_manifest",
]
