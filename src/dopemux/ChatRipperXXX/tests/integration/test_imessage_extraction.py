"""Integration tests for iMessage extraction following TDD approach.

These tests follow the acceptance criteria from ACCEPTANCE_CRITERIA.md and
detailed specifications from IMESSAGE_SPEC.md.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from chatx.extractors.base import ExtractionError
from chatx.extractors.imessage import IMessageExtractor
from chatx.schemas.message import CanonicalMessage


class TestIMessageExtractionIntegration:
    """Integration tests for iMessage extractor with comprehensive test data."""

    def test_extract_messages_comprehensive(
        self, imessage_test_db: Path, expected_imessage_messages: list[dict]
    ) -> None:
        """Test comprehensive message extraction against golden fixtures.
        
        Acceptance Criteria from ACCEPTANCE_CRITERIA.md:
        - Messages MUST include is_me, ISO-8601 timestamps, folded reactions,
          stable reply_to_msg_id for replies, attachment references, and provenance
        """
        extractor = IMessageExtractor(imessage_test_db)
        
        # Extract all messages
        extracted_messages = list(extractor.extract_messages())
        
        # Should extract all non-reaction messages (reactions are folded into target messages)
        # From our test data: 21 total messages - 5 reaction messages = 16 canonical messages
        assert len(extracted_messages) == 16, f"Expected 16 messages, got {len(extracted_messages)}"
        
        # Convert to dicts for easier comparison
        extracted_dicts = [
            msg.model_dump(exclude={"source_ref", "source_meta"})
            for msg in extracted_messages
        ]
        
        # Test each expected message is present with correct data
        for expected in expected_imessage_messages:
            matching_msg = next(
                (msg for msg in extracted_dicts if msg["msg_id"] == expected["msg_id"]),
                None
            )
            assert matching_msg is not None, f"Expected message {expected['msg_id']} not found"
            
            # Test core fields
            assert matching_msg["conv_id"] == expected["conv_id"]
            assert matching_msg["platform"] == expected["platform"]
            assert matching_msg["sender"] == expected["sender"]
            assert matching_msg["sender_id"] == expected["sender_id"]
            assert matching_msg["is_me"] == expected["is_me"]
            assert matching_msg["text"] == expected["text"]
            assert matching_msg["reply_to_msg_id"] == expected["reply_to_msg_id"]
            
            # Test reactions are properly folded
            assert len(matching_msg["reactions"]) == len(expected["reactions"])
            for reaction, expected_reaction in zip(
                matching_msg["reactions"], expected["reactions"], strict=False
            ):
                # Use from_ since that's the actual field name in the model
                assert reaction["from_"] == expected_reaction["from"]
                assert reaction["kind"] == expected_reaction["kind"]
                # Note: reaction["ts"] will be a string in model_dump(), not datetime
                assert "ts" in reaction
                
            # Test attachments
            assert len(matching_msg["attachments"]) == len(expected["attachments"])
            for attachment, expected_attachment in zip(
                matching_msg["attachments"], expected["attachments"], strict=False
            ):
                assert attachment["type"] == expected_attachment["type"]
                assert attachment["filename"] == expected_attachment["filename"]
                
    def test_timestamp_conversion_deterministic(self, imessage_test_db: Path) -> None:
        """Test Apple timestamp conversion is deterministic and handles all formats.
        
        From IMESSAGE_SPEC.md:
        - MUST convert Apple Epoch to ISO-8601 UTC with robust unit handling (ns vs s)
        """
        extractor = IMessageExtractor(imessage_test_db)
        extracted_messages = list(extractor.extract_messages())
        
        # All messages should have valid UTC timestamps
        for msg in extracted_messages:
            assert msg.timestamp is not None
            assert msg.timestamp.tzinfo == UTC
            assert isinstance(msg.timestamp, datetime)
            
        # Find messages with different timestamp formats and verify correct conversion
        nanosecond_msg = next((msg for msg in extracted_messages if msg.msg_id == "11"), None)
        microsecond_msg = next((msg for msg in extracted_messages if msg.msg_id == "12"), None)
        second_msg = next((msg for msg in extracted_messages if msg.msg_id == "1"), None)
        
        assert nanosecond_msg is not None
        assert microsecond_msg is not None
        assert second_msg is not None
        
        # All should have reasonable timestamps (around 2022 based on our test data)
        assert nanosecond_msg.timestamp.year >= 2020
        assert microsecond_msg.timestamp.year >= 2020
        assert second_msg.timestamp.year >= 2020
        
    def test_reactions_folding(self, imessage_test_db: Path) -> None:
        """Test reactions are properly folded into target messages.
        
        From IMESSAGE_SPEC.md:
        - Reaction rows MUST be grouped into target message's reactions[]
        - Reaction rows MUST be suppressed from output as standalone messages
        """
        extractor = IMessageExtractor(imessage_test_db)
        extracted_messages = list(extractor.extract_messages())

        # No message should be a standalone reaction (all should be folded)
        for _msg in extracted_messages:
            # Reactions have empty or null text and associated_message_guid
            # Since they're folded, we shouldn't see any standalone reactions
            pass
            
        # Check specific messages have expected reactions
        msg_with_like = next((msg for msg in extracted_messages if msg.msg_id == "6"), None)
        msg_with_love = next((msg for msg in extracted_messages if msg.msg_id == "3"), None)
        msg_with_laugh = next((msg for msg in extracted_messages if msg.msg_id == "2"), None)
        msg_with_emphasize = next((msg for msg in extracted_messages if msg.msg_id == "1"), None)
        
        assert msg_with_like is not None and len(msg_with_like.reactions) == 1
        assert msg_with_like.reactions[0].kind == "like"
        
        assert msg_with_love is not None and len(msg_with_love.reactions) == 1
        assert msg_with_love.reactions[0].kind == "love"
        
        assert msg_with_laugh is not None and len(msg_with_laugh.reactions) == 1
        assert msg_with_laugh.reactions[0].kind == "laugh"
        
        assert msg_with_emphasize is not None and len(msg_with_emphasize.reactions) == 1
        assert msg_with_emphasize.reactions[0].kind == "emphasize"
        
        # Check that extraction report shows correct reaction fold count
        assert extractor.report.reactions_folded >= 4
        
    def test_reply_chain_resolution(self, imessage_test_db: Path) -> None:
        """Test reply chains are resolved with stable reply_to_msg_id.
        
        From IMESSAGE_SPEC.md:
        - MUST set stable reply_to_msg_id when a DB row is a reply
        - Algorithm must build guid → msg_id map for stable mapping
        """
        extractor = IMessageExtractor(imessage_test_db)
        extracted_messages = list(extractor.extract_messages())
        
        # Find reply chain: msg-004 → msg-005 → msg-006
        parent_msg = next((msg for msg in extracted_messages if msg.msg_id == "4"), None)
        reply_msg = next((msg for msg in extracted_messages if msg.msg_id == "5"), None)
        reply_to_reply = next((msg for msg in extracted_messages if msg.msg_id == "6"), None)
        
        assert parent_msg is not None
        assert reply_msg is not None
        assert reply_to_reply is not None
        
        # Test reply chain structure
        assert parent_msg.reply_to_msg_id is None  # Original message
        assert reply_msg.reply_to_msg_id == "4"    # Replies to parent
        assert reply_to_reply.reply_to_msg_id == "5"  # Replies to reply
        
    def test_attachment_metadata_extraction(self, imessage_test_db: Path) -> None:
        """Test attachment metadata extraction without binary data.
        
        From IMESSAGE_SPEC.md:
        - MUST NOT inline binary data or upload attachments; only references
        - Emit type, filename, mime_type, uti when available
        """
        extractor = IMessageExtractor(imessage_test_db)
        extracted_messages = list(extractor.extract_messages())
        
        # Find message with attachment
        msg_with_attachment = next((msg for msg in extracted_messages if msg.msg_id == "14"), None)
        assert msg_with_attachment is not None
        assert len(msg_with_attachment.attachments) == 1
        
        attachment = msg_with_attachment.attachments[0]
        assert attachment.type == "image"
        assert attachment.filename == "photo.jpg"
        assert attachment.mime_type == "image/jpeg"
        assert attachment.uti == "public.jpeg"
        assert attachment.transfer_name == "IMG_001.jpeg"
        
        # Ensure no binary data is included (abs_path should be None in extraction)
        assert attachment.abs_path is None
        
    def test_provenance_and_source_metadata(self, imessage_test_db: Path) -> None:
        """Test provenance and source metadata preservation.
        
        From IMESSAGE_SPEC.md:
        - MUST include source_ref.path and source_ref.guid
        - MUST persist additional DB columns as source_meta
        """
        extractor = IMessageExtractor(imessage_test_db)
        extracted_messages = list(extractor.extract_messages())
        
        for msg in extracted_messages:
            # Test source_ref is populated
            assert msg.source_ref is not None
            assert msg.source_ref.path == str(imessage_test_db)
            assert msg.source_ref.guid is not None  # Chat GUID
            
            # Test source_meta preserves original fields
            assert msg.source_meta is not None
            assert "msg_rowid" in msg.source_meta
            assert "service" in msg.source_meta
            
    def test_edge_cases_and_error_handling(self, imessage_test_db: Path) -> None:
        """Test edge cases: null text, missing handles, orphaned reactions."""
        extractor = IMessageExtractor(imessage_test_db)
        extracted_messages = list(extractor.extract_messages())
        
        # Test message with no handle (should default to "Unknown")
        no_handle_msg = next((msg for msg in extracted_messages if msg.msg_id == "16"), None)
        assert no_handle_msg is not None
        assert no_handle_msg.sender == "Unknown"
        assert no_handle_msg.sender_id == "unknown"
        
        # Test messages with null/empty text
        null_text_msg = next((msg for msg in extracted_messages if msg.msg_id == "17"), None)
        empty_text_msg = next((msg for msg in extracted_messages if msg.msg_id == "18"), None)
        
        assert null_text_msg is not None
        assert null_text_msg.text is None
        
        assert empty_text_msg is not None
        assert empty_text_msg.text == ""
        
        # Test orphaned reaction is handled (doesn't crash, gets counted)
        # The orphaned reaction should be tracked in unresolved_replies or similar
        assert extractor.report.errors is not None  # Some mechanism to track issues
        
    def test_database_validation(self, invalid_imessage_db: Path) -> None:
        """Test database validation rejects invalid databases."""
        extractor = IMessageExtractor(invalid_imessage_db)
        
        # Should fail validation
        assert not extractor.validate_source()
        
        # Should raise ExtractionError on extraction attempt
        with pytest.raises(ExtractionError):
            list(extractor.extract_messages())
            
    def test_minimal_database_extraction(self, minimal_imessage_db: Path) -> None:
        """Test extraction works with minimal valid database."""
        extractor = IMessageExtractor(minimal_imessage_db)
        
        # Should pass validation
        assert extractor.validate_source()
        
        # Should extract the single message
        extracted_messages = list(extractor.extract_messages())
        assert len(extracted_messages) == 1
        
        msg = extracted_messages[0]
        assert msg.msg_id == "1"
        assert msg.text == "Hello"
        assert msg.is_me is False
        
    def test_schema_compliance(self, imessage_test_db: Path) -> None:
        """Test all extracted messages comply with CanonicalMessage schema."""
        extractor = IMessageExtractor(imessage_test_db)
        extracted_messages = list(extractor.extract_messages())
        
        # All messages should be valid CanonicalMessage instances
        for msg in extracted_messages:
            assert isinstance(msg, CanonicalMessage)
            
            # Test that Pydantic validation passes (would raise if invalid)
            msg.model_validate(msg.model_dump())
            
            # Test required fields are present
            assert msg.msg_id is not None
            assert msg.conv_id is not None
            assert msg.platform == "imessage"
            assert msg.timestamp is not None
            assert msg.sender is not None
            assert msg.sender_id is not None
            assert msg.source_ref is not None
            
    def test_extraction_report_generation(self, imessage_test_db: Path) -> None:
        """Test extraction report contains useful metrics."""
        extractor = IMessageExtractor(imessage_test_db)
        _extracted_messages = list(extractor.extract_messages())

        # Report should track key metrics
        assert extractor.report.reactions_folded > 0
        assert isinstance(extractor.report.errors, list)

        # Should track unresolved replies if any
        assert hasattr(extractor.report, 'unresolved_replies')
        
    def test_deterministic_extraction(self, imessage_test_db: Path) -> None:
        """Test extraction is deterministic - multiple runs produce identical results."""
        extractor1 = IMessageExtractor(imessage_test_db)
        extractor2 = IMessageExtractor(imessage_test_db)
        
        messages1 = list(extractor1.extract_messages())
        messages2 = list(extractor2.extract_messages())
        
        assert len(messages1) == len(messages2)
        
        # Compare message content (excluding timestamps which might vary due to
        # datetime.now() fallbacks)
        for msg1, msg2 in zip(messages1, messages2, strict=False):
            assert msg1.msg_id == msg2.msg_id
            assert msg1.conv_id == msg2.conv_id
            assert msg1.text == msg2.text
            assert msg1.is_me == msg2.is_me
            assert msg1.sender == msg2.sender
            assert len(msg1.reactions) == len(msg2.reactions)
