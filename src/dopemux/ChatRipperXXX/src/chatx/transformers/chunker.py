"""Message chunking strategies for conversation analysis."""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from chatx.schemas.message import CanonicalMessage


ChunkMethod = Literal["turns", "daily", "semantic", "fixed"]


class ChunkMetadata:
    """Metadata for a conversation chunk."""
    
    def __init__(
        self,
        contact: str,
        platform: str,
        date_start: datetime,
        date_end: datetime,
        message_ids: List[str],
        method: ChunkMethod,
        index: int,
        overlap: int = 0,
        labels_coarse: Optional[List[str]] = None,
        labels_fine_local: Optional[List[str]] = None,
        episode_ids: Optional[List[str]] = None,
    ) -> None:
        self.contact = contact
        self.platform = platform
        self.date_start = date_start
        self.date_end = date_end
        self.message_ids = message_ids
        self.method = method
        self.index = index
        self.overlap = overlap
        self.labels_coarse = labels_coarse or []
        self.labels_fine_local = labels_fine_local or []
        self.episode_ids = episode_ids or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "contact": self.contact,
            "platform": self.platform,
            "date_start": self.date_start.isoformat(),
            "date_end": self.date_end.isoformat(),
            "message_ids": self.message_ids,
            "labels_coarse": self.labels_coarse,
            "labels_fine_local": self.labels_fine_local,
            "episode_ids": self.episode_ids,
            "window": {
                "method": self.method,
                "index": self.index,
                "overlap": self.overlap,
            },
        }


class ConversationChunk:
    """A chunk of conversation data."""
    
    def __init__(
        self,
        chunk_id: str,
        conv_id: str,
        text: str,
        meta: ChunkMetadata,
        run_id: str,
        source_hash: str,
    ) -> None:
        self.chunk_id = chunk_id
        self.conv_id = conv_id
        self.text = text
        self.meta = meta
        self.run_id = run_id
        self.source_hash = source_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunk_id": self.chunk_id,
            "conv_id": self.conv_id,
            "text": self.text,
            "meta": {
                **self.meta.to_dict(),
                "char_count": len(self.text),
                "token_estimate": len(self.text.split()) * 1.3,  # Rough token estimate
            },
            "provenance": {
                "schema_v": "0.1.0",
                "run_id": self.run_id,
                "source_hash": self.source_hash,
                "model_id": None,
                "prompt_hash": None,
            },
        }


