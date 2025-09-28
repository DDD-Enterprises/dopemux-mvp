"""Data transformation pipeline."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from chatx.schemas.message import CanonicalMessage
from chatx.schemas.validator import validate_data, quarantine_invalid_data
from chatx.transformers.chunker import ConversationChunk, ConversationChunker, ChunkMethod

logger = logging.getLogger(__name__)


class TransformationPipeline:
    """Pipeline for transforming extracted data into canonical format and chunks."""
    
    def __init__(
        self,
        run_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
        validate_schemas: bool = True,
    ) -> None:
        """Initialize transformation pipeline.
        
        Args:
            run_id: Run identifier for provenance tracking
            output_dir: Directory for outputs and quarantine files
            validate_schemas: Whether to validate against JSON schemas
        """
        self.chunker = ConversationChunker(run_id=run_id)
        self.output_dir = output_dir or Path("./out")
        self.validate_schemas = validate_schemas
        logger.info(f"Initialized transformation pipeline with run_id: {self.chunker.run_id}")
    
    def normalize_messages(self, messages: List[CanonicalMessage]) -> List[CanonicalMessage]:
        """Normalize and clean message data.
        
        Args:
            messages: Raw canonical messages
            
        Returns:
            Normalized messages
        """
        normalized = []
        
        for msg in messages:
            # Basic normalization
            normalized_msg = CanonicalMessage(
                msg_id=msg.msg_id,
                conv_id=msg.conv_id,
                platform=msg.platform,
                timestamp=msg.timestamp,
                sender=msg.sender.strip() if msg.sender else "unknown",
                sender_id=msg.sender_id,
                is_me=msg.is_me,
                text=msg.text.strip() if msg.text else "",
                reply_to_msg_id=msg.reply_to_msg_id,
                reactions=msg.reactions or [],
                attachments=msg.attachments or [],
                source_ref=msg.source_ref,
                source_meta=msg.source_meta,
            )
            
            # Skip empty messages unless they have attachments or reactions
            if (not normalized_msg.text and 
                not normalized_msg.attachments and 
                not normalized_msg.reactions):
                logger.debug(f"Skipping empty message: {msg.msg_id}")
                continue
            
            normalized.append(normalized_msg)
        
        logger.info(f"Normalized {len(normalized)} messages from {len(messages)} input messages")
        return normalized
    
    def chunk_messages(
        self,
        messages: List[CanonicalMessage],
        method: ChunkMethod = "turns",
        contact: str = "unknown",
        **chunk_params: Any,
    ) -> List[ConversationChunk]:
        """Transform messages into conversation chunks.
        
        Args:
            messages: Normalized messages
            method: Chunking method
            contact: Contact identifier
            **chunk_params: Method-specific parameters
            
        Returns:
            List of conversation chunks
        """
        chunks = self.chunker.chunk_messages(
            messages=messages,
            method=method,
            contact=contact,
            **chunk_params,
        )
        
        logger.info(f"Created {len(chunks)} chunks using method '{method}'")
        return chunks
    
    def validate_and_quarantine(
        self,
        chunks: List[ConversationChunk],
        schema_name: str = "chunk"
    ) -> List[ConversationChunk]:
        """Validate chunks and quarantine invalid ones.
        
        Args:
            chunks: Chunks to validate
            schema_name: Schema to validate against
            
        Returns:
            Valid chunks only
        """
        if not self.validate_schemas:
            return chunks
        
        # Convert to dictionaries for validation
        chunk_dicts = [chunk.to_dict() for chunk in chunks]
        
        # Validate and quarantine
        valid_dicts, invalid_dicts = quarantine_invalid_data(
            chunk_dicts,
            schema_name,
            quarantine_dir=self.output_dir / "quarantine"
        )
        
        if invalid_dicts:
            logger.warning(f"Quarantined {len(invalid_dicts)} invalid chunks")
        
        # Return only valid chunks (reconstruct from valid dicts)
        valid_chunks = []
        for chunk, chunk_dict in zip(chunks, chunk_dicts):
            if chunk_dict in valid_dicts:
                valid_chunks.append(chunk)
        
        return valid_chunks
    
    def save_chunks(
        self,
        chunks: List[ConversationChunk],
        output_file: Optional[Path] = None,
        format_type: Literal["json", "jsonl"] = "jsonl",
    ) -> Path:
        """Save chunks to file.
        
        Args:
            chunks: Chunks to save
            output_file: Output file path
            format_type: Output format
            
        Returns:
            Path to saved file
        """
        if not output_file:
            timestamp = chunks[0].meta.date_start.strftime("%Y%m%d_%H%M%S")
            contact_clean = chunks[0].meta.contact.replace("@", "_at_").replace("+", "_plus_")
            output_file = self.output_dir / f"chunks_{contact_clean}_{timestamp}.{format_type}"
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionaries
        chunk_dicts = [chunk.to_dict() for chunk in chunks]
        
        # Save based on format
        if format_type == "jsonl":
            with open(output_file, "w", encoding="utf-8") as f:
                for chunk_dict in chunk_dicts:
                    f.write(json.dumps(chunk_dict, ensure_ascii=False) + "\n")
        elif format_type == "json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(chunk_dicts, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        logger.info(f"Saved {len(chunks)} chunks to {output_file}")
        return output_file
    
    def transform(
        self,
        messages: List[CanonicalMessage],
        method: ChunkMethod = "turns",
        contact: str = "unknown",
        format_type: Literal["json", "jsonl"] = "jsonl",
        output_file: Optional[Path] = None,
        **chunk_params: Any,
    ) -> tuple[List[ConversationChunk], Path]:
        """Run the complete transformation pipeline.
        
        Args:
            messages: Input messages
            method: Chunking method
            contact: Contact identifier
            format_type: Output format
            output_file: Optional output file path
            **chunk_params: Method-specific chunking parameters
            
        Returns:
            Tuple of (chunks, output_file_path)
        """
        logger.info(f"Starting transformation pipeline with {len(messages)} messages")
        
        # Step 1: Normalize messages
        normalized = self.normalize_messages(messages)
        
        # Step 2: Create chunks
        chunks = self.chunk_messages(
            normalized,
            method=method,
            contact=contact,
            **chunk_params,
        )
        
        # Step 3: Validate and quarantine
        valid_chunks = self.validate_and_quarantine(chunks)
        
        # Step 4: Save to file
        output_path = self.save_chunks(
            valid_chunks,
            output_file=output_file,
            format_type=format_type,
        )
        
        logger.info(f"Transformation pipeline complete: {len(valid_chunks)} chunks saved")
        return valid_chunks, output_path
