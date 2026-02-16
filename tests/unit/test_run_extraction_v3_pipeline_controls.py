from __future__ import annotations

import importlib.util
import json
from pathlib import Path


RUNNER_PATH = Path(__file__).resolve().parents[2] / "UPGRADES" / "run_extraction_v3.py"
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def make_cfg(*, dry_run: bool, resume: bool) -> runner.RunnerConfig:
    return runner.RunnerConfig(
        dry_run=dry_run,
        max_files_docs=3,
        max_files_code=3,
        max_chars=2000,
        file_truncate_chars=80,
        home_scan_mode="safe",
        r_profile="base",
        resume=resume,
        rpm_openai=0,
        tpm_openai=0,
        rpm_gemini=0,
        tpm_gemini=0,
        rpm_xai=0,
        tpm_xai=0,
        max_inflight=1,
    )


def test_build_partitions_stable_priority_order(tmp_path: Path) -> None:
    files = [
        tmp_path / "docs" / "guide.md",
        tmp_path / "src" / "main.py",
        tmp_path / "scripts" / "start_stack.sh",
        tmp_path / ".claude" / "settings.json",
        tmp_path / "docs" / "archive" / "old.md",
    ]
    for idx, file_path in enumerate(files):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"file-{idx}\n", encoding="utf-8")

    items = [{"path": str(path), "size": path.stat().st_size, "mtime": float(path.stat().st_mtime)} for path in files]
    inventory = runner.build_inventory(items, file_truncate_chars=80)

    first = runner.build_partitions(
        "A",
        inventory,
        max_files=10,
        max_chars=5000,
        file_truncate_chars=80,
    )
    second = runner.build_partitions(
        "A",
        list(reversed(inventory)),
        max_files=10,
        max_chars=5000,
        file_truncate_chars=80,
    )

    first_paths = [path for part in first for path in part.get("ordered_paths", [])]
    second_paths = [path for part in second for path in part.get("ordered_paths", [])]
    assert first_paths == second_paths
    assert first_paths[0].endswith(".claude/settings.json")
    assert first_paths[-1].endswith("docs/archive/old.md")
    assert runner.classify_tier(first_paths[0]) == 0
    assert runner.classify_tier(first_paths[-1]) == 3


def test_tier0_exhausted_before_tier2_or_tier3(tmp_path: Path) -> None:
    tier0_files = [
        tmp_path / ".claude" / "settings.json",
        tmp_path / ".dopemux" / "router.yaml",
        tmp_path / "compose.yml",
    ]
    tier2_file = tmp_path / "src" / "main.py"
    tier3_file = tmp_path / "docs" / "archive" / "old.md"
    for idx, file_path in enumerate(tier0_files + [tier2_file, tier3_file]):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(("x" * 250) + f"-{idx}\n", encoding="utf-8")

    items = [
        {"path": str(path), "size": path.stat().st_size, "mtime": float(path.stat().st_mtime)}
        for path in [tier3_file, tier2_file] + tier0_files
    ]
    inventory = runner.build_inventory(items, file_truncate_chars=120)
    partitions = runner.build_partitions(
        "A",
        inventory,
        max_files=2,
        max_chars=320,
        file_truncate_chars=120,
    )

    flattened = [path for part in partitions for path in part.get("ordered_paths", [])]
    first_non_tier0 = next(
        (idx for idx, path in enumerate(flattened) if runner.classify_tier(path) != 0),
        len(flattened),
    )
    assert all(runner.classify_tier(path) == 0 for path in flattened[:first_non_tier0])
    assert first_non_tier0 < len(flattened)


def test_magic_surface_index_emits_tier0_files(tmp_path: Path) -> None:
    magic = tmp_path / ".claude" / "settings.json"
    non_magic = tmp_path / "src" / "main.py"
    for path in [magic, non_magic]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test\n", encoding="utf-8")

    inventory = runner.build_inventory(
        [
            {"path": str(magic), "size": magic.stat().st_size, "mtime": float(magic.stat().st_mtime)},
            {"path": str(non_magic), "size": non_magic.stat().st_size, "mtime": float(non_magic.stat().st_mtime)},
        ],
        file_truncate_chars=80,
    )

    dirs = {"root": tmp_path / "run_123", "inputs": tmp_path / "run_123" / "00_inputs"}
    dirs["inputs"].mkdir(parents=True, exist_ok=True)
    runner.update_magic_surface_index(dirs, "A", inventory, file_truncate_chars=80)

    index_path = dirs["inputs"] / "MAGIC_SURFACE_INDEX.json"
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    paths = {row["path"] for row in payload["files"]}
    assert str(magic.resolve()) in paths
    assert str(non_magic.resolve()) not in paths
    assert payload["file_count"] == 1


