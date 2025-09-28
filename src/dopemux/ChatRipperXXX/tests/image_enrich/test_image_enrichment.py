"""Tests for image enrichment pipeline."""

import pytest
from pathlib import Path

from chatx.enrichment.image_enricher import (
    ImageEnrichmentRequest,
    ImageEnrichment,
    ImageEnricher,
)


class TestImageEnrichmentRequest:
    """Test ImageEnrichmentRequest class."""

    def test_basic_initialization(self) -> None:
        """Test basic request initialization."""
        request = ImageEnrichmentRequest(
            msg_id="m1",
            attachment_index=0,
            provenance={"source": "local"}
        )

        assert request.msg_id == "m1"
        assert request.attachment_index == 0
        assert request.provenance == {"source": "local"}
        assert request.hash_sha256 == ""  # No image data

    def test_hash_with_path(self, tmp_path: Path) -> None:
        """Test SHA256 hash computation with file path."""
        # Create a test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"test image data")

        request = ImageEnrichmentRequest(
            msg_id="m1",
            attachment_index=0,
            image_path=test_file
        )

        # Should compute hash when accessing property
        import hashlib
        expected_hash = hashlib.sha256(b"test image data").hexdigest()
        assert request.hash_sha256 == expected_hash


class TestImageEnrichment:
    """Test ImageEnrichment class."""

    def test_basic_enrichment(self) -> None:
        """Test basic enrichment creation and serialization."""
        enrichment = ImageEnrichment(
            msg_id="m1",
            attachment_index=0,
            hash_sha256="dummy_hash",
            provenance={"source": "local"},
            objects=[{"label": "person", "conf": 0.8}],
            psych={"emotion_hint": "happy"}
        )

        result = enrichment.dict()

        # Check required fields
        assert result["msg_id"] == "m1"
        assert result["attachment_index"] == 0
        assert result["hash_sha256"] == "dummy_hash"
        assert result["provenance"] == {"source": "local"}

        # Check optional fields
        assert result["objects"] == [{"label": "person", "conf": 0.8}]
        assert result["psych"]["emotion_hint"] == "happy"

    def test_minimal_enrichment(self) -> None:
        """Test enrichment with minimal required fields."""
        enrichment = ImageEnrichment(
            msg_id="m1",
            attachment_index=0,
            hash_sha256="dummy_hash",
            provenance={"source": "local"}
        )

        result = enrichment.dict()

        # Only required fields should be present
        assert "objects" not in result
        assert "psych" not in result
        assert result["msg_id"] == "m1"


@pytest.mark.asyncio
class TestImageEnricher:
    """Test ImageEnricher class."""

    async def test_basic_enrichment_flow(self) -> None:
        """Test basic enrichment flow with placeholder data."""
        enricher = ImageEnricher(
            object_detection_enabled=True,
            vlm_enabled=True
        )

        # Create request with dummy image data
        request = ImageEnrichmentRequest(
            msg_id="m1",
            attachment_index=0,
            image_data=b"dummy_image_data",
            provenance={
                "schema_v": "1",
                "run_id": "test-run",
                "model_id": "test-model",
                "prompt_hash": "testhash",
                "source": "local"
            }
        )

        enrichment, metadata = await enricher.enrich_image(request)

        assert enrichment is not None
        assert enrichment.msg_id == "m1"
        assert enrichment.attachment_index == 0
        assert enrichment is not None and enrichment.provenance["source"] == "local"

        # Check that placeholder data was set
        assert enrichment.objects == [{"label": "person", "conf": 0.85, "box": [0.1, 0.2, 0.3, 0.4]}]
        
        # Check psych analysis
        assert "psych" in enrichment.dict()
        assert enrichment is not None and enrichment.psych is not None and enrichment.psych["emotion_hint"] == "neutral"
        assert enrichment is not None and enrichment.psych is not None and enrichment.psych["coarse_labels"] == ["communication"]

        # Check metadata
        assert "processing_time_ms" in metadata
        assert metadata["run_id"] == enricher.run_id
        assert metadata["features_processed"]["objects"] is True
        assert metadata["features_processed"]["psych"] is True

    async def test_no_image_data_error(self) -> None:
        """Test error handling when no image data provided."""
        enricher = ImageEnricher()

        request = ImageEnrichmentRequest(
            msg_id="m1",
            attachment_index=0,
            provenance={"source": "local"}
        )

        enrichment, metadata = await enricher.enrich_image(request)

        assert enrichment is None
        assert metadata["error"] == "no_image_data"

    def test_enricher_initialization(self) -> None:
        """Test enricher initialization with different options."""
        # Test with all features enabled
        enricher = ImageEnricher(
            object_detection_enabled=True,
            vlm_enabled=True
        )

        assert enricher.object_detection_enabled is True
        assert enricher.vlm_enabled is True
        assert enricher.run_id is not None

        # Test with features disabled
        enricher = ImageEnricher(
            object_detection_enabled=False,
            vlm_enabled=False
        )

        assert enricher.object_detection_enabled is False
        assert enricher.vlm_enabled is False
