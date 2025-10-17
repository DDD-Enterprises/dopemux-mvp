#!/usr/bin/env python3
"""
Semantic Chunking Component

Intelligently chunks conversational data at natural boundaries while preserving context.
Optimized for chatlog conversations with speaker changes, topic shifts, and temporal gaps.

Features:
- Smart boundary detection (speaker changes, topic shifts, time gaps)
- Context preservation with overlapping windows
- Metadata tracking for each chunk
- ADHD-friendly processing with progress visualization
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import logging

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Represents a single chat message."""
    speaker: str
    content: str
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.message_id is None:
            # Generate ID from content hash
            self.message_id = hashlib.sha256(
                f"{self.speaker}:{self.content}".encode()
            ).hexdigest()[:12]

@dataclass
class ConversationChunk:
    """Represents a semantically coherent chunk of conversation."""
    chunk_id: str
    messages: List[ChatMessage]
    start_timestamp: Optional[datetime]
    end_timestamp: Optional[datetime]
    participants: List[str]
    estimated_tokens: int
    chunk_type: str  # 'topic_shift', 'speaker_change', 'time_gap', 'length_limit'
    overlap_with_previous: bool = False
    overlap_with_next: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def text_content(self) -> str:
        """Get combined text content of all messages."""
        return "\n".join([
            f"{msg.speaker}: {msg.content}"
            for msg in self.messages
        ])

    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate duration of chunk in minutes."""
        if self.start_timestamp and self.end_timestamp:
            delta = self.end_timestamp - self.start_timestamp
            return delta.total_seconds() / 60.0
        return None

class SemanticChunker:
    """
    Chunks conversations at semantic boundaries with context preservation.

    Strategies:
    1. Topic Coherence: TF-IDF similarity between adjacent messages
    2. Speaker Patterns: Natural conversation breaks
    3. Temporal Gaps: Significant time delays
    4. Length Limits: Maximum token constraints
    5. Overlapping Windows: Context preservation
    """

    def __init__(
        self,
        max_chunk_tokens: int = 4000,
        min_chunk_tokens: int = 100,
        overlap_tokens: int = 200,
        topic_similarity_threshold: float = 0.3,
        time_gap_minutes: int = 30,
        enable_spacy: bool = True
    ):
        self.max_chunk_tokens = max_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.topic_similarity_threshold = topic_similarity_threshold
        self.time_gap_minutes = time_gap_minutes

        # Load spaCy model for advanced NLP
        self.nlp = None
        if enable_spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded for semantic analysis")
            except OSError:
                logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")

        # TF-IDF vectorizer for topic similarity
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )

        # Patterns for detecting conversation markers
        self.topic_markers = [
            r'\b(by the way|btw|anyway|speaking of|moving on|next topic)\b',
            r'\b(let\'s talk about|let\'s discuss|regarding|about)\b',
            r'\b(changing topics?|new topic|different topic)\b'
        ]

        self.decision_markers = [
            r'\b(decided|decision|conclusion|agreed|consensus)\b',
            r'\b(we should|let\'s go with|final decision)\b'
        ]

        self.question_markers = [
            r'\b(what do you think|thoughts|opinions|any ideas)\b',
            r'\?$',  # Ends with question mark
        ]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters for English)."""
        return max(1, len(text) // 4)

    def _detect_topic_shift(self, messages: List[ChatMessage], window_size: int = 3) -> List[int]:
        """Detect topic shifts using TF-IDF similarity."""
        if len(messages) < window_size * 2:
            return []

        # Extract text windows
        windows = []
        for i in range(len(messages) - window_size + 1):
            window_text = " ".join([
                msg.content for msg in messages[i:i + window_size]
            ])
            windows.append(window_text)

        if len(windows) < 2:
            return []

        try:
            # Calculate TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(windows)

            # Calculate similarities between adjacent windows
            shift_points = []
            for i in range(len(windows) - 1):
                similarity = cosine_similarity(
                    tfidf_matrix[i:i+1],
                    tfidf_matrix[i+1:i+2]
                )[0][0]

                # Low similarity indicates topic shift
                if similarity < self.topic_similarity_threshold:
                    shift_points.append(i + window_size)  # Index in original messages

            return shift_points

        except Exception as e:
            logger.warning(f"Topic shift detection failed: {e}")
            return []

    def _detect_speaker_patterns(self, messages: List[ChatMessage]) -> List[int]:
        """Detect natural conversation breaks based on speaker patterns."""
        break_points = []

        for i in range(1, len(messages)):
            current_msg = messages[i]
            prev_msg = messages[i-1]

            # Long monologue by same speaker
            if (current_msg.speaker == prev_msg.speaker and
                len(prev_msg.content) > 500):  # Long message threshold
                break_points.append(i)

            # Return to previous speaker after interruption
            if (i >= 2 and
                current_msg.speaker == messages[i-2].speaker and
                current_msg.speaker != prev_msg.speaker):
                break_points.append(i)

        return break_points

    def _detect_time_gaps(self, messages: List[ChatMessage]) -> List[int]:
        """Detect significant time gaps between messages."""
        gap_points = []

        for i in range(1, len(messages)):
            if (messages[i].timestamp and messages[i-1].timestamp):
                time_diff = messages[i].timestamp - messages[i-1].timestamp
                if time_diff.total_seconds() / 60 > self.time_gap_minutes:
                    gap_points.append(i)

        return gap_points

    def _detect_content_markers(self, messages: List[ChatMessage]) -> List[int]:
        """Detect conversation markers like topic transitions, decisions."""
        marker_points = []

        for i, message in enumerate(messages):
            content = message.content.lower()

            # Check for topic transition markers
            for pattern in self.topic_markers:
                if re.search(pattern, content, re.IGNORECASE):
                    marker_points.append(i)
                    break

        return marker_points

    def _merge_boundary_points(self, *boundary_lists: List[int]) -> List[int]:
        """Merge and deduplicate boundary points."""
        all_points = set()
        for boundary_list in boundary_lists:
            all_points.update(boundary_list)

        # Remove points too close to each other (< 2 messages apart)
        merged_points = sorted(all_points)
        filtered_points = []

        for point in merged_points:
            if not filtered_points or point - filtered_points[-1] >= 2:
                filtered_points.append(point)

        return filtered_points

    def _create_chunk(
        self,
        messages: List[ChatMessage],
        chunk_type: str,
        overlap_prev: bool = False,
        overlap_next: bool = False
    ) -> ConversationChunk:
        """Create a conversation chunk from messages."""

        if not messages:
            raise ValueError("Cannot create chunk from empty messages")

        # Generate chunk ID
        first_msg = messages[0]
        last_msg = messages[-1]
        chunk_id = hashlib.sha256(
            f"{first_msg.message_id}:{last_msg.message_id}:{len(messages)}".encode()
        ).hexdigest()[:16]

        # Extract participants
        participants = list(set(msg.speaker for msg in messages))

        # Calculate timestamps
        start_time = None
        end_time = None
        for msg in messages:
            if msg.timestamp:
                if start_time is None or msg.timestamp < start_time:
                    start_time = msg.timestamp
                if end_time is None or msg.timestamp > end_time:
                    end_time = msg.timestamp

        # Estimate tokens
        text_content = "\n".join([f"{msg.speaker}: {msg.content}" for msg in messages])
        estimated_tokens = self._estimate_tokens(text_content)

        return ConversationChunk(
            chunk_id=chunk_id,
            messages=messages,
            start_timestamp=start_time,
            end_timestamp=end_time,
            participants=participants,
            estimated_tokens=estimated_tokens,
            chunk_type=chunk_type,
            overlap_with_previous=overlap_prev,
            overlap_with_next=overlap_next
        )

    def _create_overlapping_chunks(self, base_chunks: List[ConversationChunk]) -> List[ConversationChunk]:
        """Add overlapping chunks for context preservation."""
        all_chunks = []

        for i, chunk in enumerate(base_chunks):
            all_chunks.append(chunk)

            # Create overlap with next chunk if it exists
            if i < len(base_chunks) - 1:
                next_chunk = base_chunks[i + 1]

                # Take last N tokens from current chunk + first N tokens from next
                current_messages = chunk.messages
                next_messages = next_chunk.messages

                # Find split point for overlap
                overlap_messages = []

                # Add tail of current chunk
                current_tokens = 0
                for msg in reversed(current_messages):
                    msg_tokens = self._estimate_tokens(f"{msg.speaker}: {msg.content}")
                    if current_tokens + msg_tokens <= self.overlap_tokens // 2:
                        overlap_messages.insert(0, msg)
                        current_tokens += msg_tokens
                    else:
                        break

                # Add head of next chunk
                next_tokens = 0
                for msg in next_messages:
                    msg_tokens = self._estimate_tokens(f"{msg.speaker}: {msg.content}")
                    if next_tokens + msg_tokens <= self.overlap_tokens // 2:
                        overlap_messages.append(msg)
                        next_tokens += msg_tokens
                    else:
                        break

                if overlap_messages:
                    overlap_chunk = self._create_chunk(
                        overlap_messages,
                        chunk_type="overlap",
                        overlap_prev=True,
                        overlap_next=True
                    )
                    all_chunks.append(overlap_chunk)

        return all_chunks

    def chunk_conversation(
        self,
        messages: List[ChatMessage],
        show_progress: bool = True
    ) -> List[ConversationChunk]:
        """
        Main chunking method that applies all strategies.

        Returns semantically coherent chunks with overlap for context preservation.
        """

        if not messages:
            return []

        chunks = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            TimeElapsedColumn(),
            console=console,
            disable=not show_progress
        ) as progress:

            # Phase 1: Detect boundaries
            task = progress.add_task("Analyzing conversation structure...", total=100)

            progress.update(task, advance=20, description="Detecting topic shifts...")
            topic_shifts = self._detect_topic_shift(messages)

            progress.update(task, advance=20, description="Analyzing speaker patterns...")
            speaker_breaks = self._detect_speaker_patterns(messages)

            progress.update(task, advance=20, description="Finding time gaps...")
            time_gaps = self._detect_time_gaps(messages)

            progress.update(task, advance=20, description="Identifying content markers...")
            content_markers = self._detect_content_markers(messages)

            progress.update(task, advance=20, description="Merging boundary points...")
            boundary_points = self._merge_boundary_points(
                topic_shifts, speaker_breaks, time_gaps, content_markers
            )

            # Always start with boundary at beginning
            if 0 not in boundary_points:
                boundary_points = [0] + boundary_points

            # Add end boundary
            if len(messages) not in boundary_points:
                boundary_points.append(len(messages))

            boundary_points.sort()

            # Phase 2: Create base chunks
            progress.update(task, advance=0, description="Creating conversation chunks...")

            for i in range(len(boundary_points) - 1):
                start_idx = boundary_points[i]
                end_idx = boundary_points[i + 1]

                chunk_messages = messages[start_idx:end_idx]

                if not chunk_messages:
                    continue

                # Determine chunk type
                chunk_type = "length_limit"
                if start_idx in topic_shifts:
                    chunk_type = "topic_shift"
                elif start_idx in speaker_breaks:
                    chunk_type = "speaker_change"
                elif start_idx in time_gaps:
                    chunk_type = "time_gap"
                elif start_idx in content_markers:
                    chunk_type = "content_marker"

                # Check if chunk is too large
                estimated_tokens = sum(
                    self._estimate_tokens(f"{msg.speaker}: {msg.content}")
                    for msg in chunk_messages
                )

                if estimated_tokens > self.max_chunk_tokens:
                    # Split large chunk by token count
                    current_tokens = 0
                    current_messages = []

                    for msg in chunk_messages:
                        msg_tokens = self._estimate_tokens(f"{msg.speaker}: {msg.content}")

                        if current_tokens + msg_tokens > self.max_chunk_tokens and current_messages:
                            # Create chunk from accumulated messages
                            chunk = self._create_chunk(current_messages, "length_limit")
                            chunks.append(chunk)

                            # Start new chunk
                            current_messages = [msg]
                            current_tokens = msg_tokens
                        else:
                            current_messages.append(msg)
                            current_tokens += msg_tokens

                    # Add remaining messages
                    if current_messages:
                        chunk = self._create_chunk(current_messages, chunk_type)
                        chunks.append(chunk)

                else:
                    # Chunk is good size
                    chunk = self._create_chunk(chunk_messages, chunk_type)
                    chunks.append(chunk)

            progress.update(task, advance=0, description="Adding overlapping chunks...")

            # Phase 3: Add overlapping chunks for context
            if self.overlap_tokens > 0:
                chunks = self._create_overlapping_chunks(chunks)

        # Filter out chunks that are too small
        filtered_chunks = [
            chunk for chunk in chunks
            if chunk.estimated_tokens >= self.min_chunk_tokens
        ]

        console.print(Panel(
            f"✅ Created {len(filtered_chunks)} conversation chunks\n"
            f"📊 Average size: {np.mean([c.estimated_tokens for c in filtered_chunks]):.0f} tokens\n"
            f"🔗 Overlap chunks: {sum(1 for c in filtered_chunks if c.chunk_type == 'overlap')}",
            title="Semantic Chunking Complete",
            border_style="green"
        ))

        return filtered_chunks

    def chunk_from_text(
        self,
        text: str,
        format_type: str = "colon_separated",
        show_progress: bool = True
    ) -> List[ConversationChunk]:
        """
        Convenience method to chunk from raw text.

        Supports formats:
        - colon_separated: "Speaker: Message"
        - timestamp_separated: "[HH:MM] Speaker: Message"
        - json_lines: One JSON object per line
        """

        messages = []

        if format_type == "colon_separated":
            lines = text.strip().split('\n')
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                if ':' in line:
                    speaker, content = line.split(':', 1)
                    speaker = speaker.strip()
                    content = content.strip()

                    if speaker and content:
                        messages.append(ChatMessage(
                            speaker=speaker,
                            content=content,
                            message_id=f"msg_{line_num:04d}"
                        ))

        elif format_type == "timestamp_separated":
            # Parse format: "[HH:MM] Speaker: Message"
            timestamp_pattern = r'\[(\d{1,2}:\d{2})\]\s*([^:]+):\s*(.+)'
            lines = text.strip().split('\n')

            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                match = re.match(timestamp_pattern, line)
                if match:
                    time_str, speaker, content = match.groups()

                    # Convert time string to datetime (assume today)
                    try:
                        hour, minute = map(int, time_str.split(':'))
                        timestamp = datetime.now().replace(
                            hour=hour,
                            minute=minute,
                            second=0,
                            microsecond=0
                        )
                    except ValueError:
                        timestamp = None

                    messages.append(ChatMessage(
                        speaker=speaker.strip(),
                        content=content.strip(),
                        timestamp=timestamp,
                        message_id=f"msg_{line_num:04d}"
                    ))

        return self.chunk_conversation(messages, show_progress)

