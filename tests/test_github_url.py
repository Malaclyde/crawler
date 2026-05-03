"""Test GitHub URL utilities with parametrized tests."""

import pytest

from crawler.github_url import (
    build_github_dir_url,
    build_github_file_url,
    build_raw_url,
    extract_blob_path,
    extract_tree_path,
)


@pytest.mark.parametrize(
    "owner,repo,ref,filepath,expected",
    [
        ("unclecode", "crawl4ai", "main", "README.md",
         "https://raw.githubusercontent.com/unclecode/crawl4ai/main/README.md"),
        ("unclecode", "crawl4ai", "main", ".env.txt",
         "https://raw.githubusercontent.com/unclecode/crawl4ai/main/.env.txt"),
        ("owner", "repo", "main", "src/crawler.py",
         "https://raw.githubusercontent.com/owner/repo/main/src/crawler.py"),
        ("test", "project", "v1.0.0", "path/to/file.txt",
         "https://raw.githubusercontent.com/test/project/v1.0.0/path/to/file.txt"),
    ]
)
def test_build_raw_url(owner, repo, ref, filepath, expected):
    """Test build_raw_url produces correct raw.githubusercontent.com URLs."""
    result = build_raw_url(owner, repo, ref, filepath)
    assert result == expected


def test_build_raw_url_known_pattern():
    """Verify build_raw_url produces working URLs for known pattern."""
    # From plan: github.com/unclecode/crawl4ai/blob/main/.env.txt
    # Should produce: raw.githubusercontent.com/unclecode/crawl4ai/main/.env.txt
    result = build_raw_url("unclecode", "crawl4ai", "main", ".env.txt")
    expected = "https://raw.githubusercontent.com/unclecode/crawl4ai/main/.env.txt"
    assert result == expected
    assert "raw.githubusercontent.com" in result
    assert "unclecode/crawl4ai/main/.env.txt" in result


@pytest.mark.parametrize(
    "url,expected_ref,expected_path",
    [
        ("https://github.com/unclecode/crawl4ai/blob/main/README.md", "main", "README.md"),
        ("https://github.com/unclecode/crawl4ai/blob/main/src/crawler.py", "main", "src/crawler.py"),
        ("https://github.com/owner/repo/blob/dev/path/to/file.txt", "dev", "path/to/file.txt"),
        ("https://github.com/test/project/blob/feature-branch/file.py", "feature-branch", "file.py"),
    ]
)
def test_extract_blob_path(url, expected_ref, expected_path):
    """Test extract_blob_path correctly parses blob URLs."""
    ref, path = extract_blob_path(url)
    assert ref == expected_ref
    assert path == expected_path


def test_extract_blob_path_invalid():
    """Test extract_blob_path raises on invalid URLs."""
    with pytest.raises(ValueError):
        extract_blob_path("https://github.com/owner/repo/tree/main/path")
    
    with pytest.raises(ValueError):
        extract_blob_path("https://example.com")


@pytest.mark.parametrize(
    "url,expected_ref,expected_path",
    [
        ("https://github.com/unclecode/crawl4ai/tree/main", "main", ""),
        ("https://github.com/unclecode/crawl4ai/tree/main/src", "main", "src"),
        ("https://github.com/unclecode/crawl4ai/tree/main/tests/fixtures", "main", "tests/fixtures"),
        ("https://github.com/owner/repo/tree/dev/path/to/dir", "dev", "path/to/dir"),
    ]
)
def test_extract_tree_path(url, expected_ref, expected_path):
    """Test extract_tree_path correctly parses tree URLs."""
    ref, path = extract_tree_path(url)
    assert ref == expected_ref
    assert path == expected_path


def test_extract_tree_path_invalid():
    """Test extract_tree_path raises on invalid URLs."""
    with pytest.raises(ValueError):
        extract_tree_path("https://github.com/owner/repo/blob/main/path")
    
    with pytest.raises(ValueError):
        extract_tree_path("https://example.com")


@pytest.mark.parametrize(
    "owner,repo,ref,path,expected",
    [
        ("unclecode", "crawl4ai", "main", "README.md",
         "https://github.com/unclecode/crawl4ai/blob/main/README.md"),
        ("owner", "repo", "main", "src/file.py",
         "https://github.com/owner/repo/blob/main/src/file.py"),
        ("test", "project", "v1.0", "path/to/file.txt",
         "https://github.com/test/project/blob/v1.0/path/to/file.txt"),
    ]
)
def test_build_github_file_url(owner, repo, ref, path, expected):
    """Test build_github_file_url produces correct GitHub blob URLs."""
    result = build_github_file_url(owner, repo, ref, path)
    assert result == expected


@pytest.mark.parametrize(
    "owner,repo,ref,path,expected",
    [
        ("unclecode", "crawl4ai", "main", "src",
         "https://github.com/unclecode/crawl4ai/tree/main/src"),
        ("owner", "repo", "main", "tests/fixtures",
         "https://github.com/owner/repo/tree/main/tests/fixtures"),
        ("test", "project", "dev", "path/to/dir",
         "https://github.com/test/project/tree/dev/path/to/dir"),
    ]
)
def test_build_github_dir_url(owner, repo, ref, path, expected):
    """Test build_github_dir_url produces correct GitHub tree URLs."""
    result = build_github_dir_url(owner, repo, ref, path)
    assert result == expected


def test_round_trip_blob():
    """Test that blob URL extraction and building round-trips correctly."""
    original_url = "https://github.com/owner/repo/blob/main/path/to/file.py"
    ref, path = extract_blob_path(original_url)
    rebuilt_url = build_github_file_url("owner", "repo", ref, path)
    assert rebuilt_url == original_url


def test_round_trip_tree():
    """Test that tree URL extraction and building round-trips correctly."""
    original_url = "https://github.com/owner/repo/tree/main/path/to/dir"
    ref, path = extract_tree_path(original_url)
    rebuilt_url = build_github_dir_url("owner", "repo", ref, path)
    assert rebuilt_url == original_url


def test_raw_url_format():
    """Test that raw URLs follow the correct format."""
    url = build_raw_url("owner", "repo", "main", "file.txt")
    assert url.startswith("https://raw.githubusercontent.com/")
    assert "/owner/repo/main/file.txt" in url
