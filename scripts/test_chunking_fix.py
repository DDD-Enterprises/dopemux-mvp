#!/usr/bin/env python3
"""Test and fix document chunking."""

import re
from typing import List


def chunk_text_FIXED(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    preserve_structure: bool = True,
) -> List[str]:
    """Fixed chunking with proper sentence handling."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []

    if not preserve_structure:
        # Simple character-based chunking
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i : i + chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks

    # Structure-preserving chunking
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # If paragraph is small, try to add to current chunk
        if len(paragraph) <= chunk_size:
            test_addition = current_chunk + ("\n\n" if current_chunk else "") + paragraph
            if len(test_addition) <= chunk_size:
                current_chunk = test_addition
                continue
            else:
                # Current chunk is full, save it
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
                continue

        # Paragraph is too large, needs sentence-level splitting
        # First, save current chunk if it exists
        if current_chunk:
            chunks.append(current_chunk)
            current_chunk = ""

        # Split paragraph by sentences
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Try to add sentence to current chunk
            test_addition = current_chunk + (" " if current_chunk else "") + sentence

            if len(test_addition) <= chunk_size:
                current_chunk = test_addition
            else:
                # Current chunk is full
                if current_chunk:
                    chunks.append(current_chunk)
                # Start new chunk with this sentence
                # If sentence itself > chunk_size, split by words
                if len(sentence) > chunk_size:
                    words = sentence.split()
                    word_chunk = ""
                    for word in words:
                        test_word = word_chunk + (" " if word_chunk else "") + word
                        if len(test_word) <= chunk_size:
                            word_chunk = test_word
                        else:
                            if word_chunk:
                                chunks.append(word_chunk)
                            word_chunk = word
                    current_chunk = word_chunk
                else:
                    current_chunk = sentence

    # Don't forget final chunk!
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# Test it
test_text = "Short para.\n\nSecond para.\n\n" + ("Long sentence here. " * 200)
print(f"Input: {len(test_text)} chars")

chunks = chunk_text_FIXED(test_text, chunk_size=1000, chunk_overlap=100)
print(f"Output: {len(chunks)} chunks")

for i, chunk in enumerate(chunks[:5]):
    print(f"Chunk {i+1}: {len(chunk)} chars")

# Test on actual file
from pathlib import Path
test_file = Path("/Users/hue/code/code-audit/claudedocs/EXHAUSTIVE-AUDIT-PLAN.md")
if test_file.exists():
    file_text = test_file.read_text()
    chunks = chunk_text_FIXED(file_text, chunk_size=1000, chunk_overlap=100)
    print(f"\nActual file test:")
    print(f"  Input: {len(file_text)} chars")
    print(f"  Output: {len(chunks)} chunks")
    print(f"  Avg chunk size: {len(file_text) / len(chunks):.0f} chars")
