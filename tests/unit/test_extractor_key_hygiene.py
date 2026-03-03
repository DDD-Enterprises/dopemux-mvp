"""Unit tests for key hygiene preflight — TP-ENV-KEY-HYGIENE-PREFLIGHT-0003.

Network-free. Does not read real API keys from the environment.
Uses monkeypatch to control env vars precisely.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RUNNER_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "repo-truth-extractor"
    / "run_extraction_v3.py"
)
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

DEFAULT_POLICY = runner.DEFAULT_ROUTING_POLICY


# ──────────────────────────────────────────────────────────────────────────────
# _safe_key_fingerprint
# ──────────────────────────────────────────────────────────────────────────────

def test_fingerprint_is_8_hex_chars():
    fp = runner._safe_key_fingerprint("some-secret-key")
    assert len(fp) == 8
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_is_stable():
    assert runner._safe_key_fingerprint("abc") == runner._safe_key_fingerprint("abc")


def test_fingerprint_differs_for_different_values():
    assert runner._safe_key_fingerprint("key-a") != runner._safe_key_fingerprint("key-b")


def test_fingerprint_does_not_contain_secret():
    secret = "super-secret-value-12345"
    fp = runner._safe_key_fingerprint(secret)
    assert secret not in fp
    assert "super" not in fp


# ──────────────────────────────────────────────────────────────────────────────
# _collect_required_key_envs
# ──────────────────────────────────────────────────────────────────────────────

def test_collect_returns_all_providers():
    envs = runner._collect_required_key_envs(DEFAULT_POLICY)
    assert isinstance(envs, dict)
    # Must have entries for each provider present in the active ladders
    for provider_set in envs.values():
        assert isinstance(provider_set, set)
        for env_name in provider_set:
            assert isinstance(env_name, str)
            assert env_name  # non-empty


def test_collect_includes_gemini_key_env():
    envs = runner._collect_required_key_envs(DEFAULT_POLICY)
    assert "gemini" in envs
    assert "GEMINI_API_KEY" in envs["gemini"]


def test_collect_includes_xai_key_env():
    envs = runner._collect_required_key_envs(DEFAULT_POLICY)
    assert "xai" in envs
    assert "XAI_API_KEY" in envs["xai"]


def test_collect_includes_openai_key_env():
    envs = runner._collect_required_key_envs(DEFAULT_POLICY)
    assert "openai" in envs
    assert "OPENAI_API_KEY" in envs["openai"]


# ──────────────────────────────────────────────────────────────────────────────
# preflight_keys: missing key → error exit 3
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_gemini_key_raises_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report = runner.preflight_keys(DEFAULT_POLICY, strict=False)
    assert report["overall_status"] == "FAIL"
    assert report["exit_code"] == 3
    assert any("GEMINI_API_KEY" in e for e in report["errors"])


def test_missing_openai_key_raises_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = runner.preflight_keys(DEFAULT_POLICY, strict=False)
    assert report["overall_status"] == "FAIL"
    assert report["exit_code"] == 3
    assert any("OPENAI_API_KEY" in e for e in report["errors"])


# ──────────────────────────────────────────────────────────────────────────────
# preflight_keys: prefix mismatch → warning exit 2 (non-strict)
# ──────────────────────────────────────────────────────────────────────────────

def test_gemini_key_wrong_prefix_is_warning_in_non_strict(monkeypatch):
    # A valid-looking Gemini key must start with AIza.  Put an OpenAI key in the Gemini slot.
    monkeypatch.setenv("GEMINI_API_KEY", "sk-wrong-provider-key-12345")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-correct-openai-key-12345")
    monkeypatch.setenv("XAI_API_KEY", "xai-key-value-here")
    report = runner.preflight_keys(DEFAULT_POLICY, strict=False)
    assert report["overall_status"] == "WARN", f"Expected WARN, got {report['overall_status']}: {report}"
    assert report["exit_code"] == 2
    assert len(report["warnings"]) > 0
    assert len(report["errors"]) == 0


def test_openai_key_wrong_prefix_is_warning_in_non_strict(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaGoodKey")
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-sk-key")
    monkeypatch.setenv("XAI_API_KEY", "xai-something")
    report = runner.preflight_keys(DEFAULT_POLICY, strict=False)
    assert report["overall_status"] == "WARN"
    assert report["exit_code"] == 2


# ──────────────────────────────────────────────────────────────────────────────
# preflight_keys: prefix mismatch → error exit 3 in strict mode
# ──────────────────────────────────────────────────────────────────────────────

def test_gemini_key_wrong_prefix_is_error_in_strict(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "sk-wrong-provider-key-12345")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-correct-openai-key-12345")
    monkeypatch.setenv("XAI_API_KEY", "xai-key-value-here")
    report = runner.preflight_keys(DEFAULT_POLICY, strict=True)
    assert report["overall_status"] == "FAIL"
    assert report["exit_code"] == 3
    assert len(report["errors"]) > 0


def test_openai_key_wrong_prefix_is_error_in_strict(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaGoodKey")
    monkeypatch.setenv("OPENAI_API_KEY", "badprefix-key")
    monkeypatch.setenv("XAI_API_KEY", "xai-something")
    report = runner.preflight_keys(DEFAULT_POLICY, strict=True)
    assert report["overall_status"] == "FAIL"
    assert report["exit_code"] == 3


# ──────────────────────────────────────────────────────────────────────────────
# preflight_keys: xAI no prefix check
# ──────────────────────────────────────────────────────────────────────────────

def test_xai_key_any_prefix_is_not_warned(monkeypatch):
    """xAI has no standardized key prefix — any value should not trigger a prefix warning."""
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaGoodKey")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-good-openai-key")
    monkeypatch.setenv("XAI_API_KEY", "something-completely-different")
    report = runner.preflight_keys(DEFAULT_POLICY, strict=False)
    # If no other prefix mismatch, xAI should not cause a warning
    xai_warnings = [w for w in report["warnings"] if "xai" in w.lower() or "XAI_API_KEY" in w]
    assert xai_warnings == [], f"Unexpected xAI prefix warning: {xai_warnings}"


# ──────────────────────────────────────────────────────────────────────────────
# preflight_keys: PASS when all keys correct
# ──────────────────────────────────────────────────────────────────────────────

def test_all_keys_correct_is_pass(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSomethingValid")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-good-openai-key-12345")
    monkeypatch.setenv("XAI_API_KEY", "xai-any-format-is-fine")
    report = runner.preflight_keys(DEFAULT_POLICY, strict=False)
    assert report["overall_status"] == "PASS"
    assert report["exit_code"] == 0
    assert report["errors"] == []
    assert report["warnings"] == []


# ──────────────────────────────────────────────────────────────────────────────
# preflight_keys: report never contains key plaintext
# ──────────────────────────────────────────────────────────────────────────────

def test_report_does_not_contain_key_plaintext(monkeypatch):
    secret = "sk-super-secret-value-that-must-not-appear-in-output"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaFakeKey")
    monkeypatch.setenv("XAI_API_KEY", "xai-fake-key")
    report = runner.preflight_keys(DEFAULT_POLICY, strict=False)
    report_str = str(report)
    assert secret not in report_str, f"Secret leaked in report: {report_str[:200]}"
