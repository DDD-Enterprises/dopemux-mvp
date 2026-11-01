"""W09 (Runner Memory Wave 2A, R2): ADR-227 narrow DCP-RED-MERGE-SEAM-0001 carve-out.

Exactly 20 files named by W01, W02 and W05 are exempt from the path-level block,
each as a file-exact negative lookahead anchored with ``\\Z``. Everything else in
the three trees, and ``services/task-orchestrator/``, stays blocked.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIR = _ROOT / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))
_SRC_DIR = _ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from dcp_surface_guard import (  # noqa: E402
    RED_LANE_ID,
    _FALLBACK_COMPILED,
    surface_guard_block,
)
from dopemux.dcp import red_lane_rules  # noqa: E402
from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS  # noqa: E402

WMA = "services/working-memory-assistant/"
CONPORT = "docker/mcp-servers-source/conport/"
BRIDGE = "services/dopecon-bridge/"

EXEMPT_BY_TREE = {
    WMA: (
        "dope_memory_main.py",
        "mcp_http.py",
        "auth_identity.py",
        "eventbus_consumer.py",
        "chronicle/store.py",
        "chronicle/schema.sql",
        "chronicle/sqlite_migrations.py",
        "chronicle/migrations/v1_3_0_add_write_principal.sql",
        "tests/test_mcp_http_endpoint.py",
    ),
    CONPORT: (
        "server.py",
        "enhanced_server.py",
        "instance_detector.py",
        "conport_mcp_stdio.py",
        "auth_identity.py",
        "schema.sql",
        "migrations/008_write_principal.sql",
        "migrations/008_rollback.sql",
        "migrations/conport_migration_gate.py",
    ),
    BRIDGE: (
        "dopecon_bridge/clients.py",
        "ddg_mcp_stdio.py",
    ),
}
EXEMPT = tuple(tree + name for tree, names in EXEMPT_BY_TREE.items() for name in names)

# Sampled files that exist (or plausibly exist) in each tree and are NOT exempt.
STILL_BLOCKED = (
    WMA + "conport_client.py",
    WMA + "chronicle/capture_client.py",
    WMA + "chronicle/migrations/v1_2_0_something.sql",
    WMA + "tests/test_other.py",
    WMA + "Dockerfile",
    WMA + "requirements.txt",
    WMA + "src/mcp/server.py",
    CONPORT + "direct_server.py",
    CONPORT + "info_server.py",
    CONPORT + "unified_queries.py",
    CONPORT + "Dockerfile",
    CONPORT + "migrations/007_worktree_support_simple.sql",
    CONPORT + "migrations/008_other.sql",
    CONPORT + "tests/test_anything.py",
    BRIDGE + "main.py",
    BRIDGE + "dopecon_bridge/app.py",
    BRIDGE + "dopecon_bridge/auth.py",
    BRIDGE + "kg_endpoints.py",
    BRIDGE + "Dockerfile",
    BRIDGE + "tests/test_clients.py",
    "services/task-orchestrator/app/main.py",
    "services/task-orchestrator/dopemux_orchestrator/auth.py",
    "src/conport/anything.py",  # ^src/conport/ is not part of this carve-out
)


def _edit(rel: str, tool: str = "Edit", root: Path = _ROOT):
    return surface_guard_block(tool, {"file_path": str(root / rel)}, root)


def _regex_blocked(rel: str) -> bool:
    return any(p.search(rel) for p in FORBIDDEN_PATHS)


def _near_misses(rel: str) -> list[str]:
    """Variants of an exempt path that must NOT inherit its exemption."""
    d, _, base = rel.rpartition("/")
    stem, dot, ext = base.rpartition(".")
    out = [
        rel + ".bak",  # suffix
        rel + "~",
        f"{d}/x{base}",  # prefix
        f"{d}/{base}.orig",
        f"{d}/sub/{base}",  # nested same-named file
        f"{d}/{stem}2.{ext}",
        f"{d}/{base.upper()}",  # case variant of the file name
        f"{d}/{stem.title()}{dot}{ext}",
        f"{d}/../{rel.rsplit('/', 1)[0].rsplit('/', 1)[-1]}/{base}",  # spelled via ..
        f"{d}/./sub/../{base}",  # ..-segment inside the subtree
    ]
    return out


# ---------------------------------------------------------------------------
# The exempt set is exactly the 20 packet-B01 files, as the rules file spells it
# ---------------------------------------------------------------------------

def test_exempt_list_is_exactly_twenty_paths():
    assert len(EXEMPT) == 20
    assert len(set(EXEMPT)) == 20


def _lookahead_names(tree: str) -> set[str]:
    """Parse the file-exact negative lookaheads out of the live pattern for ``tree``."""
    matches = [p for p in FORBIDDEN_PATHS if p.pattern.startswith("^" + tree)]
    assert len(matches) == 1, (tree, [m.pattern for m in matches])
    pat = matches[0]
    assert pat.flags & re.DOTALL, "`.*` patterns must compile with re.DOTALL"
    assert pat.pattern.endswith(r".*\Z")
    names = re.findall(r"\(\?!(.*?)\\Z\)", pat.pattern)
    return {re.sub(r"\\(.)", r"\1", n) for n in names}


@pytest.mark.parametrize("tree", list(EXEMPT_BY_TREE))
def test_rules_file_lookaheads_match_the_pinned_list(tree):
    assert _lookahead_names(tree) == set(EXEMPT_BY_TREE[tree])


@pytest.mark.parametrize("tree", list(EXEMPT_BY_TREE))
def test_no_directory_exemption_in_lookaheads(tree):
    """Every lookahead ends in ``\\Z``; none is a bare directory prefix like ``(?!tests/)``."""
    pat = next(p for p in FORBIDDEN_PATHS if p.pattern.startswith("^" + tree))
    for chunk in re.findall(r"\(\?!.*?\)", pat.pattern):
        assert chunk.endswith(r"\Z)"), chunk


def test_no_traversal_companion_pattern_was_added():
    """File-exact exemptions need no `..` companion (unlike the ADR-226 eval/ directory)."""
    companions = [p.pattern for p in FORBIDDEN_PATHS if r"\.\." in p.pattern]
    assert all(c.startswith("^services/dope-context/") for c in companions), companions


# ---------------------------------------------------------------------------
# Every exempted path is allowed (all three edit tools)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel", EXEMPT)
def test_exempt_path_is_editable(rel):
    for tool in ("Edit", "Write", "NotebookEdit"):
        assert _edit(rel, tool) is None, (tool, rel)
    assert not _regex_blocked(rel), rel


@pytest.mark.parametrize("rel", EXEMPT)
def test_exempt_path_is_not_a_read_block_either(rel):
    assert surface_guard_block("Read", {"file_path": str(_ROOT / rel)}, _ROOT) is None


# ---------------------------------------------------------------------------
# Near-misses stay blocked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel", EXEMPT)
def test_near_misses_of_exempt_paths_stay_blocked(rel):
    for variant in _near_misses(rel):
        result = _edit(variant)
        assert result is not None, variant
        assert RED_LANE_ID in result, variant


@pytest.mark.parametrize("rel", EXEMPT)
def test_embedded_and_trailing_newline_variants_stay_blocked_at_regex_level(rel):
    # Regex layer on its own (the guard's control-char short-circuit is a second layer).
    for variant in (rel + "\n", rel + "\nextra.py"):
        assert _regex_blocked(variant), repr(variant)
    for variant in (rel + "\n", rel + "\nextra.py"):
        result = surface_guard_block("Edit", {"file_path": str(_ROOT / rel) + variant[len(rel):]}, _ROOT)
        assert result is not None, repr(variant)
        assert RED_LANE_ID in result


def test_embedded_newline_does_not_leak_into_a_blocked_sibling():
    """`mcp_http.py\\nDockerfile` must not borrow mcp_http.py's exemption."""
    rel = WMA + "mcp_http.py\nDockerfile"
    assert _regex_blocked(rel)
    assert surface_guard_block("Edit", {"file_path": str(_ROOT / WMA) + "mcp_http.py\nDockerfile"}, _ROOT)