class ConversationChunker:
    """Chunks conversations using various strategies."""
    
    def __init__(self, run_id: Optional[str] = None) -> None:
        """Initialize chunker.
        
        Args:
            run_id: Optional run identifier for provenance
        """
        self.run_id = run_id or str(uuid.uuid4())
    
    def _compute_source_hash(self, messages: List[CanonicalMessage]) -> str:
        """Compute deterministic hash of source messages."""
        # Create stable hash from message IDs and timestamps
        content = "|".join(f"{msg.msg_id}:{msg.timestamp.isoformat()}" for msg in messages)
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _generate_chunk_id(self, conv_id: str, method: str, index: int) -> str:
        """Generate deterministic chunk ID."""
        content = f"{conv_id}:{method}:{index}:{self.run_id}"
        return "ch_" + hashlib.sha256(content.encode()).hexdigest()[:8]
    
    def chunk_by_turns(
        self,
        messages: List[CanonicalMessage],
        turns_per_chunk: int = 40,
        stride: int = 10,
        contact: str = "unknown",
    ) -> List[ConversationChunk]:
        """Chunk messages by turn count with sliding window.
        
        Args:
            messages: Messages to chunk
            turns_per_chunk: Number of turns per chunk
            stride: Overlap between chunks
            contact: Contact identifier
            
        Returns:
            List of conversation chunks
        """
        if not messages:
            return []
        
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        source_hash = self._compute_source_hash(sorted_messages)
        
        # Determine conversation ID and platform
        conv_id = sorted_messages[0].conv_id or "unknown"
        platform = sorted_messages[0].platform
        
        chunks = []
        index = 0
        
        for i in range(0, len(sorted_messages), turns_per_chunk - stride):
            end_idx = min(i + turns_per_chunk, len(sorted_messages))
            chunk_messages = sorted_messages[i:end_idx]
            
            if not chunk_messages:
                break
            
            # Build chunk text
            text_lines = []
            for msg in chunk_messages:
                sender = "ME" if msg.is_me else contact
                timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M")
                text_lines.append(f"[{timestamp}] {sender}: {msg.text}")
            
            text = "\n".join(text_lines)
            
            # Create metadata
            meta = ChunkMetadata(
                contact=contact,
                platform=platform,
                date_start=chunk_messages[0].timestamp,
                date_end=chunk_messages[-1].timestamp,
                message_ids=[msg.msg_id for msg in chunk_messages],
                method="turns",
                index=index,
                overlap=stride if i > 0 else 0,
            )
            
            # Create chunk
            chunk_id = self._generate_chunk_id(conv_id, "turns", index)
            chunk = ConversationChunk(
                chunk_id=chunk_id,
                conv_id=conv_id,
                text=text,
                meta=meta,
                run_id=self.run_id,
                source_hash=source_hash,
            )
            
            chunks.append(chunk)
            index += 1
        
        return chunks
    
    def chunk_by_daily(
        self,
        messages: List[CanonicalMessage],
        contact: str = "unknown",
    ) -> List[ConversationChunk]:
        """Chunk messages by daily windows.
        
        Args:
            messages: Messages to chunk
            contact: Contact identifier
            
        Returns:
            List of conversation chunks
        """
        if not messages:
            return []
        
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        source_hash = self._compute_source_hash(sorted_messages)
        
        # Group by date
        daily_groups = {}
        for msg in sorted_messages:
            date_key = msg.timestamp.date()
            if date_key not in daily_groups:
                daily_groups[date_key] = []
            daily_groups[date_key].append(msg)
        
        # Create chunks
        chunks = []
        conv_id = sorted_messages[0].conv_id or "unknown"
        platform = sorted_messages[0].platform
        
        for index, (date, day_messages) in enumerate(sorted(daily_groups.items())):
            if not day_messages:
                continue
            
            # Build chunk text
            text_lines = []
            for msg in day_messages:
                sender = "ME" if msg.is_me else contact
                timestamp = msg.timestamp.strftime("%H:%M")
                text_lines.append(f"[{timestamp}] {sender}: {msg.text}")
            
            text = f"=== {date.isoformat()} ===\n" + "\n".join(text_lines)
            
            # Create metadata
            date_start = datetime.combine(date, day_messages[0].timestamp.time())
            date_end = datetime.combine(date, day_messages[-1].timestamp.time())
            
            meta = ChunkMetadata(
                contact=contact,
                platform=platform,
                date_start=date_start,
                date_end=date_end,
                message_ids=[msg.msg_id for msg in day_messages],
                method="daily",
                index=index,
                overlap=0,
            )
            
            # Create chunk
            chunk_id = self._generate_chunk_id(conv_id, "daily", index)
            chunk = ConversationChunk(
                chunk_id=chunk_id,
                conv_id=conv_id,
                text=text,
                meta=meta,
                run_id=self.run_id,
                source_hash=source_hash,
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def chunk_by_fixed_size(
        self,
        messages: List[CanonicalMessage],
        char_limit: int = 4000,
        contact: str = "unknown",
    ) -> List[ConversationChunk]:
        """Chunk messages by character count with smart boundaries.
        
        Args:
            messages: Messages to chunk
            char_limit: Maximum characters per chunk
            contact: Contact identifier
            
        Returns:
            List of conversation chunks
        """
        if not messages:
            return []
        
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        source_hash = self._compute_source_hash(sorted_messages)
        
        conv_id = sorted_messages[0].conv_id or "unknown"
        platform = sorted_messages[0].platform
        
        chunks = []
        current_messages = []
        current_char_count = 0
        index = 0
        
        for msg in sorted_messages:
            sender = "ME" if msg.is_me else contact
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M")
            msg_text = f"[{timestamp}] {sender}: {msg.text}"
            msg_char_count = len(msg_text) + 1  # +1 for newline
            
            # Check if adding this message would exceed limit
            if current_char_count + msg_char_count > char_limit and current_messages:
                # Create chunk from current messages
                text = "\n".join(
                    f"[{m.timestamp.strftime('%Y-%m-%d %H:%M')}] "
                    f"{'ME' if m.is_me else contact}: {m.text}"
                    for m in current_messages
                )
                
                meta = ChunkMetadata(
                    contact=contact,
                    platform=platform,
                    date_start=current_messages[0].timestamp,
                    date_end=current_messages[-1].timestamp,
                    message_ids=[m.msg_id for m in current_messages],
                    method="fixed",
                    index=index,
                    overlap=0,
                )
                
                chunk_id = self._generate_chunk_id(conv_id, "fixed", index)
                chunk = ConversationChunk(
                    chunk_id=chunk_id,
                    conv_id=conv_id,
                    text=text,
                    meta=meta,
                    run_id=self.run_id,
                    source_hash=source_hash,
                )
                
                chunks.append(chunk)
                index += 1
                
                # Reset for next chunk
                current_messages = []
                current_char_count = 0
            
            # Add current message to chunk
            current_messages.append(msg)
            current_char_count += msg_char_count
        
        # Handle remaining messages
        if current_messages:
            text = "\n".join(
                f"[{m.timestamp.strftime('%Y-%m-%d %H:%M')}] "
                f"{'ME' if m.is_me else contact}: {m.text}"
                for m in current_messages
            )
            
            meta = ChunkMetadata(
                contact=contact,
                platform=platform,
                date_start=current_messages[0].timestamp,
                date_end=current_messages[-1].timestamp,
                message_ids=[m.msg_id for m in current_messages],
                method="fixed",
                index=index,
                overlap=0,
            )
            
            chunk_id = self._generate_chunk_id(conv_id, "fixed", index)
            chunk = ConversationChunk(
                chunk_id=chunk_id,
                conv_id=conv_id,
                text=text,
                meta=meta,
                run_id=self.run_id,
                source_hash=source_hash,
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def chunk_messages(
        self,
        messages: List[CanonicalMessage],
        method: ChunkMethod = "turns",
        contact: str = "unknown",
        **kwargs: Any,
    ) -> List[ConversationChunk]:
        """Chunk messages using specified strategy.
        
        Args:
            messages: Messages to chunk
            method: Chunking strategy
            contact: Contact identifier
            **kwargs: Method-specific parameters
            
        Returns:
            List of conversation chunks
        """
        if method == "turns":
            return self.chunk_by_turns(
                messages,
                turns_per_chunk=kwargs.get("turns_per_chunk", 40),
                stride=kwargs.get("stride", 10),
                contact=contact,
            )
        elif method == "daily":
            return self.chunk_by_daily(messages, contact=contact)
        elif method == "fixed":
            return self.chunk_by_fixed_size(
                messages,
                char_limit=kwargs.get("char_limit", 4000),
                contact=contact,
            )
        else:
            raise ValueError(f"Unsupported chunking method: {method}")