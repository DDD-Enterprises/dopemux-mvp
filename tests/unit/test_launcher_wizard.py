from __future__ import annotations

from pathlib import Path

from dopemux.console import console as dopemux_console
from dopemux.ux import launcher_wizard


def test_start_wizard_uses_shared_dopemux_console(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeLive:
        is_started = False

        def start(self) -> None:
            self.is_started = True

        def stop(self) -> None:
            self.is_started = False

    class FakeWizard:
        def __init__(self, console) -> None:  # type: ignore[no-untyped-def]
            captured["console"] = console
            self.live = FakeLive()

        def run_role_selection(self):  # type: ignore[no-untyped-def]
            return None

    monkeypatch.setattr(launcher_wizard, "LauncherWizard", FakeWizard)

    role_key, wizard = launcher_wizard.start_wizard()

    assert role_key is None
    assert wizard is None
    assert captured["console"] is dopemux_console


def test_launcher_footer_renders_status_chip(monkeypatch) -> None:
    class FakeInstructionManager:
        def __init__(self, _cwd: Path) -> None:
            pass

        def list_personas(self) -> list[str]:
            return []

    monkeypatch.setattr(launcher_wizard, "InstructionManager", FakeInstructionManager)

    wizard = launcher_wizard.LauncherWizard(dopemux_console)
    footer = wizard._build_footer()

    assert "[LOGGED]" in footer.plain
    assert "Use ↑/↓ to navigate" in footer.plain