@pytest.mark.parametrize("rel", EXEMPT)
def test_trailing_slash_variant_stays_blocked_at_regex_level(rel):
    """`mcp_http.py/` names a directory, not the exempt file: the rule must not match it.

    Regex layer only. ``surface_guard_block`` builds a ``pathlib.Path``, which drops a
    trailing slash, so at the guard layer the string collapses to the exempt file itself
    (a write to ``file.py/`` fails with ENOTDIR, so this opens nothing).
    """
    assert _regex_blocked(rel + "/"), rel
    assert _regex_blocked(rel + "//"), rel


def test_dotdot_segments_stay_blocked():
    for rel in (
        WMA + "chronicle/../mcp_http.py",  # resolves to an exempt file but is spelled with ..
        WMA + "chronicle/../tests/test_other.py",  # resolves to a blocked file
        WMA + "../task-orchestrator/app/main.py",  # escapes into a sibling tree
        WMA + "../working-memory-assistant/conport_client.py",
        CONPORT + "migrations/../direct_server.py",
        CONPORT + "migrations/../../conport/info_server.py",
        BRIDGE + "dopecon_bridge/../main.py",
        BRIDGE + "dopecon_bridge/../../task-orchestrator/app/main.py",
        "services/foo/../working-memory-assistant/conport_client.py",
        "docker/../docker/mcp-servers-source/conport/direct_server.py",
    ):
        result = _edit(rel)
        assert result is not None, rel
        assert RED_LANE_ID in result, rel


