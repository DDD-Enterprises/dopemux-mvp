from dopemux.ui.cockpit.frame import LAYOUTS
from dopemux.ui.cockpit.render import render_cockpit


def test_bridge_actions_are_in_inspector_area_and_adapter_only() -> None:
    layout = LAYOUTS["120x40"]
    lines = render_cockpit(120, 40).splitlines()
    bridge_lines = [line for line in lines if "ADAPTER -> do" in line]
    assert len(bridge_lines) == 1
    assert bridge_lines[0].index("ADAPTER ->") > layout.right_divider
    assert "[EDGE] bridge is adapter/proxy o" in "\n".join(lines)
    assert "WRITE -> <service> : <action>" in "\n".join(lines)
    assert "→" not in "\n".join(lines)
