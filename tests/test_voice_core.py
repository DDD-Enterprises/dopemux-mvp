from __future__ import annotations

from dopemux.voice import (
    Surface,
    VoiceMode,
    build_rewrite_instruction,
    load_voice_gates,
    select_mode,
    validate_output,
)
from dopemux.ui.voice import VoiceEngine, validate_output as legacy_validate_output


def test_load_voice_gates_reads_bundle_defaults() -> None:
    gates = load_voice_gates()

    assert gates["lexical_gates"]["hard_avoid_phrases"] == [
        "as an ai",
        "probably",
        "maybe",
        "generally speaking",
    ]
    assert "NEXT:" in gates["lexical_gates"]["required_closers"]


def test_validate_output_rejects_hard_avoid_phrase() -> None:
    result = validate_output(
        Surface.CLI,
        VoiceMode.FILTH_DAEMON,
        "Maybe this is fine.\nNEXT: inspect the artifact.",
        load_voice_gates(),
    )

    assert not result.ok
    assert any(item.code == "LEX_HARD_AVOID" for item in result.violations)


def test_cli_and_agent_surfaces_require_closer() -> None:
    result = validate_output(
        Surface.AGENT,
        VoiceMode.CLINICAL_FORENSICS,
        "FACT: artifact missing.",
        load_voice_gates(),
    )

    assert not result.ok
    assert any(item.code == "MISSING_CLOSER" for item in result.violations)


def test_ui_surface_requires_shape_and_blocks_shame_language() -> None:
    result = validate_output(
        Surface.UI,
        VoiceMode.UI_STRICT,
        'label: focus guard\nmessage: public shame is live.\naction: retry',
        load_voice_gates(),
    )

    assert not result.ok
    assert any(item.code == "UI_TONE" for item in result.violations)


def test_select_mode_is_deterministic() -> None:
    assert select_mode(Surface.UI, "anything") is VoiceMode.UI_STRICT
    assert select_mode(Surface.AGENT, "privacy shield and coverage threshold") is VoiceMode.CLINICAL_FORENSICS
    assert select_mode(Surface.CLI, "short banner") is VoiceMode.BANNER


def test_rewrite_instruction_lists_violations() -> None:
    result = validate_output(
        Surface.CLI,
        VoiceMode.FILTH_DAEMON,
        "As an AI I can help.",
        load_voice_gates(),
    )

    rewrite = build_rewrite_instruction(result.violations)

    assert rewrite.startswith("DRIFT ALERT: voice gates failed.")
    assert "LEX_HARD_AVOID" in rewrite


def test_voice_engine_is_deterministic_for_existing_callers() -> None:
    engine = VoiceEngine(mode=VoiceMode.UX_SCOLD, is_scattered=True)

    assert engine.get_roast() == engine.get_roast()
    assert engine.banner("detail") == engine.banner("detail")
    assert engine.get_aftercare() == "Logged. Hydrate. That's enough for now."


def test_legacy_validate_output_returns_string_messages() -> None:
    violations = legacy_validate_output("probably\nNEXT: tighten the copy.")

    assert violations
    assert "LEX_HARD_AVOID" in violations[0]
