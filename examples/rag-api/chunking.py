"""
Simple text chunking for a RAG ingestion pipeline.

Splits a document into overlapping, roughly fixed-size chunks. This is
deliberately basic (character-count based, whitespace-aware) rather than a
"real" recursive/semantic chunker — the goal is to make chunk boundaries and
overlap easy to see and reason about. See
../../docs/16-rag-apis/chunking-pipelines.md for a fuller discussion of
chunking strategies (fixed-size, recursive, semantic, token-aware) and their
trade-offs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    index: int
    start_char: int
    end_char: int


def chunk_text(
    text: str,
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Split `text` into overlapping chunks of roughly `chunk_size` characters.

    Chunk boundaries snap to the nearest whitespace at or before the target
    cut point (when one exists nearby) so chunks don't split a word in half.
    `chunk_overlap` characters from the end of each chunk are repeated at
    the start of the next, so context near a boundary isn't lost entirely
    to one side.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size")

    text = text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to snap `end` to the nearest preceding whitespace, so we don't
        # cut a word in half — but only if that doesn't shrink the chunk to
        # near-nothing.
        if end < text_len:
            snap = text.rfind(" ", start, end)
            if snap != -1 and snap > start + chunk_size // 2:
                end = snap

        chunk_str = text[start:end].strip()
        if chunk_str:
            chunks.append(Chunk(text=chunk_str, index=index, start_char=start, end_char=end))
            index += 1

        if end >= text_len:
            break

        # Advance start, backing up by `chunk_overlap` so consecutive chunks
        # share some context.
        start = max(end - chunk_overlap, start + 1)

    return chunks
