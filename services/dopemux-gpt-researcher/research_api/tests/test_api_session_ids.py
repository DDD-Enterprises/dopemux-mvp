"""Validation tests for the research API request boundary."""

from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

try:
    from ..api.main import ResearchRequest
except ImportError:  # pragma: no cover - direct test execution fallback
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from api.main import ResearchRequest


def test_research_request_accepts_uuid_session_id():
    request = ResearchRequest(
        topic="Security review of CodeQL taint handling",
        session_id="550e8400-e29b-41d4-a716-446655440000",
    )

    assert str(request.session_id) == "550e8400-e29b-41d4-a716-446655440000"


def test_research_request_rejects_non_uuid_session_id():
    with pytest.raises(ValidationError):
        ResearchRequest(
            topic="Security review of CodeQL taint handling",
            session_id="not-a-valid-session-id",
        )
