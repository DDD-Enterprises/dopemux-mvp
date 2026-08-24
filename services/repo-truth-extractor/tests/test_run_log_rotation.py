"""F-19: RUN.log grew unbounded (plain `logging.FileHandler`, append mode,
no cap, no automated rotation). `configure_run_file_logger` in
run_extraction_v5.py now defaults to a `RotatingFileHandler` sized from
DPMX_RUN_LOG_MAX_BYTES / DPMX_RUN_LOG_BACKUP_COUNT (with a 10 MiB / 5-backup
default), and still supports opting back out to unbounded growth by setting
the max-bytes env var to 0.
"""
from __future__ import annotations

import importlib.util
import logging
import logging.handlers
import sys
import types
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module(name: str) -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runner_module(request: pytest.FixtureRequest) -> types.ModuleType:
    extract_runner_logger = logging.getLogger("extract_runner")
    original_level = extract_runner_logger.level
    module = _load_runner_module(f"run_extraction_v5_log_rotation_{request.node.name}")
    yield module
    # `configure_run_file_logger` attaches to the process-wide
    # `logging.getLogger("extract_runner")` registry (shared across every
    # loaded copy of the module in this pytest session) — always detach and
    # close whatever handler this test installed, and restore the logger's
    # level, so nothing leaks into unrelated tests running later in the
    # same session.
    handler = getattr(module, "_RUN_FILE_HANDLER", None)
    if handler is not None:
        extract_runner_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    extract_runner_logger.setLevel(original_level)


def test_run_log_rotates_by_default_when_size_cap_exceeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner_module: types.ModuleType
) -> None:
    monkeypatch.setenv(runner_module.RUN_LOG_MAX_BYTES_ENV, "500")
    monkeypatch.setenv(runner_module.RUN_LOG_BACKUP_COUNT_ENV, "2")

    run_log_path = runner_module.configure_run_file_logger(tmp_path)
    assert isinstance(runner_module._RUN_FILE_HANDLER, logging.handlers.RotatingFileHandler)

    logger = logging.getLogger("extract_runner")
    # `logging.basicConfig()` in the module under test is a no-op once the
    # root logger already has handlers (true inside a pytest session that
    # has run other tests) — pin the level explicitly here so this test's
    # INFO records aren't filtered out by whatever the root logger's level
    # happened to be left at by test ordering. This is a test-isolation
    # concern only: in a real CLI invocation `basicConfig` runs in a fresh
    # process and reliably sets root to INFO.
    logger.setLevel(logging.INFO)
    for i in range(200):
        logger.info("padding line %04d %s", i, "x" * 40)

    assert run_log_path.exists()
    # RotatingFileHandler must have kept the live file under (roughly) the
    # cap and rolled at least one backup out — this is what "no automated
    # rotation" (F-19) means was previously missing.
    assert run_log_path.stat().st_size <= 500 + 4096  # allow one record's slack
    rotated = sorted(tmp_path.glob("RUN.log.*"))
    assert rotated, f"expected rotated backup files under {tmp_path}, found none"
    assert len(rotated) <= 2


def test_run_log_rotation_disabled_via_zero_max_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner_module: types.ModuleType
) -> None:
    monkeypatch.setenv(runner_module.RUN_LOG_MAX_BYTES_ENV, "0")

    runner_module.configure_run_file_logger(tmp_path)

    # Opting out (max_bytes=0) preserves the pre-fix plain-append behavior
    # for any caller that relied on it.
    assert type(runner_module._RUN_FILE_HANDLER) is logging.FileHandler


def test_run_log_default_env_is_ten_mib_five_backups(
    runner_module: types.ModuleType,
) -> None:
    assert runner_module.DEFAULT_RUN_LOG_MAX_BYTES == 10 * 1024 * 1024
    assert runner_module.DEFAULT_RUN_LOG_BACKUP_COUNT == 5
