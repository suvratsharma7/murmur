"""Tests for the sentence-boundary token chunker.

Validates that the chunker yields correctly on punctuation boundaries,
respects the fallback token threshold, flushes remaining text, and
invokes the on_token callback for every token.
"""
import pytest
from chunker import SentenceBoundaryChunker


async def _token_gen(tokens: list[str]):
    """Helper: yield a list of strings as an async iterator."""
    for t in tokens:
        yield t


@pytest.mark.asyncio
async def test_yields_on_period():
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["Hello", " ", "world", "."]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world."
    assert chunks[0].idx == 0


@pytest.mark.asyncio
async def test_yields_on_exclamation():
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["Wow", "!"]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    assert len(chunks) == 1
    assert chunks[0].text == "Wow!"


@pytest.mark.asyncio
async def test_yields_on_question():
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["How", " ", "are", " ", "you", "?"]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    assert len(chunks) == 1
    assert chunks[0].text == "How are you?"


@pytest.mark.asyncio
async def test_yields_on_newline():
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["Line one", "\n", "Line two", "."]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    assert len(chunks) == 2
    assert chunks[0].text == "Line one\n"
    assert chunks[1].text == "Line two."


@pytest.mark.asyncio
async def test_yields_on_semicolon():
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["First", " ", "clause", ";", " ", "second", "."]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    assert len(chunks) == 2
    assert chunks[0].text == "First clause;"
    assert chunks[1].text == " second."


@pytest.mark.asyncio
async def test_fallback_at_threshold():
    """After 20 tokens without a boundary, the chunker forces a yield."""
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    # 25 tokens without any sentence-ending punctuation
    tokens = [f"word{i} " for i in range(25)]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    # Should yield at token 20, then flush remaining 5
    assert len(chunks) == 2
    assert chunks[0].idx == 0
    assert chunks[1].idx == 1


@pytest.mark.asyncio
async def test_flushes_remaining_text():
    """Text without any boundary is flushed when the stream closes."""
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["Hello", " ", "there"]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    assert len(chunks) == 1
    assert chunks[0].text == "Hello there"


@pytest.mark.asyncio
async def test_empty_stream():
    """An empty token stream produces no chunks."""
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    chunks = [chunk async for chunk in chunker.feed(_token_gen([]))]
    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_on_token_callback():
    """The on_token callback fires for every token in the stream."""
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["Hello", " ", "world", "."]
    received = []

    async def on_token(t):
        received.append(t)

    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens), on_token=on_token)]
    assert received == ["Hello", " ", "world", "."]
    assert len(chunks) == 1


@pytest.mark.asyncio
async def test_multiple_sentences():
    """Multiple sentences produce multiple chunks with sequential indices."""
    chunker = SentenceBoundaryChunker(fallback_tokens=20)
    tokens = ["First", ".", " ", "Second", ".", " ", "Third", "."]
    chunks = [chunk async for chunk in chunker.feed(_token_gen(tokens))]
    assert len(chunks) == 3
    assert chunks[0].idx == 0
    assert chunks[1].idx == 1
    assert chunks[2].idx == 2
