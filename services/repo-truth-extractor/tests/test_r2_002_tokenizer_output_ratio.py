"""TP-RTE-TRUTH-R2-002 (F-12): unified tokenizer + per-lane output-ratio
table + printed preview assumptions.

Covers extractor/costing.py's new shared estimate_tokens() /
estimate_tokens_from_char_count() / classify_model_family() /
resolve_output_ratio() / project_output_tokens(), and
lib/prescan/cost_estimator.py's CostEstimator.estimate() which is now the
one caller wired through them (replacing the prior independent chars/3.5
tokenizer + flat-15%-output + unvalidated-80%-version-chain-discount
heuristics).

DRY-RUN ONLY: nothing here makes a network or provider call. tiktoken (when
exercised) runs a local, offline encoding table only.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from extractor import costing  # noqa: E402
from lib.prescan import cost_estimator as cost_estimator_module  # noqa: E402
from lib.prescan.cost_estimator import CostEstimator  # noqa: E402
from lib.prescan.models import FileEntry, PrescanConfig  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_tokenizer_cache():
    """Every test gets a clean tiktoken-probe cache so monkeypatching one
    test's tokenizer availability can never leak into the next test."""
    costing.reset_tokenizer_cache()
    yield
    costing.reset_tokenizer_cache()


# ---------------------------------------------------------------------------
# estimate_tokens() -- text-based, dict-returning, tokenizer-labeled
# ---------------------------------------------------------------------------


def test_estimate_tokens_heuristic_for_non_openai_family() -> None:
    text = "x" * 400  # 400 chars
    result = costing.estimate_tokens(text, provider="xai", model_id="grok-4.3")
    assert result["tokenizer"] == "heuristic_chars4"
    assert result["confidence"] == "heuristic"
    # Hand arithmetic: 400 chars / HEURISTIC_CHARS_PER_TOKEN (4.0) = 100.
    assert costing.HEURISTIC_CHARS_PER_TOKEN == 4.0
    assert result["tokens"] == 100


def test_estimate_tokens_tiktoken_measured_for_openai_family() -> None:
    if costing._get_tiktoken_encoding() is None:  # noqa: SLF001
        pytest.skip("tiktoken not importable in this environment")
    text = "hello world, this is a fixture string used to cross check token counts."
    result = costing.estimate_tokens(text, provider="openai", model_id="gpt-5.5")
    assert result["tokenizer"] == "tiktoken_o200k_base"
    assert result["confidence"] == "measured"
    # Independent cross-check: encode the SAME string directly with tiktoken
    # in this test (not through costing.py) and assert the numbers agree —
    # proves estimate_tokens() is really delegating to tiktoken, not just
    # returning a heuristic guess mislabeled "measured".
    import tiktoken

    enc = tiktoken.get_encoding("o200k_base")
    assert result["tokens"] == len(enc.encode(text))
    assert result["tokens"] == 15  # pinned: recomputed by hand above too


def test_estimate_tokens_openrouter_openai_alias_is_openai_family() -> None:
    if costing._get_tiktoken_encoding() is None:  # noqa: SLF001
        pytest.skip("tiktoken not importable in this environment")
    result = costing.estimate_tokens(
        "partition context text", provider="openrouter", model_id="openai/gpt-5.3-codex"
    )
    assert result["tokenizer"] == "tiktoken_o200k_base"
    assert result["confidence"] == "measured"


def test_estimate_tokens_falls_back_to_heuristic_when_tiktoken_unavailable(monkeypatch) -> None:
    """Even for an OpenAI-family route, if tiktoken cannot be loaded the
    result must fall back to the heuristic — never raise, never silently
    report "measured" for a heuristic number."""
    monkeypatch.setattr(costing, "_get_tiktoken_encoding", lambda: None)
    text = "y" * 40
    result = costing.estimate_tokens(text, provider="openai", model_id="gpt-5.5")
    assert result["tokenizer"] == "heuristic_chars4"
    assert result["confidence"] == "heuristic"
    assert result["tokens"] == 10  # 40 / 4.0


# ---------------------------------------------------------------------------
# estimate_tokens_from_char_count() -- count-only variant (prescan's actual
# call path: it has FileEntry.size_bytes, never real file text)
# ---------------------------------------------------------------------------


def test_estimate_tokens_from_char_count_uses_shared_heuristic_constant() -> None:
    result = costing.estimate_tokens_from_char_count(800, provider="openai", model_id="gpt-5.5")
    assert result["tokenizer"] == "heuristic_chars4_count_only"
    assert result["confidence"] == "heuristic"
    # Hand arithmetic: 800 / 4.0 = 200. Even for an OpenAI-family route this
    # NEVER reaches "measured" — there is no text to tokenize, only a count.
    assert result["tokens"] == 200


