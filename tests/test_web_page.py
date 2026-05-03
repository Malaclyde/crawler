"""Test non-GitHub web page parser."""

import pytest
from unittest.mock import AsyncMock, patch

from crawler.parsers.web_page import parse_web_page
from crawler.models import WebPageResponse


class MockCrawlResult:
    """Mock crawl result."""
    def __init__(self, markdown="", metadata=None, success=True):
        self.markdown = markdown
        self.metadata = metadata or {}
        self.success = success


class MockAsyncWebCrawler:
    """Mock AsyncWebCrawler."""
    
    def __init__(self, return_result=None):
        self.return_result = return_result or MockCrawlResult()
        self.arun_called_with = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass
    
    async def arun(self, url, config=None):
        self.arun_called_with = (url, config)
        return self.return_result


@pytest.mark.asyncio
async def test_parse_web_page_basic():
    """Test basic web page parsing."""
    expected_markdown = "# Title\n\nContent"
    mock_result = MockCrawlResult(markdown=expected_markdown, metadata={"title": "Test"})
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.parsers.web_page.AsyncWebCrawler', return_value=mock_crawler):
        result = await parse_web_page("https://example.com")
    
    assert result.url == "https://example.com"
    assert result.type == "web_page"
    assert result.markdown == expected_markdown
    assert result.metadata == {"title": "Test"}


@pytest.mark.asyncio
async def test_parse_web_page_excluded_tags():
    """Test that excluded_tags config is applied."""
    mock_result = MockCrawlResult(markdown="content")
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.parsers.web_page.AsyncWebCrawler', return_value=mock_crawler):
        await parse_web_page("https://example.com")
    
    _, config = mock_crawler.arun_called_with
    assert config.excluded_tags == ["nav", "footer", "script", "style"]


@pytest.mark.asyncio
async def test_parse_web_page_empty():
    """Test parsing with empty content."""
    mock_result = MockCrawlResult(markdown="", metadata={})
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.parsers.web_page.AsyncWebCrawler', return_value=mock_crawler):
        result = await parse_web_page("https://example.com")
    
    assert result.markdown == ""
    assert result.metadata is None


@pytest.mark.asyncio
async def test_parse_web_page_no_metadata():
    """Test parsing with no metadata."""
    mock_result = MockCrawlResult(markdown="content", metadata=None)
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.parsers.web_page.AsyncWebCrawler', return_value=mock_crawler):
        result = await parse_web_page("https://example.com")
    
    assert result.metadata is None


@pytest.mark.asyncio
async def test_parse_web_page_serialization():
    """Test that response serializes correctly."""
    mock_result = MockCrawlResult(
        markdown="# Test",
        metadata={"key": "value"}
    )
    mock_crawler = MockAsyncWebCrawler(return_result=mock_result)
    
    with patch('crawler.parsers.web_page.AsyncWebCrawler', return_value=mock_crawler):
        result = await parse_web_page("https://example.com")
    
    # Test JSON serialization
    import json
    data = json.loads(result.model_dump_json())
    assert data["url"] == "https://example.com"
    assert data["type"] == "web_page"
    assert data["markdown"] == "# Test"
    assert data["metadata"] == {"key": "value"}
