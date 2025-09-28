"""Tests for binary attachment file copying functionality."""

import tempfile
from pathlib import Path

import pytest

from chatx.imessage.attachments import copy_attachment_files, compute_file_hash
from chatx.schemas.message import Attachment


class TestCopyBinaries:
    """Test binary attachment file copying functionality."""
    
    def test_file_hashing(self, tmp_path):
        """Test SHA-256 file content hashing."""
        # Create test file with known content
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, world!"
        test_file.write_bytes(test_content)
        
        # Compute hash
        file_hash = compute_file_hash(test_file)
        
        # Should be deterministic and correct
        import hashlib
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert file_hash == expected_hash
        assert len(file_hash) == 64  # SHA-256 hex length
    
    def test_copy_attachment_files_structure(self, tmp_path):
        """Test that files are copied with correct directory structure."""
        # Create source file
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "test_image.jpg"
        test_content = b"fake image data for testing"
        source_file.write_bytes(test_content)
        
        # Create attachment object pointing to source
        attachment = Attachment(
            type="image",
            filename="test_image.jpg",
            abs_path=None,
            mime_type="image/jpeg",
            uti="public.jpeg",
            transfer_name="IMG_001.jpg"
        )
        
        # Mock the attachment lookup to point to our test file
        import chatx.imessage.attachments as att_module
        original_home = Path.home()
        
        # Temporarily patch Path.home() to point to our test directory
        def mock_home():
            return tmp_path
        
        att_module.Path.home = mock_home
        
        # Create the expected Messages/Attachments structure
        attachments_dir = tmp_path / "Library" / "Messages" / "Attachments"
        attachments_dir.mkdir(parents=True)
        (attachments_dir / "test_image.jpg").write_bytes(test_content)
        
        try:
            # Test file copying
            out_dir = tmp_path / "output"
            
            updated_attachments, _ = copy_attachment_files([attachment], out_dir)
            
            # Verify structure
            assert len(updated_attachments) == 1
            updated_att = updated_attachments[0]
            
            # Should have abs_path set
            assert updated_att.abs_path is not None
            copied_file = Path(updated_att.abs_path)
            assert copied_file.exists()
            
            # Should be in hash-based directory structure
            assert "attachments" in str(copied_file)
            assert copied_file.name.startswith(compute_file_hash(attachments_dir / "test_image.jpg"))
            
            # Content should match
            assert copied_file.read_bytes() == test_content
            assert updated_att.source_meta["hash"]["sha256"] == compute_file_hash(
                attachments_dir / "test_image.jpg"
            )
            
        finally:
            # Restore original Path.home
            att_module.Path.home = lambda: original_home
    
    def test_copy_nonexistent_files_gracefully(self, tmp_path):
        """Test that nonexistent files are handled gracefully."""
        attachment = Attachment(
            type="image",
            filename="nonexistent.jpg",
            abs_path=None,
            mime_type="image/jpeg",
            uti="public.jpeg", 
            transfer_name="MISSING.jpg"
        )
        
        out_dir = tmp_path / "output"
        
        # Should not raise exception
        updated_attachments, _ = copy_attachment_files([attachment], out_dir)
        
        # Attachment should be unchanged (abs_path still None)
        assert len(updated_attachments) == 1
        assert updated_attachments[0].abs_path is None
        assert updated_attachments[0].filename == "nonexistent.jpg"
    
    def test_deduplication_same_content(self, tmp_path):
        """Test that identical files are deduplicated by hash."""
        # Create identical source files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        test_content = b"identical content"
        
        file1 = source_dir / "file1.jpg"
        file2 = source_dir / "file2.jpg"
        file1.write_bytes(test_content)
        file2.write_bytes(test_content)
        
        # Create attachments
        attachment1 = Attachment(
            type="image", filename="file1.jpg", abs_path=None,
            mime_type="image/jpeg", uti="public.jpeg", transfer_name=None
        )
        
        attachment2 = Attachment(
            type="image", filename="file2.jpg", abs_path=None, 
            mime_type="image/jpeg", uti="public.jpeg", transfer_name=None
        )
        
        # Mock file system
        import chatx.imessage.attachments as att_module
        original_home = Path.home()
        
        def mock_home():
            return tmp_path
        
        att_module.Path.home = mock_home
        
        attachments_dir = tmp_path / "Library" / "Messages" / "Attachments"
        attachments_dir.mkdir(parents=True)
        (attachments_dir / "file1.jpg").write_bytes(test_content)
        (attachments_dir / "file2.jpg").write_bytes(test_content)
        
        try:
            out_dir = tmp_path / "output"
            
            updated_attachments, dedupe_map = copy_attachment_files(
                [attachment1, attachment2], out_dir
            )

            # Both should have same hash-based directory
            hash1_dir = Path(updated_attachments[0].abs_path).parent
            hash2_dir = Path(updated_attachments[1].abs_path).parent

            # Same content should result in same hash directory
            assert hash1_dir == hash2_dir
            assert len(dedupe_map) == 1
            
        finally:
            att_module.Path.home = lambda: original_home
    
    def test_multiple_different_files(self, tmp_path):
        """Test copying multiple different files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        # Create different files
        files_content = {
            "image.jpg": b"image data",
            "video.mp4": b"video data that is longer",
            "audio.m4a": b"audio"
        }
        
        attachments = []
        for filename, content in files_content.items():
            (source_dir / filename).write_bytes(content)
            
            attachments.append(Attachment(
                type="image" if "jpg" in filename else "video" if "mp4" in filename else "audio",
                filename=filename,
                abs_path=None,
                mime_type="image/jpeg" if "jpg" in filename else "video/mp4" if "mp4" in filename else "audio/mp4",
                uti="public.jpeg" if "jpg" in filename else "public.mpeg-4" if "mp4" in filename else "public.mpeg-4-audio",
                transfer_name=None
            ))
        
        # Mock file system
        import chatx.imessage.attachments as att_module
        original_home = Path.home()
        
        def mock_home():
            return tmp_path
            
        att_module.Path.home = mock_home
        
        attachments_dir = tmp_path / "Library" / "Messages" / "Attachments"
        attachments_dir.mkdir(parents=True)
        
        for filename, content in files_content.items():
            (attachments_dir / filename).write_bytes(content)
        
        try:
            out_dir = tmp_path / "output"
            updated_attachments, dedupe_map = copy_attachment_files(
                attachments, out_dir
            )

            # All should be copied successfully
            assert len(updated_attachments) == 3

            for att in updated_attachments:
                assert att.abs_path is not None
                copied_file = Path(att.abs_path)
                assert copied_file.exists()

                # Content should match original
                original_content = files_content[att.filename]
                assert copied_file.read_bytes() == original_content

            # Should have different hash directories for different content
            hash_dirs = {Path(att.abs_path).parent for att in updated_attachments}
            assert len(hash_dirs) == 3  # All different content
            assert len(dedupe_map) == 3
            
        finally:
            att_module.Path.home = lambda: original_home