def test_estimate_tokens_from_char_count_negative_input_clamps_to_zero() -> None:
    result = costing.estimate_tokens_from_char_count(-50)
    assert result["tokens"] == 0


# ---------------------------------------------------------------------------
# classify_model_family()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,model_id,expected_family",
    [
        ("openai", "gpt-5.5", "gpt"),
        ("openai", "gpt-5.4-mini", "gpt_mini"),
        ("openai", "gpt-5.3-codex", "codex"),
        ("openrouter", "openai/gpt-5.4-mini", "gpt_mini"),
        ("gemini", "gemini-3-flash-preview", "gemini"),
        ("xai", "grok-4.3", "grok"),
        ("xai", "grok-4.20-beta-0309-reasoning", "reasoning"),
        ("openai", "o1-preview", "reasoning"),
        ("openai", "o3-mini", "reasoning"),
        ("unknownvendor", "some-model", "generic"),
    ],
)
def test_classify_model_family(provider: str, model_id: str, expected_family: str) -> None:
    assert costing.classify_model_family(provider, model_id) == expected_family


def test_classify_model_family_does_not_false_positive_on_gpt_4o() -> None:
    # "gpt-4o-mini" contains the substring "4o" but is NOT an o-series
    # reasoning model; the regex must not match a bare trailing "o".
    assert costing.classify_model_family("openai", "gpt-4o-mini") != "reasoning"


# ---------------------------------------------------------------------------
# resolve_output_ratio() / project_output_tokens()
# ---------------------------------------------------------------------------


def test_resolve_output_ratio_known_lane_and_family() -> None:
    resolved = costing.resolve_output_ratio("SYNTH", "openai", "gpt-5.5")
    assert resolved["lane"] == "SYNTH"
    assert resolved["model_family"] == "gpt"
    assert resolved["output_ratio"] == costing.OUTPUT_RATIO_TABLE["SYNTH"]["gpt"]
    assert resolved["ratio_source"] == "assumed"


def test_resolve_output_ratio_unknown_lane_falls_back_to_default() -> None:
    resolved = costing.resolve_output_ratio("NOT_A_REAL_LANE", "openai", "gpt-5.5")
    assert resolved["lane"] == costing.DEFAULT_OUTPUT_LANE
    assert resolved["lane_requested"] == "NOT_A_REAL_LANE"


def test_resolve_output_ratio_unknown_family_falls_back_to_generic() -> None:
    resolved = costing.resolve_output_ratio("BULK_DOCS", "some_new_vendor", "mystery-model")
    assert resolved["model_family"] == "generic"
    assert resolved["output_ratio"] == costing.OUTPUT_RATIO_TABLE["BULK_DOCS"]["generic"]


def test_project_output_tokens_applies_table_ratio() -> None:
    projected = costing.project_output_tokens(
        10_000, lane="CE", provider="openai", model_id="gpt-5.3-codex"
    )
    ratio = costing.OUTPUT_RATIO_TABLE["CE"]["codex"]
    # Hand arithmetic: 10,000 * 0.03 = 300.
    assert ratio == 0.03
    assert projected["output_tokens"] == 300


def test_project_output_tokens_respects_min_tokens_floor() -> None:
    projected = costing.project_output_tokens(
        1, lane="CE", provider="openai", model_id="gpt-5.3-codex", min_tokens=64
    )
    assert projected["output_tokens"] == 64


# ---------------------------------------------------------------------------
# CostEstimator.estimate() end-to-end
# ---------------------------------------------------------------------------


def _prescan_config(tmp_path: Path, *, provider: str, model: str) -> PrescanConfig:
    return PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        provider=provider,
        model=model,
    )


def _fixed_pricing(monkeypatch, *, input_1m: float, output_1m: float) -> None:
    """Isolate CostEstimator's OWN token/ratio math (the subject of this
    packet) from config/pricing.yaml's real, evolving catalog contents."""

    def _fake_get_pricing_rate(provider: str, model_id: str):
        return {
            "input_1m": input_1m,
            "output_1m": output_1m,
            "source": "test_fixture",
            "pricing_key": f"{provider}/{model_id}",
            "unpriced": False,
        }

    monkeypatch.setattr(cost_estimator_module, "_get_pricing_rate", _fake_get_pricing_rate)