def test_home_safe_filter_blocks_non_allowlisted_paths(tmp_path: Path) -> None:
    home = tmp_path / "home"
    safe_file = home / ".config" / "dopemux" / "config.yaml"
    unsafe_file = home / ".ssh" / "id_rsa"
    safe_file.parent.mkdir(parents=True, exist_ok=True)
    unsafe_file.parent.mkdir(parents=True, exist_ok=True)
    safe_file.write_text("ok: true\n", encoding="utf-8")
    unsafe_file.write_text("secret\n", encoding="utf-8")

    filtered = runner.home_safe_filter(
        [
            {"path": str(safe_file.resolve()), "size": safe_file.stat().st_size, "mtime": float(safe_file.stat().st_mtime)},
            {"path": str(unsafe_file.resolve()), "size": unsafe_file.stat().st_size, "mtime": float(unsafe_file.stat().st_mtime)},
        ],
        home,
    )
    kept_paths = {item["path"] for item in filtered}
    assert str(safe_file.resolve()) in kept_paths
    assert str(unsafe_file.resolve()) not in kept_paths


def test_partition_payload_hash_stable(tmp_path: Path) -> None:
    file_path = tmp_path / "config" / "mcp.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text('{"server":"conport"}\n', encoding="utf-8")

    items = [{"path": str(file_path), "size": file_path.stat().st_size, "mtime": float(file_path.stat().st_mtime)}]
    inventory = runner.build_inventory(items, file_truncate_chars=80)
    by_path = {item["path"]: item for item in inventory}

    payload_hash_1 = runner.build_partition_payload_hash([str(file_path)], by_path, 80)
    payload_hash_2 = runner.build_partition_payload_hash([str(file_path)], by_path, 80)
    assert payload_hash_1 == payload_hash_2


def test_resume_skips_completed_chunks(tmp_path: Path) -> None:
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)

    source = tmp_path / "config" / "settings.toml"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("mode = 'safe'\n", encoding="utf-8")
    inventory = runner.build_inventory([{"path": str(source), "size": source.stat().st_size, "mtime": source.stat().st_mtime}], 80)
    inventory_by_path = {item["path"]: item for item in inventory}

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: TEST.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("TEST.json",))

    partitions = [
        {
            "id": "A_P0001_C0001",
            "base_partition_id": "A_P0001",
            "paths": [str(source)],
            "ordered_paths": [str(source)],
        }
    ]
    cfg = make_cfg(dry_run=True, resume=True)
    controller = runner.RequestController(run_id="run-test", cfg=cfg)

    first = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        inventory_by_path=inventory_by_path,
        phase_dir=phase_dir,
        cfg=cfg,
        request_controller=controller,
    )
    second = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        inventory_by_path=inventory_by_path,
        phase_dir=phase_dir,
        cfg=cfg,
        request_controller=controller,
    )

    assert first["planned_chunks"] == 1
    assert second["skipped_chunks"] == 1
    assert second["hash_mismatch_chunk_ids"] == []


def test_rate_limit_report_counts_retry_deterministically(monkeypatch) -> None:
    class FakeResponse:
        def __init__(self, status_code: int, payload: dict, headers: dict[str, str]):
            self.status_code = status_code
            self._payload = payload
            self.headers = headers
            self.text = json.dumps(payload)

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise runner.requests.HTTPError(f"status={self.status_code}", response=self)

        def json(self) -> dict:
            return self._payload

    responses = [
        FakeResponse(429, {"error": "rate_limit"}, {"retry-after": "1"}),
        FakeResponse(200, {"choices": [{"message": {"content": '{"ok":true}'}}]}, {"x-request-id": "req-2"}),
    ]

    def fake_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        return responses.pop(0)

    monkeypatch.setattr(runner.requests, "post", fake_post)
    monkeypatch.setattr(runner.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    controller = runner.RequestController(run_id="run-test", cfg=make_cfg(dry_run=False, resume=False))
    content, _meta = controller.execute_chat_completion(
        provider="gemini",
        model_id="gemini-2.0-flash-001",
        api_key_env="GEMINI_API_KEY",
        system_prompt="system",
        user_content="user",
        retry_seed="seed",
        est_tokens=10,
    )
    assert content == '{"ok":true}'

    report = controller.export_rate_limit_report()
    gemini = next(item for item in report["providers"] if item["provider"] == "gemini")
    assert gemini["total_calls"] == 1
    assert gemini["successful_calls"] == 1
    assert gemini["retry_events"] == 1
    assert gemini["status_429"] == 1
    assert gemini["retry_after_obeyed"] == 1
    assert gemini["total_backoff_seconds"] == 1.0
