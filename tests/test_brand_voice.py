from services.shared.brand_voice import (
    StatusChip,
    brand_error,
    brand_payload,
    brand_text,
    break_copy,
    hyperfocus_copy,
    tone_name,
    voice_header,
)


def test_brand_text_prefixes_chip_and_preserves_message():
    rendered = brand_text("Keep the next step visible.", chip=StatusChip.LIVE)

    assert rendered == "[LIVE] Keep the next step visible."


def test_brand_payload_includes_additive_metadata():
    payload = brand_payload("Recovery block protected.", chip=StatusChip.AFTERCARE, surface="ui")

    assert payload["message"] == "[AFTERCARE] Recovery block protected."
    assert payload["status_chip"] == "AFTERCARE"
    assert payload["tone"] == "aftercare"
    assert payload["voice_header"] == voice_header("ui")


def test_break_and_hyperfocus_copy_are_deterministic():
    urgent_title, urgent_message, urgent_speech = break_copy(90, urgent=True)
    hyper_title, hyper_message, hyper_speech = hyperfocus_copy(120)

    assert urgent_title.startswith("[BLOCKER]")
    assert urgent_message.startswith("[BLOCKER]")
    assert urgent_speech == "Break needed now. You have been working for 90 minutes. Take a ten minute reset."
    assert hyper_title.startswith("[BLOCKER]")
    assert hyper_message.startswith("[BLOCKER]")
    assert hyper_speech == (
        "Hyperfocus guard. You have been working for 120 minutes without a break. "
        "Step out for fifteen minutes and reset."
    )


def test_brand_error_and_tone_name_follow_chip_mapping():
    assert brand_error("Check the trace.", chip=StatusChip.BLOCKER) == "[BLOCKER] Check the trace."
    assert tone_name(StatusChip.LOGGED) == "logged"
