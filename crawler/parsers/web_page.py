"""Parser for non-GitHub web pages."""

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter

from ..models import WebPageResponse


async def parse_web_page(
    url: str,
    query: str | None = None,
    selector: str | None = None,
    cache: bool = False,
) -> WebPageResponse:
    """
    Parse a non-GitHub web page and extract markdown.

    Args:
        url: URL to parse
        query: Optional BM25 query to filter relevant content
        selector: Optional CSS selector to scope crawling
        cache: Enable crawl4ai cache

    Returns:
        WebPageResponse with markdown and metadata
    """
    kwargs = dict(
        verbose=False,
        excluded_tags=["nav", "footer", "script", "style"],
    )
    if selector:
        kwargs["css_selector"] = selector
    if cache:
        kwargs["cache_mode"] = CacheMode.ENABLED
    if query:
        bm25 = BM25ContentFilter(user_query=query, bm25_threshold=1.0)
        kwargs["markdown_generator"] = DefaultMarkdownGenerator(content_filter=bm25)

    config = CrawlerRunConfig(**kwargs)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=config)

    # Extract markdown: prefer fit_markdown when query is set
    markdown = ""
    if query and hasattr(result.markdown, "fit_markdown") and result.markdown.fit_markdown:
        markdown = result.markdown.fit_markdown
    elif hasattr(result.markdown, "raw_markdown"):
        markdown = result.markdown.raw_markdown
    else:
        markdown = result.markdown or ""

    return WebPageResponse(
        url=url,
        type="web_page",
        markdown=markdown,
        metadata=result.metadata if result.metadata else None,
    )
