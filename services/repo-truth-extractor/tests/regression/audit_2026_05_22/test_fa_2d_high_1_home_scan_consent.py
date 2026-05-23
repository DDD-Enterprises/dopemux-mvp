from __future__ import annotations

from dataclasses import replace
import fnmatch
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

_SERVICE_ROOT = Path(__file__).resolve().parents[3]
_TESTS_ROOT = _SERVICE_ROOT / "tests"
for _path in (_SERVICE_ROOT, _TESTS_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from _v5_smoke_helpers import load_runner_module, make_cfg  # noqa: E402
from rte_phase_wrappers import plan_home_phase  # noqa: E402


def _full_home_cfg(runner: Any) -> Any:
    return replace(make_cfg(runner), home_scan_mode="full")


def test_full_home_scan_refuses_without_explicit_consent_before_collection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = load_runner_module()
    monkeypatch.delenv("DPMX_HOME_SCAN_FULL_OK", raising=False)

    def fail_if_collection_planned(**_: Any) -> Any:
        raise AssertionError("home collection should not be planned without consent")

    monkeypatch.setattr(runner, "_plan_home_phase_impl", fail_if_collection_planned)

    with pytest.raises(RuntimeError, match="DPMX_HOME_SCAN_FULL_OK=1"):
        runner.run_phase_H({"H": tmp_path / "H"}, _full_home_cfg(runner))


def test_full_home_scan_allows_explicit_consent_without_real_home_scan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = load_runner_module()
    monkeypatch.setenv("DPMX_HOME_SCAN_FULL_OK", "1")

    planned: Dict[str, Any] = {}
    executed: Dict[str, Any] = {}

    def fake_plan_home_phase_impl(**kwargs: Any) -> Any:
        planned.update(kwargs)
        return SimpleNamespace(precollected_items=[])

    def fake_run_phase_inner(*args: Any, **kwargs: Any) -> None:
        executed["args"] = args
        executed["precollected_items"] = kwargs["precollected_items"]

    monkeypatch.setattr(runner, "_plan_home_phase_impl", fake_plan_home_phase_impl)
    monkeypatch.setattr(runner, "_run_phase_inner", fake_run_phase_inner)

    runner.run_phase_H({"H": tmp_path / "H"}, _full_home_cfg(runner))

    assert planned["home_scan_mode"] == "full"
    assert executed["precollected_items"] == []


def test_home_phase_sensitive_paths_are_excluded_from_collector_targets(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    sensitive_rel_paths = [
        ".ssh/id_rsa",
        ".SSH/id_rsa",
        ".aws/credentials",
        ".AWS/credentials",
        ".config/mcp/settings.json",
        ".local/share/token.txt",
        ".gnupg/private-keys-v1.d/key",
        ".kube/config",
        ".KUBE/config",
        "Library/Keychains/login.keychain-db",
        "library/keychains/login.keychain-db",
        "Containers/com.example/token.txt",
        "containers/com.example/token.txt",
        ".netrc",
        ".aws_credentials",
    ]
    safe_rel_path = ".dopemux/config.yaml"
    for rel_path in [*sensitive_rel_paths, safe_rel_path]:
        target = home / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture\n", encoding="utf-8")

    captured_excludes: List[str] = []

    class FakeCollector:
        def __init__(self, root: Path, excludes: List[str]) -> None:
            self.root = root
            self.excludes = excludes
            captured_excludes.extend(excludes)

        def _is_excluded(self, path: Path) -> bool:
            name = path.name
            rel = str(path.relative_to(self.root))
            return any(
                fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat)
                for pat in self.excludes
            )

        def collect(self, subdirs: List[str]) -> List[Dict[str, Any]]:
            items: List[Dict[str, Any]] = []
            for subdir in subdirs:
                root = self.root / subdir
                if root.is_file():
                    if not self._is_excluded(root):
                        items.append({"path": str(root)})
                    continue
                for path in sorted(root.rglob("*")):
                    if path.is_file() and not self._is_excluded(path):
                        items.append({"path": str(path)})
            return items

    plan = plan_home_phase(
        home=home,
        collector_factory=FakeCollector,
        home_safe_roots=[
            ".dopemux",
            ".ssh",
            ".SSH",
            ".aws",
            ".AWS",
            ".config/mcp",
            ".local/share",
            ".gnupg",
            ".kube",
            ".KUBE",
            "Library/Keychains",
            "library/keychains",
            "Containers",
            "containers",
            ".netrc",
            ".aws_credentials",
        ],
        home_scan_mode="full",
        home_safe_filter=lambda items, _home: items,
    )

    collected = {
        str(Path(item["path"]).relative_to(home))
        for item in plan.precollected_items or []
    }
    assert safe_rel_path in collected
    assert not collected.intersection(sensitive_rel_paths)
    assert ".ssh/*" in captured_excludes
    assert ".config/*" in captured_excludes
    assert "Library/Keychains/*" in captured_excludes
