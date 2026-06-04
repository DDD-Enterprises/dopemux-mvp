import pytest


@pytest.mark.parametrize(
    ("state", "expected_label"),
    [
        ("measured", "MEASURED"),
        ("inferred", "INFERRED"),
        ("low-conf", "LOW-CONF"),
        ("calibrating", "CALIBRATING"),
        ("unavailable", "UNAVAILABLE"),
    ],
)
def test_confidence_band_renders_explicit_state_label(state, expected_label):
    from dopemux.ux.confidence_band import render_confidence_band

    rendered = render_confidence_band(value=0.82, state=state)

    assert expected_label in rendered
    assert rendered not in {"82%", "82.0%", "0.82"}


def test_confidence_band_low_confidence_overrides_inferred_state():
    from dopemux.ux.confidence_band import render_confidence_band

    rendered = render_confidence_band(value=0.82, state="inferred", confidence=0.42)

    assert "LOW-CONF" in rendered
    assert "INFERRED" not in rendered


def test_confidence_band_unavailable_omits_fabricated_number():
    from dopemux.ux.confidence_band import render_confidence_band

    rendered = render_confidence_band(value=None, state="unavailable")

    assert "UNAVAILABLE" in rendered
    assert "%" not in rendered
