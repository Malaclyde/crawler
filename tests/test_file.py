"""Test file page parser."""

import pytest
from unittest.mock import patch

from crawler.parsers.file import _extract_size_and_lines


@pytest.mark.parametrize(
    "html,expected_size,expected_lines",
    [
        (
            '<div data-testid="blob-size"><span>4 lines (4 loc) · 139 Bytes</span></div>',
            "139 Bytes",
            4,
        ),
        (
            '<div data-testid="blob-size"><span>1 lines (1 loc) · 23 Bytes</span></div>',
            "23 Bytes",
            1,
        ),
        (
            '<div data-testid="blob-size"><span>500 lines (450 loc) · 12.5 KB</span></div>',
            "12.5 KB",
            500,
        ),
        (
            '<div data-testid="blob-size"><span>1,234 lines (1,200 loc) · 45.2 KB</span></div>',
            "45.2 KB",
            1234,
        ),
        ("<div>no blob info here</div>", None, None),
        ("", None, None),
    ],
)
def test_extract_size_and_lines(html, expected_size, expected_lines):
    """Test extracting size and line count from blob page HTML."""
    size, lines = _extract_size_and_lines(html)
    assert size == expected_size
    assert lines == expected_lines
