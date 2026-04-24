from dopemux.ui.cockpit.render import render_cockpit


def test_rte_renders_as_services_child_surface_only() -> None:
    output = render_cockpit(120, 40)
    assert "Services -> repo-truth-extractor authority:" in output
    assert "R1 Runs authority: repo-truth-extractor" in output
    assert "6 RTE" not in output


def test_rte_tabs_and_seed_runs_render_with_src() -> None:
    output = render_cockpit(120, 40)
    for tab in ("R1 Runs", "R2 Active", "R3 Prescan", "R4 Doctor", "R5 Coverage", "R6 Audit"):
        assert tab in output
    assert "v5-2026-04-22T14:32Z-a91c" in output
    assert "phase=normalize" in output
    assert "SRC=repo-truth-extractor" in output
