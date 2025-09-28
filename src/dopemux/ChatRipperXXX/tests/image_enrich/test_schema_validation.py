from __future__ import annotations

import hashlib

from chatx.schemas.validator import validate_data


def test_minimal_image_enrichment_row_validates():
    # Minimal, but representative row with caption and psych block
    sample = {
        "msg_id": "m1",
        "attachment_index": 0,
        "hash_sha256": hashlib.sha256(b"demo").hexdigest(),
        "caption": {"short": "A person holding a coffee cup"},
        "tags": ["person", "coffee"],
        "psych": {
            "coarse_labels": ["communication"],
            "fine_labels_local": ["anxious_attachment"],
            "emotion_hint": "neutral",
            "interaction_type": "other",
            "power_balance": 0.0,
            "boundary_health": "none",
            "confidence": 0.8,
            "provenance": {
                "schema_v": "1",
                "run_id": "test-run",
                "model_id": "qwen2.5-vl-7b-instruct",
                "prompt_hash": "deadbeefdeadbeef",
                "source": "local",
            },
        },
        "provenance": {
            "schema_v": "1",
            "run_id": "test-run",
            "model_id": "florence2-base",
            "prompt_hash": "cafebabecafebabe",
            "source": "local",
        },
    }

    ok, errors = validate_data(sample, "image_enrichment", strict=False)
    assert ok, f"Schema should validate, got errors: {errors}"


def test_invalid_missing_msg_id_fails():
    sample = {
        "attachment_index": 0,
        "provenance": {
            "schema_v": "1",
            "run_id": "test-run",
            "model_id": "florence2-base",
            "prompt_hash": "cafebabecafebabe",
            "source": "local",
        },
    }
    ok, errors = validate_data(sample, "image_enrichment", strict=False)
    assert not ok and errors, "Validation should fail when required fields are missing"

