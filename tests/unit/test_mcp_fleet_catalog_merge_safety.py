"""Merge-safety tests for the `.codex/config.toml` managed-region merge.

Covers two defect classes in `merge_codex_config_toml`:

* F1 — CRLF input: the managed region must be located by offsets in the
  original text so replacement actually happens and the file keeps a single
  line-ending style.
* F2 — the hand-authored `mcp_servers` guard must use a TOML parse as the
  oracle instead of a `"[mcp_servers."` substring probe, which misses other
  spellings and trips on comments/strings.
"""

import tomllib
from pathlib import Path

import pytest

from dopemux.mcp import fleet_catalog

REPO_ROOT = Path(__file__).resolve().parents[2]

BEGIN = fleet_catalog.CODEX_MANAGED_BEGIN
END = fleet_catalog.CODEX_MANAGED_END

# TOML that defines a top-level `mcp_servers` key without the literal
# `[mcp_servers.` spelling the old substring guard looked for.
HAND_AUTHORED_SERVERS = {
    "spaced-header": '[ mcp_servers.rogue ]\ncommand = "x"\n',
    "parent-table": '[mcp_servers]\nrogue.command = "x"\n',
    "dotted-key": 'mcp_servers.rogue = { command = "x" }\n',
}

# TOML that merely mentions the marker text and defines no servers.
BENIGN_MENTIONS = {
    "comment": '# [mcp_servers.old] removed\nmodel = "gpt"\n',
    "string": 'note = "[mcp_servers.x]"\n',
}


@pytest.fixture(scope="module")
def catalog() -> dict:
    return fleet_catalog.load_root_catalog(REPO_ROOT)


@pytest.fixture(scope="module")
def region(catalog) -> str:
    return fleet_catalog.render_codex_managed_region(catalog)


def _servers(toml_text: str) -> dict:
    return tomllib.loads(toml_text)["mcp_servers"]


def test_module_under_test_is_this_checkout():
    # The shared venv carries an editable install of another checkout; pytest's
    # `pythonpath = src` must win so these tests exercise *this* tree.
    expected = REPO_ROOT / "src" / "dopemux" / "mcp" / "fleet_catalog.py"
    assert Path(fleet_catalog.__file__).resolve() == expected.resolve()


# ---------------------------------------------------------------------------
# LF behaviour is pinned byte-for-byte
# ---------------------------------------------------------------------------


def test_lf_append_output_is_byte_identical_to_pre_fix_shape(catalog, region):
    existing = 'model = "gpt"\n\n[agents]\nmax_threads = 4\n'
    expected = 'model = "gpt"\n\n[agents]\nmax_threads = 4\n\n' + region + "\n"

    assert fleet_catalog.merge_codex_config_toml(existing, catalog) == expected
    # Trailing-newline normalisation of the append path is unchanged.
    assert (
        fleet_catalog.merge_codex_config_toml(existing.rstrip("\n"), catalog)
        == expected
    )
    assert fleet_catalog.merge_codex_config_toml(existing + "\n\n", catalog) == expected
    assert fleet_catalog.merge_codex_config_toml("", catalog) == region + "\n"
    assert fleet_catalog.merge_codex_config_toml(None, catalog) == region + "\n"


def test_lf_replace_output_is_byte_identical_to_pre_fix_shape(catalog, region):
    stale = "\n".join(
        [BEGIN + " stale", '[mcp_servers.stale]\ncommand = "old"', "", END]
    )
    existing = 'model = "gpt"\n\n' + stale + "\n\n[agents]\nmax_threads = 4\n"
    expected = 'model = "gpt"\n\n' + region + "\n\n[agents]\nmax_threads = 4\n"

    merged = fleet_catalog.merge_codex_config_toml(existing, catalog)

    assert merged == expected
    assert fleet_catalog.merge_codex_config_toml(merged, catalog) == merged


def test_extract_marked_region_contract_for_other_callers(region):
    lf = 'model = "gpt"\n\n' + region + "\n"
    assert fleet_catalog._extract_marked_region(lf, BEGIN, END) == region

    crlf = lf.replace("\n", "\r\n")
    found = fleet_catalog._extract_marked_region(crlf, BEGIN, END)
    assert found is not None
    assert found in crlf  # a true substring, so `.replace(found, …)` works
    assert found.replace("\r\n", "\n") == region

    assert (
        fleet_catalog._extract_marked_region(BEGIN + "\nno end\n", BEGIN, END) is None
    )
    assert fleet_catalog._extract_marked_region("no markers\n", BEGIN, END) is None


# ---------------------------------------------------------------------------
# F1 — CRLF files
# ---------------------------------------------------------------------------


