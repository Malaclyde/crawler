"""Tests for the raw HTTP client."""

import pytest
from unittest.mock import patch, AsyncMock

from crawler.raw_http import is_binary_url, check_url, fetch_raw, _guess_type_from_extension


class TestIsBinaryUrl:
    def test_text_extension(self):
        assert is_binary_url("https://example.com/file.py") is False
        assert is_binary_url("https://example.com/file.md") is False
        assert is_binary_url("https://example.com/file.txt") is False
        assert is_binary_url("https://example.com/file.json") is False
        assert is_binary_url("https://example.com/file.html") is False

    def test_binary_extension(self):
        assert is_binary_url("https://example.com/file.png") is True
        assert is_binary_url("https://example.com/file.jpg") is True
        assert is_binary_url("https://example.com/file.zip") is True
        assert is_binary_url("https://example.com/file.pdf") is True
        assert is_binary_url("https://example.com/file.exe") is True

    def test_no_extension(self):
        assert is_binary_url("https://example.com") is False

    def test_content_type_text(self):
        assert is_binary_url("https://example.com/f", "text/html") is False
        assert is_binary_url("https://example.com/f", "text/plain") is False
        assert is_binary_url("https://example.com/f", "application/json") is False

    def test_content_type_binary(self):
        assert is_binary_url("https://example.com/f", "application/octet-stream") is True
        assert is_binary_url("https://example.com/f", "application/x-binary") is True

    def test_extension_overrides_content_type(self):
        # Extension check happens first, so it takes priority
        result = is_binary_url("https://example.com/file.png")
        assert result is True  # Extension wins


class TestGuessTypeFromExtension:
    def test_text_extensions(self):
        assert _guess_type_from_extension("https://example.com/file.py") == "text/plain"
        assert _guess_type_from_extension("https://example.com/file.md") == "text/plain"
        assert _guess_type_from_extension("https://example.com/file.txt") == "text/plain"

    def test_binary_extensions(self):
        assert _guess_type_from_extension("https://example.com/file.png") == "application/octet-stream"
        assert _guess_type_from_extension("https://example.com/file.jpg") == "application/octet-stream"
        assert _guess_type_from_extension("https://example.com/file.zip") == "application/octet-stream"

    def test_unknown_extension(self):
        assert _guess_type_from_extension("https://example.com/file.xyz") is None
        assert _guess_type_from_extension("https://example.com") is None


@pytest.mark.asyncio
async def test_fetch_raw_text():
    """Test fetching a known text file."""
    content = await fetch_raw(
        "https://raw.githubusercontent.com/unclecode/crawl4ai/main/.env.txt"
    )
    assert content is not None
    assert len(content) > 0
    assert "GROQ_API_KEY" in content


@pytest.mark.asyncio
async def test_fetch_raw_clip():
    """Test that content is clipped when exceeding max_bytes."""
    content = await fetch_raw(
        "https://raw.githubusercontent.com/unclecode/crawl4ai/main/crawl4ai/adaptive_crawler%20copy.py",
        max_bytes=100,
    )
    assert "use --force-large to download the full file" in content


@pytest.mark.asyncio
async def test_fetch_raw_no_clip():
    """Test that small files are not clipped."""
    content = await fetch_raw(
        "https://raw.githubusercontent.com/unclecode/crawl4ai/main/.env.txt",
        max_bytes=50000,
    )
    assert "use --force-large to download the full file" not in content


@pytest.mark.asyncio
async def test_check_url():
    """Test HEAD request returns type and size."""
    ct, cl = await check_url("https://raw.githubusercontent.com/unclecode/crawl4ai/main/.env.txt")
    assert ct is not None
    assert "text/plain" in ct
    assert cl is not None
    assert cl > 0