# Example usage and testing
def test_semantic_chunker():
    """Test the semantic chunker with sample conversation."""

    # Sample conversation
    conversation_text = """
    Alice: Hey everyone! We need to discuss the new project requirements.
    Bob: Agreed! I think we should start with the authentication system.
    Charlie: Good point. We decided last week to use OAuth2 for authentication.
    Alice: Yes, and we need to implement user registration by next Friday.
    Bob: I'll take care of the database schema. Should we use PostgreSQL?
    Charlie: That sounds good. We also need to consider the API design.
    Alice: Important: The client wants real-time notifications.
    Bob: Noted. I'll research WebSocket implementation options.
    Charlie: We should also plan for mobile compatibility.
    Alice: By the way, changing topics - we need to discuss the budget for Q4.
    Bob: The infrastructure costs are higher than expected.
    Charlie: We might need to optimize our cloud usage.
    Alice: Let's schedule a separate meeting for budget discussions.
    Bob: Good idea. Back to the technical implementation - any thoughts on testing?
    Charlie: We should implement unit tests from the beginning.
    Alice: Agreed. Let's also set up CI/CD pipeline.
    """

    chunker = SemanticChunker()
    chunks = chunker.chunk_from_text(conversation_text)

    console.print(f"\n🧩 Generated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        console.print(f"\n**Chunk {i+1}** ({chunk.chunk_type}, {chunk.estimated_tokens} tokens):")
        console.print(f"Participants: {', '.join(chunk.participants)}")
        console.print(f"Content preview: {chunk.text_content[:100]}...")

    return chunks

if __name__ == "__main__":
    test_semantic_chunker()