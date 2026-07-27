"""Canonical Voyage model configuration for dope-context.

The registry keeps embedding dimensions, request limits, pricing, and migration
aliases in one place. Collection/index code should persist an index fingerprint
derived from these settings so incompatible model changes cannot be silently
mixed in the same Qdrant collection.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional


@dataclass(frozen=True)
class EmbeddingModelSpec:
    """Static capabilities required by dope-context."""

    name: str
    endpoint: str
    default_dimension: int
    supported_dimensions: FrozenSet[int]
    per_input_tokens: int
    max_request_inputs: int
    max_request_tokens: int
    price_per_million_tokens: float
    legacy: bool = False


_DIMENSIONS = frozenset({256, 512, 1024, 2048})

MODEL_SPECS: Dict[str, EmbeddingModelSpec] = {
    "voyage-code-3": EmbeddingModelSpec(
        name="voyage-code-3",
        endpoint="embeddings",
        default_dimension=1024,
        supported_dimensions=_DIMENSIONS,
        per_input_tokens=32_000,
        max_request_inputs=1_000,
        max_request_tokens=120_000,
        price_per_million_tokens=0.18,
    ),
    "voyage-4-large": EmbeddingModelSpec(
        name="voyage-4-large",
        endpoint="embeddings",
        default_dimension=1024,
        supported_dimensions=_DIMENSIONS,
        per_input_tokens=32_000,
        max_request_inputs=1_000,
        max_request_tokens=120_000,
        price_per_million_tokens=0.12,
    ),
    "voyage-4": EmbeddingModelSpec(
        name="voyage-4",
        endpoint="embeddings",
        default_dimension=1024,
        supported_dimensions=_DIMENSIONS,
        per_input_tokens=32_000,
        max_request_inputs=1_000,
        max_request_tokens=320_000,
        price_per_million_tokens=0.06,
    ),
    "voyage-4-lite": EmbeddingModelSpec(
        name="voyage-4-lite",
        endpoint="embeddings",
        default_dimension=1024,
        supported_dimensions=_DIMENSIONS,
        per_input_tokens=32_000,
        max_request_inputs=1_000,
        max_request_tokens=1_000_000,
        price_per_million_tokens=0.02,
    ),
    "voyage-context-4": EmbeddingModelSpec(
        name="voyage-context-4",
        endpoint="contextualized_embeddings",
        default_dimension=1024,
        supported_dimensions=_DIMENSIONS,
        per_input_tokens=32_000,
        max_request_inputs=1_000,
        max_request_tokens=120_000,
        price_per_million_tokens=0.12,
    ),
    "voyage-context-3": EmbeddingModelSpec(
        name="voyage-context-3",
        endpoint="contextualized_embeddings",
        default_dimension=1024,
        supported_dimensions=_DIMENSIONS,
        per_input_tokens=32_000,
        max_request_inputs=1_000,
        max_request_tokens=120_000,
        price_per_million_tokens=0.18,
        legacy=True,
    ),
    # voyage-3-lite is in the vendor 120K request-token group; only
    # voyage-4-lite (and voyage-3.5-lite if added later) carry the 1M ceiling.
    "voyage-3-lite": EmbeddingModelSpec(
        name="voyage-3-lite",
        endpoint="embeddings",
        default_dimension=512,
        supported_dimensions=frozenset({512}),
        per_input_tokens=32_000,
        max_request_inputs=1_000,
        max_request_tokens=120_000,
        price_per_million_tokens=0.02,
        legacy=True,
    ),
}

DEFAULT_CODE_MODEL = "voyage-code-3"
DEFAULT_DOC_MODEL = "voyage-context-4"
DEFAULT_GENERAL_MODEL = "voyage-4"
DEFAULT_RERANK_MODEL = "rerank-2.5"
DEFAULT_OUTPUT_DIMENSION = 1024
DEFAULT_OUTPUT_DTYPE = "float"
INDEX_SCHEMA_VERSION = "dope-context-v2"


def env_model(name: str, default: str) -> str:
    """Read a model override without accepting an empty value."""

    return os.getenv(name, default).strip() or default


def get_model_spec(model: str, *, endpoint: Optional[str] = None) -> EmbeddingModelSpec:
    """Return a known model or fail closed on unsupported configuration."""

    try:
        spec = MODEL_SPECS[model]
    except KeyError as exc:
        supported = ", ".join(sorted(MODEL_SPECS))
        raise ValueError(
            f"Unsupported Voyage model '{model}'. Supported models: {supported}"
        ) from exc

    if endpoint and spec.endpoint != endpoint:
        raise ValueError(
            f"Voyage model '{model}' uses endpoint '{spec.endpoint}', not '{endpoint}'"
        )
    return spec


def validate_dimension(model: str, output_dimension: Optional[int]) -> int:
    """Resolve and validate an embedding dimension."""

    spec = get_model_spec(model)
    dimension = output_dimension or spec.default_dimension
    if dimension not in spec.supported_dimensions:
        supported = ", ".join(str(value) for value in sorted(spec.supported_dimensions))
        raise ValueError(
            f"Model '{model}' does not support {dimension} dimensions; "
            f"supported dimensions: {supported}"
        )
    return dimension


def resolve_context_model(requested: Optional[str], configured: str) -> str:
    """Return the requested model or the configured default.

    Explicit model requests are never rewritten. Contextual rollback is done
    only via ``DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL`` (see ``index_profile``).
    ``DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3`` is a deprecated no-op for selection.
    """

    if requested in (None, ""):
        return configured
    return requested


def resolve_contextual_embed_model_from_env() -> str:
    """Canonical contextual model selector (index + query).

    Delegates to ``index_profile.resolve_contextual_embed_model`` so callers
    that still import from the registry share one implementation.
    """

    # Local import avoids a circular dependency at module load time.
    from ..index_profile import resolve_contextual_embed_model

    return resolve_contextual_embed_model()


def index_fingerprint(
    *,
    model: str,
    output_dimension: int,
    output_dtype: str,
    chunker_version: str,
) -> str:
    """Return a deterministic identifier for single-model index checks.

    Multi-vector collections should prefer ``CollectionProfile.profile_fingerprint``
    from ``index_profile``; this helper remains for docs payload provenance.
    """

    payload = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "model": model,
        "output_dimension": output_dimension,
        "output_dtype": output_dtype,
        "chunker_version": chunker_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
