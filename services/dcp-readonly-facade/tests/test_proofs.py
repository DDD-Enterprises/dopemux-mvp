"""Proofs: listing, containment, symlink/cross-project rejection, staleness."""

from __future__ import annotations

import os

from dcp_facade import proofs


def test_list_bundles_and_substring_filter(make_workspace):
    info = make_workspace(
        bundles={"TP-A-0001": {"head_sha": "x"}, "TP-B-0002": {"head_sha": "y"}}
    )
    ws = info["path"]
    bundles, truncated = proofs.list_bundles(ws)
    names = {b["bundle_id"] for b in bundles}
    assert names == {"TP-A-0001", "TP-B-0002"}
    assert truncated is False
    only_a, _ = proofs.list_bundles(ws, packet_filter="TP-A")
    assert {b["bundle_id"] for b in only_a} == {"TP-A-0001"}


def test_list_bundles_filter_is_literal_not_regex(make_workspace):
    # a regex metachar is treated as a literal substring (no match, no error)
    ws = make_workspace(bundles={"TP-A-0001": {"head_sha": "x"}})["path"]
    out, _ = proofs.list_bundles(ws, packet_filter="TP-A.*")
    assert out == []


def test_list_bundles_cap_truncation(make_workspace):
    many = {f"TP-{i:04d}": {"head_sha": "h"} for i in range(25)}
    ws = make_workspace(bundles=many)["path"]
    bundles, truncated = proofs.list_bundles(ws, cap=20)
    assert len(bundles) == 20
    assert truncated is True


def test_fetch_valid_bundle(make_workspace):
    ws = make_workspace(bundles={"TP-A-0001": {"head_sha": "abc"}})["path"]
    data, block, warnings = proofs.fetch_bundle(ws, "TP-A-0001", current_head=None)
    assert block is None
    assert data["bundle_id"] == "TP-A-0001"
    assert "PROOF.json" in data["contents"]
    assert "AUDIT.md" in data["contents"]


def test_invalid_bundle_id_rejected(make_workspace):
    ws = make_workspace()["path"]
    for bad in ("../etc", "a/b", "..", ".hidden", "", None):
        data, block, _ = proofs.fetch_bundle(ws, bad)
        assert data is None
        assert block is not None


def test_symlink_escape_rejected(make_workspace, tmp_path):
    info = make_workspace()
    ws = info["path"]
    proof_root = ws / "proof"
    proof_root.mkdir(exist_ok=True)
    outside = tmp_path / "outside_secret"
    outside.mkdir()
    (outside / "PROOF.json").write_text("{}", encoding="utf-8")
    os.symlink(outside, proof_root / "evil")
    data, block, _ = proofs.fetch_bundle(ws, "evil")
    assert data is None
    assert "escapes proof root" in block


def test_cross_project_bundle_not_found(make_workspace):
    # bundle exists only in project B; fetching it via A's workspace must not find it
    make_workspace(name="a", bundles={"TP-ONLY-IN-A": {"head_sha": "1"}})
    ws_b = make_workspace(name="b")["path"]
    data, block, _ = proofs.fetch_bundle(ws_b, "TP-ONLY-IN-A")
    assert data is None
    assert block == "bundle not found"


def test_stale_proof_warning(make_workspace):
    ws = make_workspace(bundles={"TP-A-0001": {"head_sha": "deadbeefdeadbeef"}})["path"]
    data, block, warnings = proofs.fetch_bundle(ws, "TP-A-0001", current_head="cafebabecafebabe")
    assert block is None
    assert data["stale"] is True
    assert any("stale proof bundle" in w for w in warnings)


def test_fresh_proof_no_stale_warning(make_workspace):
    ws = make_workspace(bundles={"TP-A-0001": {"head_sha": "matching"}})["path"]
    data, block, warnings = proofs.fetch_bundle(ws, "TP-A-0001", current_head="matching")
    assert data["stale"] is False
    assert not any("stale" in w for w in warnings)


def test_large_file_bounded_and_truncated(make_workspace):
    big = "A" * (proofs._MAX_FILE_BYTES + 5000)
    ws = make_workspace(
        bundles={"TP-A-0001": {"head_sha": "h"}},
        extra_proof_files={"TP-A-0001/COMMAND_LOG.md": big},
    )["path"]
    data, block, warnings = proofs.fetch_bundle(ws, "TP-A-0001")
    assert block is None
    assert len(data["contents"]["COMMAND_LOG.md"]) <= proofs._MAX_FILE_BYTES
    assert any("truncated" in w for w in warnings)