def test_crlf_round_trip_replaces_region_and_keeps_single_line_ending(catalog, region):
    first = fleet_catalog.merge_codex_config_toml('model = "gpt"\n', catalog)
    crlf = first.replace("\n", "\r\n")

    merged = fleet_catalog.merge_codex_config_toml(crlf, catalog)

    assert merged.count(BEGIN) == 1
    assert merged.count(END) == 1
    assert merged.startswith('model = "gpt"\r\n\r\n')  # user bytes untouched
    assert "\n" not in merged.replace("\r\n", "")  # no mixed line endings
    assert _servers(merged) == _servers(first)
    found = fleet_catalog._extract_marked_region(merged, BEGIN, END)
    assert found is not None
    assert found.replace("\r\n", "\n") == region
    # Idempotent on the CRLF form too.
    assert fleet_catalog.merge_codex_config_toml(merged, catalog) == merged


def test_crlf_stale_region_is_actually_replaced(catalog, region):
    first = fleet_catalog.merge_codex_config_toml('model = "gpt"\n', catalog)
    stale = "\r\n".join(
        [BEGIN + " stale", "[mcp_servers.stale]", 'command = "old"', "", END]
    )
    existing = (
        'model = "gpt"\r\n\r\n' + stale + "\r\n\r\n[agents]\r\nmax_threads = 4\r\n"
    )

    merged = fleet_catalog.merge_codex_config_toml(existing, catalog)

    assert "stale" not in merged
    assert merged.count(BEGIN) == 1
    assert merged.startswith('model = "gpt"\r\n\r\n')
    assert merged.endswith(END + "\r\n\r\n[agents]\r\nmax_threads = 4\r\n")
    assert "\n" not in merged.replace("\r\n", "")
    assert _servers(merged) == _servers(first)
    assert tomllib.loads(merged)["agents"]["max_threads"] == 4


def test_crlf_append_path_keeps_single_line_ending(catalog, region):
    merged = fleet_catalog.merge_codex_config_toml('model = "gpt"\r\n', catalog)

    assert merged.startswith('model = "gpt"\r\n\r\n' + BEGIN)
    assert merged.endswith(END + "\r\n")
    assert "\n" not in merged.replace("\r\n", "")
    assert _servers(merged) == _servers(region)


# ---------------------------------------------------------------------------
# F2 — TOML-parse oracle for the hand-authored guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "existing", HAND_AUTHORED_SERVERS.values(), ids=HAND_AUTHORED_SERVERS
)
def test_hand_authored_servers_are_rejected_without_region(catalog, existing):
    assert "mcp_servers" in tomllib.loads(existing)  # oracle: it really defines servers

    with pytest.raises(fleet_catalog.MCPFleetCatalogError, match="hand-authored"):
        fleet_catalog.merge_codex_config_toml(existing, catalog)


@pytest.mark.parametrize(
    "existing", HAND_AUTHORED_SERVERS.values(), ids=HAND_AUTHORED_SERVERS
)
def test_hand_authored_servers_are_rejected_alongside_region(catalog, region, existing):
    assert "mcp_servers" in tomllib.loads(existing)

    with pytest.raises(fleet_catalog.MCPFleetCatalogError, match="hand-authored"):
        fleet_catalog.merge_codex_config_toml(existing + "\n" + region + "\n", catalog)


@pytest.mark.parametrize("existing", BENIGN_MENTIONS.values(), ids=BENIGN_MENTIONS)
def test_benign_mentions_merge_without_region(catalog, region, existing):
    user_keys = tomllib.loads(existing)
    assert "mcp_servers" not in user_keys  # oracle: no servers defined

    merged = fleet_catalog.merge_codex_config_toml(existing, catalog)

    assert merged == existing + "\n" + region + "\n"
    parsed = tomllib.loads(merged)
    assert {k: parsed[k] for k in user_keys} == user_keys
    assert parsed["mcp_servers"] == _servers(region)


@pytest.mark.parametrize("existing", BENIGN_MENTIONS.values(), ids=BENIGN_MENTIONS)
def test_benign_mentions_merge_alongside_region(catalog, region, existing):
    user_keys = tomllib.loads(existing)
    assert "mcp_servers" not in user_keys
    stale = "\n".join(
        [BEGIN + " stale", '[mcp_servers.stale]\ncommand = "old"', "", END]
    )

    merged = fleet_catalog.merge_codex_config_toml(
        existing + "\n" + stale + "\n", catalog
    )

    assert merged == existing + "\n" + region + "\n"
    parsed = tomllib.loads(merged)
    assert {k: parsed[k] for k in user_keys} == user_keys
    assert parsed["mcp_servers"] == _servers(region)


def test_unparseable_content_mentioning_mcp_servers_fails_closed(catalog, region):
    broken = 'model = "gpt"\nmcp_servers = \n'
    with pytest.raises(tomllib.TOMLDecodeError):
        tomllib.loads(broken)

    with pytest.raises(fleet_catalog.MCPFleetCatalogError, match="mcp_servers"):
        fleet_catalog.merge_codex_config_toml(broken, catalog)
    with pytest.raises(fleet_catalog.MCPFleetCatalogError, match="mcp_servers"):
        fleet_catalog.merge_codex_config_toml(broken + "\n" + region + "\n", catalog)
