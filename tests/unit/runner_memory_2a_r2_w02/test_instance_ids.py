"""``instance_detector``: the ``shared`` instance value and the workspace binding."""

from __future__ import annotations

import pytest

from .helpers import BOUND_WORKSPACE


@pytest.mark.parametrize("value", [None, "", "   ", "shared", "SHARED", " Shared "])
def test_should_treat_shared_and_empty_as_the_null_instance(instance_detector, value):
    assert instance_detector.normalize_instance_id(value) is None
    assert instance_detector.SimpleInstanceDetector.normalize_instance_id(value) is None


def test_should_keep_a_real_instance_id_as_given(instance_detector):
    assert instance_detector.normalize_instance_id("feature-auth") == "feature-auth"
    assert instance_detector.normalize_instance_id(" feature-auth ") == "feature-auth"
    assert instance_detector.SHARED_INSTANCE_ID == "shared"


def test_should_read_the_binding_from_env_without_a_cwd_fallback(instance_detector, monkeypatch):
    monkeypatch.delenv("DOPEMUX_WORKSPACE_ID", raising=False)
    assert instance_detector.get_bound_workspace_id() is None
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "")
    assert instance_detector.SimpleInstanceDetector.get_bound_workspace_id() is None
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", BOUND_WORKSPACE)
    assert instance_detector.get_bound_workspace_id() == BOUND_WORKSPACE


def test_should_keep_the_read_side_behaviour_unchanged(instance_detector, monkeypatch):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "")
    assert instance_detector.get_instance_id() is None
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "feature-auth")
    assert instance_detector.get_instance_id() == "feature-auth"
    monkeypatch.delenv("DOPEMUX_WORKSPACE_ID", raising=False)
    assert instance_detector.get_workspace_id()  # still falls back to the cwd for reads
