"""Sentence-boundary token chunker for the streaming voice pipeline.

Voice TTFB-audio is dominated by how fast the first sentence reaches TTS.
Yielding on sentence boundaries produces natural-sounding speech.
The token fallback (default 20) prevents indefinite stalls on long
preambles without punctuation.

Tune the fallback via MURMUR_CHUNK_FALLBACK_TOKENS env var.
"""
from dataclasses import dataclass
from typing import AsyncIterator, Awaitable, Callable

from config import settings

# Punctuation that signals a natural sentence boundary for TTS prosody
SENTENCE_BOUNDARIES = frozenset(".!?\n;:")


@dataclass
class Chunk:
    """A text chunk ready for TTS synthesis."""

    idx: int
    text: str


class SentenceBoundaryChunker:
    """Accumulates LLM tokens and yields chunks at sentence boundaries.

    The chunker reads the LLM token stream and yields a Chunk whenever:
    1. The accumulated text ends with '.', '!', '?', '\\n', ';', or ':'.
    2. The accumulated text reaches fallback_tokens without hitting (1).
    3. The token stream closes (flush final buffer).
    """

    def __init__(self, fallback_tokens: int | None = None):
        self.fallback_tokens = fallback_tokens or settings.chunk_fallback_tokens

    async def feed(
        self,
        token_stream: AsyncIterator[str],
        on_token: Callable[[str], Awaitable[None]] | None = None,
    ) -> AsyncIterator[Chunk]:
        """Consume tokens and yield chunks at sentence boundaries.

        Args:
            token_stream: Async iterator of token strings from the LLM.
            on_token: Optional callback invoked for each token as it arrives,
                      enabling real-time token-by-token streaming to the client
                      while still accumulating chunks for TTS.

        Yields:
            Chunk objects with sequential idx and accumulated text.
        """
        buffer = ""
        token_count = 0
        chunk_idx = 0

        async for token in token_stream:
            buffer += token
            token_count += 1

            if on_token is not None:
                await on_token(token)

            # Check for sentence boundary at end of accumulated text
            # Use raw last char (not stripped) so \n is detected correctly
            if buffer and buffer[-1] in SENTENCE_BOUNDARIES:
                yield Chunk(idx=chunk_idx, text=buffer)
                buffer = ""
                token_count = 0
                chunk_idx += 1
            # Fallback: yield after N tokens to prevent indefinite stalls
            elif token_count >= self.fallback_tokens:
                yield Chunk(idx=chunk_idx, text=buffer)
                buffer = ""
                token_count = 0
                chunk_idx += 1

        # Flush any remaining text after stream closes
        if buffer.strip():
            yield Chunk(idx=chunk_idx, text=buffer)