def test_case_variants_of_trees_stay_blocked():
    for rel in (
        "SERVICES/working-memory-assistant/conport_client.py",
        "services/WORKING-MEMORY-ASSISTANT/conport_client.py",
        "Docker/mcp-servers-source/conport/direct_server.py",
        "services/DopeCon-Bridge/main.py",
        WMA + "MCP_HTTP.PY.bak",
    ):
        assert _edit(rel) is not None, rel


def test_control_character_paths_are_hard_blocked_by_the_guard():
    for ch in ("\n", "\r", "\x00", "\x1b", "\x7f"):
        fp = str(_ROOT / WMA / "mcp_http.py") + ch
        assert surface_guard_block("Edit", {"file_path": fp}, _ROOT) is not None, repr(ch)


# ---------------------------------------------------------------------------
# Everything else in the three trees (and the orchestrator) stays blocked
# ---------------------------------------------------------------------------

def test_sample_is_large_enough():
    for tree in (WMA, CONPORT, BRIDGE):
        assert sum(1 for p in STILL_BLOCKED if p.startswith(tree)) >= 5, tree


@pytest.mark.parametrize("rel", STILL_BLOCKED)
def test_every_other_path_stays_blocked(rel):
    for tool in ("Edit", "Write", "NotebookEdit"):
        result = _edit(rel, tool)
        assert result is not None, (tool, rel)
        assert RED_LANE_ID in result
    assert _regex_blocked(rel), rel


def test_task_orchestrator_stays_blocked_wholesale():
    for rel in (
        "services/task-orchestrator/app/main.py",
        "services/task-orchestrator/auth_identity.py",  # same name as an exempt file, other service
        "services/task-orchestrator/mcp_http.py",
        "services/task-orchestrator/dopecon_bridge/clients.py",
    ):
        assert _edit(rel) is not None, rel


def test_same_names_in_other_trees_are_not_exempt():
    """An exempt file name is exempt only at its exact path, never in a sibling tree."""
    for rel in (
        "services/working-memory-assistant/auth_identity.py".replace("working-memory-assistant", "task-orchestrator"),
        CONPORT + "mcp_http.py",
        WMA + "server.py",  # exempt in conport, not here
        WMA + "schema.sql",  # chronicle/schema.sql is exempt, this is not
        CONPORT + "chronicle/schema.sql",
        BRIDGE + "clients.py",  # dopecon_bridge/clients.py is exempt, this is not
        BRIDGE + "auth_identity.py",
        BRIDGE + "mcp_http.py",
        WMA + "migrations/conport_migration_gate.py",
        WMA + "chronicle/migrations/008_write_principal.sql",
    ):
        assert _edit(rel) is not None, rel


