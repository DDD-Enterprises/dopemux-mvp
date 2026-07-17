"""TP-0017 acceptance harness tests (deterministic; live consent fail-closed)."""

from __future__ import annotations

import json

from dcp_facade import acceptance as ACC


def test_live_mode_requires_dual_consent(monkeypatch):
    monkeypatch.delenv(ACC.LIVE_CONSENT_ENV, raising=False)
    monkeypatch.delenv(ACC.LIVE_TOKEN_ENV, raising=False)
    monkeypatch.delenv(ACC.LIVE_PROVIDER_ENV, raising=False)
    ok, reason = ACC.live_mode_authorized()
    assert ok is False
    assert ACC.LIVE_CONSENT_ENV in reason


def test_live_mode_rejects_placeholder_token(monkeypatch):
    monkeypatch.setenv(ACC.LIVE_CONSENT_ENV, "1")
    monkeypatch.setenv(ACC.LIVE_TOKEN_ENV, "<PLACEHOLDER>")
    monkeypatch.setenv(ACC.LIVE_PROVIDER_ENV, "chatgpt")
    ok, reason = ACC.live_mode_authorized()
    assert ok is False
    assert "placeholder" in reason


def test_deterministic_gates_pass_without_network(monkeypatch):
    monkeypatch.delenv(ACC.LIVE_CONSENT_ENV, raising=False)
    results = ACC.run_deterministic_gates()
    assert results
    assert all(r.status in {"PASS", "FAIL"} for r in results)
    assert any(r.test_id == "DCP-ACC-001" and r.status == "PASS" for r in results)
    assert any(r.test_id == "DCP-ACC-006" and r.status == "PASS" for r in results)
    assert any(r.test_id == "DCP-ACC-014" and r.status == "PASS" for r in results)
    assert any(r.test_id == "DCP-ACC-022" and r.status == "PASS" for r in results)


def test_full_report_marks_live_not_run_and_not_release_ready(monkeypatch):
    monkeypatch.delenv(ACC.LIVE_CONSENT_ENV, raising=False)
    report = ACC.run_acceptance(include_live=True)
    assert report["live_authorized"] is False
    assert report["release_ready"] is False
    assert report["blocking_failures"] == 0
    assert report["blocking_live_not_run"] > 0
    # No secret material in JSON
    blob = json.dumps(report)
    assert "acc-token-alpha" not in blob
    assert "Bearer" not in blob


def test_skipped_live_is_never_pass(monkeypatch):
    monkeypatch.delenv(ACC.LIVE_CONSENT_ENV, raising=False)
    live = ACC.run_live_gates()
    assert live
    assert all(r.status == "NOT_RUN" for r in live)
    assert all(r.blocking for r in live)


def test_local_live_loopback_passes_with_synthetic_token(monkeypatch):
    monkeypatch.setenv(ACC.LIVE_CONSENT_ENV, "1")
    monkeypatch.setenv(ACC.LIVE_TOKEN_ENV, "synthetic-local-live-token-0017")
    monkeypatch.setenv(ACC.LIVE_PROVIDER_ENV, "local")
    live = ACC.run_live_gates()
    assert any(r.status == "PASS" and r.gate_type == "live" for r in live)
    # Vendor tunnel gates remain NOT_RUN without vendor secrets/runners.
    assert any(r.test_id == "DCP-ACC-024" and r.status == "NOT_RUN" for r in live)
    assert any(r.test_id == "DCP-ACC-027" and r.status == "PASS" for r in live)
    # Never leak token into details
    blob = " ".join(r.detail for r in live)
    assert "synthetic-local-live-token-0017" not in blob
