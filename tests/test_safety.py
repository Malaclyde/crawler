"""Tests for safety check functions."""

import pytest

from crawler.safety import clip_content, SIZE_CLIP_WARNING


class TestClipContent:
    def test_under_limit(self):
        content = "short text"
        result = clip_content(content, max_bytes=100)
        assert result == content

    def test_over_limit(self):
        content = "x" * 200
        result = clip_content(content, max_bytes=50)
        assert len(result) < 200
        assert "use --force-large" in result

    def test_force_large(self):
        content = "x" * 200
        result = clip_content(content, max_bytes=50, force_large=True)
        assert result == content
        assert len(result) == 200

    def test_exact_boundary(self):
        content = "x" * 100
        result = clip_content(content, max_bytes=100)
        assert result == content
        assert "use --force-large" not in result

    def test_one_byte_over(self):
        content = "x" * 101
        result = clip_content(content, max_bytes=100)
        assert "use --force-large" in result

    def test_empty_string(self):
        result = clip_content("", max_bytes=100)
        assert result == ""

    def test_warning_message_format(self):
        content = "x" * 200
        result = clip_content(content, max_bytes=50)
        warning = SIZE_CLIP_WARNING.format(limit=50)
        assert result.endswith(warning)
