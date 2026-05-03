"""Test raw content fetcher with mocked crawl4ai responses."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from crawler.raw_fetcher import fetch_raw_content, fetch_raw_readme
from crawler.models import ReadmeContent


class MockCrawlResult:
    """Mock crawl result for testing."""
    def __init__(self, success: bool, markdown: str | None = None):
        self.success = success
        self.markdown = markdown


class MockAsyncWebCrawler:
    """Mock AsyncWebCrawler for testing."""
    
    def __init__(self, return_result: MockCrawlResult | None = None):
        self.return_result = return_result or MockCrawlResult(success=False)
        self.arun_called_with = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass
    
    async def arun(self, url: str, config=None):
        # Verify config uses only_text=True
        if config is not None:
            assert config.only_text is True
        self.arun_called_with = (url, config)
        return self.return_result


@pytest.mark.asyncio
async def test_fetch_raw_content_success():
    """Test successful raw content fetch."""
    expected_content = "# README\n\nThis is a test README."
    mock_result = MockCrawlResult(success=True, markdown=expected_content)
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_content("owner", "repo", "main", "README.md")
    
    assert result == expected_content
    assert mock_crawler.arun_called_with is not None
    url, _ = mock_crawler.arun_called_with
    assert "raw.githubusercontent.com" in url
    assert "owner/repo/main/README.md" in url


@pytest.mark.asyncio
async def test_fetch_raw_content_404():
    """Test that 404 response returns None."""
    mock_result = MockCrawlResult(success=False)
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_content("owner", "repo", "main", "nonexistent.md")
    
    assert result is None


@pytest.mark.asyncio
async def test_fetch_raw_content_empty():
    """Test that empty content returns the empty string."""
    mock_result = MockCrawlResult(success=True, markdown="")
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_content("owner", "repo", "main", "empty.txt")
    
    assert result == ""


@pytest.mark.asyncio
async def test_fetch_raw_readme_priority():
    """Test README detection prioritizes README.md."""
    readme_content = "# Test README"
    mock_result = MockCrawlResult(success=True, markdown=readme_content)
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_readme("owner", "repo", "main")
    
    assert result is not None
    assert result.filename == "README.md"
    assert result.content == readme_content


@pytest.mark.asyncio
async def test_fetch_raw_readme_fallback():
    """Test README detection falls back through candidates."""
    call_count = 0
    
    async def mock_arun(url, config=None):
        nonlocal call_count
        call_count += 1
        # Simulate README.md not found, readme.md found
        if "README.md" in url:
            return MockCrawlResult(success=False)
        elif "readme.md" in url:
            return MockCrawlResult(success=True, markdown="# readme")
        return MockCrawlResult(success=False)
    
    mock_crawler = MagicMock()
    mock_crawler.arun = mock_arun
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock()
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_readme("owner", "repo", "main")
    
    assert result is not None
    assert result.filename == "readme.md"
    assert call_count == 2  # Tried README.md first, then readme.md


@pytest.mark.asyncio
async def test_fetch_raw_readme_not_found():
    """Test README returns None when no candidates found."""
    mock_result = MockCrawlResult(success=False)
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_readme("owner", "repo", "main")
    
    assert result is None


@pytest.mark.asyncio
async def test_fetch_raw_readme_with_dir_path():
    """Test README fetch with directory path."""
    mock_result = MockCrawlResult(success=True, markdown="# Content")
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        await fetch_raw_readme("owner", "repo", "main", dir_path="docs")
    
    url, _ = mock_crawler.arun_called_with
    assert "owner/repo/main/docs/README.md" in url


@pytest.mark.asyncio
async def test_fetch_raw_readme_custom_candidates():
    """Test README fetch with custom candidate list."""
    mock_result = MockCrawlResult(success=True, markdown="# Content")
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    custom_candidates = ["CUSTOM.md", "CUSTOM.rst"]
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        await fetch_raw_readme("owner", "repo", "main", candidates=custom_candidates)
    
    url, _ = mock_crawler.arun_called_with
    # Should try CUSTOM.md first
    assert "CUSTOM.md" in url or "CUSTOM.rst" in url


@pytest.mark.asyncio
async def test_fetch_raw_content_binary():
    """Test that binary content is returned as-is."""
    # Binary content should be returned as-is
    binary_content = "PK\x03\x04\x14\x00\x00\x00\x08\x00"  # ZIP header
    mock_result = MockCrawlResult(success=True, markdown=binary_content)
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_content("owner", "repo", "main", "file.zip")
    
    assert result == binary_content


@pytest.mark.asyncio
async def test_fetch_raw_readme_all_candidates_fail():
    """Test when all README candidates fail."""
    async def mock_arun(url, config=None):
        return MockCrawlResult(success=False)
    
    mock_crawler = MagicMock()
    mock_crawler.arun = mock_arun
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock()
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        result = await fetch_raw_readme("owner", "repo", "main")
    
    assert result is None


@pytest.mark.asyncio
async def test_fetch_raw_content_url_construction():
    """Test that raw URL is correctly constructed."""
    mock_result = MockCrawlResult(success=True, markdown="content")
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        await fetch_raw_content("test-owner", "test-repo", "test-ref", "path/to/file.txt")
    
    url, _ = mock_crawler.arun_called_with
    expected_url = "https://raw.githubusercontent.com/test-owner/test-repo/test-ref/path/to/file.txt"
    assert expected_url in url


@pytest.mark.asyncio
async def test_fetch_raw_readme_url_construction():
    """Test that README raw URL is correctly constructed."""
    mock_result = MockCrawlResult(success=True, markdown="content")
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.raw_fetcher.AsyncWebCrawler', return_value=mock_crawler):
        await fetch_raw_readme("test-owner", "test-repo", "test-ref")
    
    url, _ = mock_crawler.arun_called_with
    assert "raw.githubusercontent.com" in url
    assert "test-owner/test-repo/test-ref/README.md" in url