def test_cost_estimator_hand_computed_dollar_total(tmp_path: Path, monkeypatch) -> None:
    """Independently hand-recomputed estimate (no tiktoken variability:
    provider=xai routes through the heuristic chars/4 path everywhere)."""
    _fixed_pricing(monkeypatch, input_1m=10.0, output_1m=20.0)
    cfg = _prescan_config(tmp_path, provider="xai", model="grok-4.3")
    estimator = CostEstimator(cfg)

    # One included file, 4000 bytes, no duplicates, no version-chain members.
    entries = [
        FileEntry(rel_path="a.py", size_bytes=4000, extension=".py", include=True),
    ]
    result = estimator.estimate(entries)

    # --- Hand arithmetic ---
    # gross tokens = 4000 / 4.0 (HEURISTIC_CHARS_PER_TOKEN)      = 1000
    # dup tokens    = 0                                          = 0
    # net input     = 1000 - 0                                   = 1000
    # lane=BULK_DOCS (CostEstimator's DEFAULT_OUTPUT_LANE), family="grok"
    #   -> ratio = OUTPUT_RATIO_TABLE["BULK_DOCS"]["grok"] = 0.10
    # output tokens = max(1, int(1000 * 0.10))                   = 100
    # input_cost  = (1000 / 1_000_000) * 10.0 = 0.01
    # output_cost = ( 100 / 1_000_000) * 20.0 = 0.002
    # total       = 0.012
    assert costing.OUTPUT_RATIO_TABLE["BULK_DOCS"]["grok"] == 0.10
    assert result["net_estimates"]["input_tokens"] == 1000
    assert result["net_estimates"]["output_tokens"] == 100
    assert result["net_estimates"]["total_cost_usd"] == pytest.approx(0.012, abs=1e-9)


def test_cost_estimator_excludes_measured_duplicates(tmp_path: Path, monkeypatch) -> None:
    _fixed_pricing(monkeypatch, input_1m=1.0, output_1m=1.0)
    cfg = _prescan_config(tmp_path, provider="xai", model="grok-4.3")
    estimator = CostEstimator(cfg)
    entries = [
        FileEntry(rel_path="a.py", size_bytes=4000, extension=".py", include=True),
        FileEntry(
            rel_path="a_copy.py",
            size_bytes=4000,
            extension=".py",
            include=True,
            is_duplicate=True,
        ),
    ]
    result = estimator.estimate(entries)
    # gross = 8000/4 = 2000; dup = 4000/4 = 1000; net = 2000 - 1000 = 1000.
    assert result["corpus_stats"]["total_tokens_gross"] == 2000
    assert result["estimated_savings"]["duplicate_tokens"] == 1000
    assert result["net_estimates"]["input_tokens"] == 1000


def test_cost_estimator_does_not_discount_version_chain_members(tmp_path: Path, monkeypatch) -> None:
    """F-12/A2-5: version-chain members must be priced at FULL weight; the
    old code silently subtracted an unvalidated 80% from them. The byte
    count is still reported, but unpriced/not subtracted."""
    _fixed_pricing(monkeypatch, input_1m=1.0, output_1m=1.0)
    cfg = _prescan_config(tmp_path, provider="xai", model="grok-4.3")
    estimator = CostEstimator(cfg)
    entries = [
        FileEntry(
            rel_path="v1.py",
            size_bytes=4000,
            extension=".py",
            include=True,
            version_chain_id="chain-1",
            is_latest_version=False,
        ),
    ]
    result = estimator.estimate(entries)
    # gross = 4000/4 = 1000, NOT discounted by 80% -> net input == gross.
    assert result["net_estimates"]["input_tokens"] == 1000
    assert result["estimated_savings"]["version_chain_tokens"] == 0
    assert result["estimated_savings"]["version_chain_bytes_unmodeled"] == 4000


def test_cost_estimator_assumptions_block_prints_tokenizer_and_ratio(
    tmp_path: Path, monkeypatch
) -> None:
    _fixed_pricing(monkeypatch, input_1m=1.0, output_1m=1.0)
    cfg = _prescan_config(tmp_path, provider="xai", model="grok-4.3")
    estimator = CostEstimator(cfg)
    entries = [FileEntry(rel_path="a.py", size_bytes=400, extension=".py", include=True)]
    result = estimator.estimate(entries)

    assumptions = result["assumptions"]
    assert assumptions["tokenizer"] == "heuristic_chars4_count_only"
    assert assumptions["tokenizer_confidence"] == "heuristic"
    assert assumptions["chars_per_token_heuristic"] == 4.0
    assert assumptions["output_ratio_lane"] == "BULK_DOCS"
    assert assumptions["output_ratio_model_family"] == "grok"
    assert assumptions["output_ratio"] == 0.10
    assert assumptions["output_ratio_source"] == "assumed"
