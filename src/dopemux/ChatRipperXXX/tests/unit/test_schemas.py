"""Tests for Pydantic schemas."""

from datetime import UTC, datetime

import pytest

from chatx.schemas.enrichment import Certainty, Directness, EnrichmentMessage, Provenance
from chatx.schemas.message import Attachment, CanonicalMessage, Reaction, SourceRef
from chatx.schemas.redaction import PolicyRule, PrivacyPolicy, RedactionReport


class TestCanonicalMessage:
    """Test the CanonicalMessage schema."""
    
    def test_minimal_message(self):
        """Test creating a message with minimal required fields."""
        msg = CanonicalMessage(
            msg_id="123",
            conv_id="conv_456",
            platform="imessage",
            timestamp=datetime.now(UTC),
            sender="John Doe",
            sender_id="john@example.com",
            is_me=False,
            source_ref=SourceRef(path="/path/to/chat.db")
        )
        
        assert msg.msg_id == "123"
        assert msg.platform == "imessage"
        assert msg.is_me is False
        assert len(msg.reactions) == 0
        assert len(msg.attachments) == 0
        assert msg.text is None
    
    def test_message_with_reactions(self):
        """Test message with reactions."""
        reaction = Reaction(
            from_="Jane",
            kind="love",
            ts=datetime.now(UTC)
        )
        
        msg = CanonicalMessage(
            msg_id="123",
            conv_id="conv_456",
            platform="imessage",
            timestamp=datetime.now(UTC),
            sender="John Doe",
            sender_id="john@example.com",
            is_me=False,
            reactions=[reaction],
            source_ref=SourceRef(path="/path/to/chat.db")
        )
        
        assert len(msg.reactions) == 1
        assert msg.reactions[0].from_ == "Jane"
        assert msg.reactions[0].kind == "love"
    
    def test_message_with_attachments(self):
        """Test message with attachments."""
        attachment = Attachment(
            type="image",
            filename="photo.jpg",
            mime_type="image/jpeg"
        )
        
        msg = CanonicalMessage(
            msg_id="123",
            conv_id="conv_456",
            platform="imessage",
            timestamp=datetime.now(UTC),
            sender="John Doe",
            sender_id="john@example.com",
            is_me=False,
            attachments=[attachment],
            source_ref=SourceRef(path="/path/to/chat.db")
        )
        
        assert len(msg.attachments) == 1
        assert msg.attachments[0].type == "image"
        assert msg.attachments[0].filename == "photo.jpg"
    
    def test_invalid_platform(self):
        """Test that invalid platform values are rejected."""
        with pytest.raises(ValueError):
            CanonicalMessage(
                msg_id="123",
                conv_id="conv_456",
                platform="invalid_platform",  # Should fail validation
                timestamp=datetime.now(UTC),
                sender="John Doe",
                sender_id="john@example.com",
                is_me=False,
                source_ref=SourceRef(path="/path/to/chat.db")
            )


class TestEnrichmentMessage:
    """Test the EnrichmentMessage schema."""
    
    def test_minimal_enrichment(self):
        """Test creating enrichment with minimal required fields."""
        provenance = Provenance(
            schema_v="1.0",
            run_id="run_123",
            model_id="gpt-4",
            prompt_hash="abc123"
        )
        
        enrichment = EnrichmentMessage(
            msg_id="123",
            speech_act="inform",
            intent="share information",
            stance="neutral",
            tone="casual",
            emotion_primary="neutral",
            certainty=Certainty(val=0.8),
            directness=Directness(val=0.6),
            boundary_signal="none",
            repair_attempt=False,
            inferred_meaning="User is sharing information",
            confidence_llm=0.9,
            source="local",
            provenance=provenance
        )
        
        assert enrichment.msg_id == "123"
        assert enrichment.stance == "neutral"
        assert enrichment.emotion_primary == "neutral"
        assert enrichment.certainty.val == 0.8
        assert enrichment.source == "local"
    
    def test_enrichment_validation(self):
        """Test validation of enrichment fields."""
        # Test invalid stance
        with pytest.raises(ValueError):
            EnrichmentMessage(
                msg_id="123",
                speech_act="inform",
                intent="share information",
                stance="invalid_stance",  # Should fail
                tone="casual",
                emotion_primary="neutral",
                certainty=Certainty(val=0.8),
                directness=Directness(val=0.6),
                boundary_signal="none",
                repair_attempt=False,
                inferred_meaning="Test",
                confidence_llm=0.9,
                source="local",
                provenance=Provenance(
                    schema_v="1.0", run_id="run_123",
                    model_id="gpt-4", prompt_hash="abc123"
                )
            )


class TestRedactionReport:
    """Test the RedactionReport schema."""
    
    def test_minimal_report(self):
        """Test creating a redaction report."""
        report = RedactionReport(
            coverage=0.95,
            strict=True,
            hardfail_triggered=False,
            messages_total=100,
            tokens_redacted=25
        )
        
        assert report.coverage == 0.95
        assert report.strict is True
        assert report.messages_total == 100
        assert len(report.placeholders) == 0
        assert len(report.visibility_leaks) == 0
    
    def test_report_with_details(self):
        """Test report with placeholder counts and leaks."""
        report = RedactionReport(
            coverage=0.85,
            strict=True,
            hardfail_triggered=False,
            messages_total=100,
            tokens_redacted=25,
            placeholders={"PHONE_NUMBER": 3, "EMAIL": 2},
            visibility_leaks=["potential_leak_1"],
            notes=["Processing completed with warnings"]
        )
        
        assert report.placeholders["PHONE_NUMBER"] == 3
        assert len(report.visibility_leaks) == 1
        assert len(report.notes) == 1


class TestPrivacyPolicy:
    """Test privacy policy schema."""
    
    def test_privacy_policy(self):
        """Test creating a privacy policy."""
        rule = PolicyRule(
            rule_id="phone_numbers",
            description="Redact phone numbers",
            pattern=r"\b\d{3}-\d{3}-\d{4}\b",
            replacement="[PHONE]",
            severity="high"
        )
        
        policy = PrivacyPolicy(
            policy_id="default",
            version="1.0",
            description="Default privacy policy",
            rules=[rule]
        )
        
        assert policy.policy_id == "default"
        assert len(policy.rules) == 1
        assert policy.rules[0].rule_id == "phone_numbers"
        assert policy.strict_mode is True
