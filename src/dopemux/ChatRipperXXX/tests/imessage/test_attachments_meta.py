"""Tests for attachment metadata extraction utilities."""

from chatx.imessage.attachments import (
    MIME_TYPE_MAP,
    UTI_TYPE_MAP,
    determine_attachment_type,
)


class TestAttachmentTypeMapping:
    """Test attachment type determination utilities."""
    
    def test_uti_type_mapping(self):
        """Test UTI to attachment type mapping."""
        # Images
        assert determine_attachment_type("public.jpeg", None, None) == "image"
        assert determine_attachment_type("public.png", None, None) == "image"
        assert determine_attachment_type("public.heic", None, None) == "image"
        
        # Videos
        assert determine_attachment_type("public.mpeg-4", None, None) == "video"
        assert determine_attachment_type("public.quicktime-movie", None, None) == "video"
        
        # Audio
        assert determine_attachment_type("public.mp3", None, None) == "audio"
        assert determine_attachment_type("public.mpeg-4-audio", None, None) == "audio"
        
        # Documents
        assert determine_attachment_type("com.adobe.pdf", None, None) == "file"
        assert determine_attachment_type("com.microsoft.word.doc", None, None) == "file"
        
        # Archives
        assert determine_attachment_type("public.zip-archive", None, None) == "file"
    
    def test_mime_type_fallback(self):
        """Test MIME type fallback when UTI is unavailable."""
        # UTI unknown, fallback to MIME type
        assert determine_attachment_type(None, "image/jpeg", None) == "image"
        assert determine_attachment_type(None, "video/mp4", None) == "video"
        assert determine_attachment_type(None, "audio/mpeg", None) == "audio"
        assert determine_attachment_type(None, "application/pdf", None) == "file"
        
        # UTI unknown, MIME type also unknown
        assert determine_attachment_type("unknown.uti", "unknown/mime", None) == "unknown"
    
    def test_filename_extension_fallback(self):
        """Test filename extension as last resort."""
        # UTI and MIME both unknown, fallback to extension
        assert determine_attachment_type(None, None, "photo.jpg") == "image"
        assert determine_attachment_type(None, None, "video.mp4") == "video"
        assert determine_attachment_type(None, None, "song.mp3") == "audio"
        assert determine_attachment_type(None, None, "doc.pdf") == "file"
        
        # Case insensitive
        assert determine_attachment_type(None, None, "PHOTO.JPG") == "image"
        
        # Unknown extension
        assert determine_attachment_type(None, None, "file.xyz") == "unknown"
    
    def test_uti_takes_precedence(self):
        """Test that UTI takes precedence over MIME type and filename."""
        # UTI says image, but MIME type says video - should trust UTI
        assert determine_attachment_type("public.jpeg", "video/mp4", "file.mp4") == "image"
    
    def test_mime_type_precedence_over_filename(self):
        """Test that MIME type takes precedence over filename extension."""
        # MIME type says video, filename says image - should trust MIME type
        assert determine_attachment_type(None, "video/mp4", "file.jpg") == "video"
    
    def test_empty_or_none_inputs(self):
        """Test handling of empty or None inputs."""
        assert determine_attachment_type(None, None, None) == "unknown"
        assert determine_attachment_type("", "", "") == "unknown"
        assert determine_attachment_type(None, None, "file_without_extension") == "unknown"
    
    def test_comprehensive_type_coverage(self):
        """Test that all major UTI and MIME types are covered."""
        # Verify that our mappings have reasonable coverage
        assert len(UTI_TYPE_MAP) >= 20  # Should have good coverage of Apple UTIs
        assert len(MIME_TYPE_MAP) >= 15  # Should have common MIME types
        
        # Verify all mapped types are valid
        valid_types = {"image", "video", "audio", "file"}
        for uti_type in UTI_TYPE_MAP.values():
            assert uti_type in valid_types
        
        for mime_type in MIME_TYPE_MAP.values():
            assert mime_type in valid_types
