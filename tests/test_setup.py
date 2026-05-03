"""Test that crawl4ai imports and AsyncWebCrawler can be instantiated."""

import pytest
from crawl4ai import AsyncWebCrawler


def test_crawl4ai_import():
    """Verify crawl4ai can be imported."""
    from crawl4ai import __version__
    assert __version__ is not None


def test_async_web_crawler_instantiation():
    """Verify AsyncWebCrawler can be instantiated."""
    crawler = AsyncWebCrawler()
    assert crawler is not None
    assert isinstance(crawler, AsyncWebCrawler)


@pytest.mark.asyncio
async def test_async_web_crawler_context_manager():
    """Verify AsyncWebCrawler works as a context manager."""
    async with AsyncWebCrawler() as crawler:
        assert crawler is not None
