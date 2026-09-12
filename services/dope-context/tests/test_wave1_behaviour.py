"""Wave 1b (BEHAVIOUR) driving tests -- ADR-226 Amendment A5a.

TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007. Covers exactly the scope the operator
approved under A5a: the tokenizer cache bound (E10), the previously-dead
budget_starvation / degraded_guarantee_applied flags (E2/E4), and the
token_count preference over the byte/lexical heuristic (E17). Wave 1a
(R-5, E1, E16, C1, C6, C13, registry additions) and Wave 1c/A5b
(contextualized_embedder.py, voyage_reranker.py retry parity) are explicitly
out of scope for this packet slice -- see the packet's Status section.

Also pins the fingerprint invariant that makes Wave 1 reviewable on its diff
alone: no member of VectorProfile.fingerprint_payload() may change as a
side effect of anything in this wave.
"""

from __future__ import annotations

import pytest

from src.index_profile import build_code_collection_profile, build_docs_collection_profile
from src.utils.model_tokenizer import VoyageTokenCounter
from src.utils.token_budget import BASE_OVERHEAD_TOKENS, truncate_docs_results

# Pinned against origin/main before this wave's changes (environ={} forces
# the default model regardless of the host's actual env vars, so this is
# reproducible anywhere). A change to either value means something in this
# diff moved fingerprint_payload() -- Wave 1's defining constraint.
_EXPECTED_CODE_PROFILE_DIGEST = "a78e8e6bf0aa"
_EXPECTED_DOCS_PROFILE_DIGEST = "bc3e80ff1a1b"


def test_fingerprint_payload_unchanged_by_wave1():
    code = build_code_collection_profile(environ={})
    docs = build_docs_collection_profile(environ={})
    assert code.profile_digest == _EXPECTED_CODE_PROFILE_DIGEST
    assert docs.profile_digest == _EXPECTED_DOCS_PROFILE_DIGEST


# ---------------------------------------------------------------------------
# E10: VoyageTokenCounter._cache must be bounded, not grow for the process
# lifetime. Mirrors voyage_embedder.py's _cache_response bound; no TTL/expiry
# concept applies here (unlike that embedding-response cache) because a
# (model, text-sha256) -> TokenCount mapping is a pure function of its key --
# nothing about it ever becomes stale, so oldest-first eviction on its own is
# the correct, complete mirror of the pattern for this cache's shape.
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_tokenizer_cache_evicts_oldest_first_when_bound_reached():
    counter = VoyageTokenCounter(max_cache_entries=3)
    texts = ["alpha text one", "beta text two", "gamma text three", "delta text four"]

    for text in texts:
        await counter.count_each([text], model="voyage-code-3")

    assert len(counter._cache) == 3
    first_key = VoyageTokenCounter._key(texts[0], "voyage-code-3")
    assert first_key not in counter._cache
    for text in texts[1:]:
        assert VoyageTokenCounter._key(text, "voyage-code-3") in counter._cache


@pytest.mark.anyio
async def test_tokenizer_cache_hit_does_not_evict():
    counter = VoyageTokenCounter(max_cache_entries=2)
    await counter.count_each(["one"], model="voyage-code-3")
    await counter.count_each(["two"], model="voyage-code-3")
    # Re-request an already-cached text: must be a cache hit, not a third
    # insert that would evict "one" under a naive unconditional-insert bound.
    await counter.count_each(["one"], model="voyage-code-3")
    assert len(counter._cache) == 2
    assert VoyageTokenCounter._key("one", "voyage-code-3") in counter._cache
    assert VoyageTokenCounter._key("two", "voyage-code-3") in counter._cache


# ---------------------------------------------------------------------------
# E2/E4: budget_starvation and degraded_guarantee_applied were declared and
# never assigned. Both must be True exactly on the path where real matches
# existed but nothing fit the budget normally (the forced single-result
# degrade), and False on an ordinary truncation.
# ---------------------------------------------------------------------------


def _doc_result(text: str, **extra):
    return {"source_path": "docs/x.md", "text": text, "score": 1.0, **extra}


def test_budget_starvation_flags_set_on_forced_degrade():
    # A budget one token above the floor cannot fit even the smallest normal
    # item once BASE_OVERHEAD_TOKENS is subtracted, forcing the degrade path.
    results = [_doc_result("some real content that would normally fit fine")]
    _, trunc_info = truncate_docs_results(
        results, budget_tokens=BASE_OVERHEAD_TOKENS + 1, per_item_max_chars=2000
    )
    assert trunc_info.budget_starvation is True
    assert trunc_info.degraded_guarantee_applied is True


def test_budget_starvation_flags_false_on_ordinary_truncation():
    results = [_doc_result("short")]
    _, trunc_info = truncate_docs_results(
        results, budget_tokens=9_000, per_item_max_chars=2000
    )
    assert trunc_info.budget_starvation is False
    assert trunc_info.degraded_guarantee_applied is False


def test_budget_starvation_flags_false_on_empty_input():
    _, trunc_info = truncate_docs_results([], budget_tokens=9_000, per_item_max_chars=2000)
    assert trunc_info.budget_starvation is False
    assert trunc_info.degraded_guarantee_applied is False


# ---------------------------------------------------------------------------
# E17: a docs item carrying a real Voyage-reported token_count must be
# trusted over the byte/lexical heuristic when deciding whether its content
# needs truncating at all.
# ---------------------------------------------------------------------------


def test_token_count_preference_skips_unnecessary_truncation():
    # The heuristic alone would estimate this text at well over the small
    # per-item budget below and truncate it -- but its real token_count
    # says it comfortably fits.
    long_text = "word " * 200
    with_count = [_doc_result(long_text, token_count=5)]
    without_count = [_doc_result(long_text)]

    truncated_with, _ = truncate_docs_results(
        with_count, budget_tokens=9_000, per_item_max_chars=50
    )
    truncated_without, _ = truncate_docs_results(
        without_count, budget_tokens=9_000, per_item_max_chars=50
    )

    assert truncated_with[0]["text_truncated"] is False
    assert truncated_with[0]["text"] == long_text
    assert truncated_without[0]["text_truncated"] is True
    assert truncated_without[0]["text"] != long_text


def test_token_count_never_reaches_the_returned_item():
    results = [_doc_result("hello", token_count=5)]
    truncated, _ = truncate_docs_results(
        results, budget_tokens=9_000, per_item_max_chars=50
    )
    assert "token_count" not in truncated[0]


def test_token_count_stripped_on_the_degraded_path_too():
    results = [_doc_result("hello", token_count=5)]
    truncated, _ = truncate_docs_results(
        results, budget_tokens=BASE_OVERHEAD_TOKENS + 1, per_item_max_chars=50
    )
    assert "token_count" not in truncated[0]