# ---------------------------------------------------------------------------
# Symlink: an exempt name pointing at a blocked file is still blocked
# ---------------------------------------------------------------------------

def test_symlink_at_exempt_name_pointing_at_blocked_file_is_blocked(tmp_path):
    root = tmp_path / "repo"
    blocked = root / WMA / "conport_client.py"
    blocked.parent.mkdir(parents=True)
    blocked.write_text("# blocked\n")
    link = root / WMA / "mcp_http.py"
    link.symlink_to("conport_client.py")
    result = surface_guard_block("Edit", {"file_path": str(link)}, root)
    assert result is not None
    assert RED_LANE_ID in result


def test_real_exempt_file_in_scaffold_is_allowed(tmp_path):
    root = tmp_path / "repo"
    real = root / CONPORT / "migrations" / "008_write_principal.sql"
    real.parent.mkdir(parents=True)
    real.write_text("-- new\n")
    assert surface_guard_block("Write", {"file_path": str(real)}, root) is None


# ---------------------------------------------------------------------------
# Wiring invariants
# ---------------------------------------------------------------------------

def test_fallback_patterns_remain_a_subset_of_live_rules():
    for path in (
        "src/dopemux_pr_merge_specialist/queue_drain.py",
        "dopemux_pr_merge_specialist/queue_drain.py",
        "scripts/batch_resolve_and_merge.py",
    ):
        if any(p.search(path) for p in _FALLBACK_COMPILED):
            assert _regex_blocked(path), path


def test_every_forbidden_pattern_is_z_anchored():
    for p in FORBIDDEN_PATHS:
        assert p.pattern.endswith(r"\Z") or p.pattern.endswith(r"\Z)") or r"\Z" in p.pattern, p.pattern
        assert "$" not in p.pattern.replace(r"\$", ""), p.pattern
        if ".*" in p.pattern:
            assert p.flags & re.DOTALL, p.pattern


def test_security_release_gate_follows_the_same_list():
    from tools.pr_steward import security_release_gate as gate

    assert gate.FORBIDDEN_PATHS is red_lane_rules.FORBIDDEN_PATHS


def test_scanner_text_rules_are_untouched():
    ids = [r.rule_id for r in red_lane_rules.TEXT_RULES]
    assert ids == ["MERGE_SEAM_001", "DOPETASK_001", "NETWORK_001", "EXTERNAL_WRITE_001", "LIVE_WRITE_001"]


# ---------------------------------------------------------------------------
# ADR-227
# ---------------------------------------------------------------------------

_ADR = _ROOT / "docs" / "90-adr" / "adr-227-memory-spine-seam-narrow-carveout.md"


def _adr_text() -> str:
    assert _ADR.is_file(), _ADR
    return _ADR.read_text(encoding="utf-8")


def test_adr_frontmatter_status_accepted_and_relations():
    # Operator accepted ADR-227 on 2026-10-31 (ADR227_ACCEPTANCE.md, J01-CARVEOUT).
    text = _adr_text()
    assert text.startswith("---\n")
    front = text.split("---\n", 2)[1]
    assert re.search(r"^id: ADR-227$", front, re.M)
    assert re.search(r"^type: adr$", front, re.M)
    assert re.search(r"^status: accepted$", front, re.M)
    relates = front.split("relates_to:", 1)[1]
    for ref in ("MACRO-DMX-RUNNER-MEMORY-2A-001", "ADR-224", "ADR-226", "ADR-MCPINT-002"):
        assert ref in relates, ref


def test_adr_lists_every_exempt_path():
    text = _adr_text()
    for rel in EXEMPT:
        assert rel in text, rel


def test_adr_states_boundaries():
    text = _adr_text()
    for needle in (
        "red_lane_scanner.py",
        "security_release_gate.py",
        "FORBIDDEN_PATHS",
        "no directory exemption",
        "services/task-orchestrator/",
        "Rollback",
        "git revert",
        "Accepted by the operator",
    ):
        assert needle in text, needle
    assert "no `..` companion" in text
