"""Main orchestrator for the GitHub-aware web crawler."""

import json
import logging
import sys
from urllib.parse import quote

import httpx

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter

from .models import CrawlResponse, WebPageResponse
from .url_classifier import classify_url, URLType
from .parsers.web_page import parse_web_page
from .parsers.repo import parse_repo_page
from .parsers.file import parse_file_page
from .parsers.issues import parse_issues_page
from .parsers.pulls import parse_pulls_page
from .parsers.releases import parse_releases_page
from .parsers.wiki import parse_wiki_page
from .parsers.commits import parse_commits_page
from .parsers.fallback import parse_fallback
from .raw_http import fetch_raw, check_url
from .safety import (
    check_binary, check_binary_for_raw_url, clip_content,
    MAX_CRAWL_BYTES, MAX_FETCH_BYTES, MAX_DOWNLOAD_BYTES,
)

logger = logging.getLogger(__name__)


def _build_run_config(
    query: str | None = None,
    selector: str | None = None,
    cache: bool = False,
    **overrides,
) -> CrawlerRunConfig:
    """Build CrawlerRunConfig with optional BM25 filter, CSS selector, and cache."""
    kwargs = dict(verbose=False)

    if selector:
        kwargs["css_selector"] = selector

    if cache:
        kwargs["cache_mode"] = CacheMode.ENABLED

    if query:
        bm25 = BM25ContentFilter(user_query=query, bm25_threshold=1.0)
        kwargs["markdown_generator"] = DefaultMarkdownGenerator(content_filter=bm25)

    kwargs.update(overrides)
    return CrawlerRunConfig(**kwargs)


def _apply_fit_markdown(response, query: str | None) -> None:
    """Replace response.markdown with fit_markdown if query was used."""
    if not query:
        return
    if hasattr(response, "markdown") and hasattr(response, "metadata"):
        # fit_markdown is on the result, not on the response — handled in crawl()
        pass


async def crawl(
    url: str,
    mode: str = "crawl",
    force_large: bool = False,
    force_binary: bool = False,
    skip_preformatting: bool = False,
    query: str | None = None,
    selector: str | None = None,
    cache: bool = False,
    max_depth: int = 2,
    max_pages: int = 50,
    confidence: float = 0.7,
    strategy: str = "statistical",
) -> CrawlResponse | str | dict | list:
    if mode == "fetch":
        await check_binary(url, force_binary=force_binary)
        max_bytes = None if force_large else MAX_FETCH_BYTES
        return await fetch_raw(url, max_bytes=max_bytes)

    if mode == "download":
        raise ValueError("Use download() function for download mode")

    if mode == "site":
        return await crawl_site(
            url, query=query, selector=selector, cache=cache,
            max_depth=max_depth, max_pages=max_pages, force_large=force_large,
        )

    if mode == "research":
        if not query:
            raise ValueError("research mode requires --query")
        return await crawl_research(
            url, query=query, cache=cache, max_pages=max_pages,
            confidence=confidence, strategy=strategy, selector=selector,
        )

    # Crawl mode (default)
    classification = classify_url(url)

    # PDF auto-detection — must happen before binary check
    if url.lower().endswith(".pdf"):
        return await _crawl_pdf(url, force_large=force_large)

    # Binary check before crawl4ai
    if classification.url_type == URLType.WEB_PAGE:
        await check_binary(url, force_binary=force_binary)
    elif classification.url_type == URLType.GH_FILE and classification.owner and classification.repo and classification.ref and classification.path:
        await check_binary_for_raw_url(
            classification.owner, classification.repo,
            classification.ref, classification.path,
            force_binary=force_binary,
        )

    try:
        if skip_preformatting:
            response = await parse_web_page(url, query=query, selector=selector, cache=cache)
        elif classification.url_type == URLType.WEB_PAGE:
            response = await parse_web_page(url, query=query, selector=selector, cache=cache)
        elif classification.url_type in [URLType.GH_REPO, URLType.GH_DIRECTORY]:
            response = await parse_repo_page(url)
        elif classification.url_type == URLType.GH_FILE:
            response = await parse_file_page(url, force_large=force_large, force_binary=force_binary)
        elif classification.url_type in [URLType.GH_ISSUES, URLType.GH_ISSUE]:
            response = await parse_issues_page(url)
        elif classification.url_type in [URLType.GH_PULLS, URLType.GH_PULL]:
            response = await parse_pulls_page(url)
        elif classification.url_type == URLType.GH_RELEASES:
            response = await parse_releases_page(url)
        elif classification.url_type in [URLType.GH_WIKI, URLType.GH_WIKI_PAGE]:
            response = await parse_wiki_page(url)
        elif classification.url_type in [URLType.GH_COMMITS, URLType.GH_COMMIT]:
            response = await parse_commits_page(url)
        else:
            response = await parse_fallback(url)
    except Exception as e:
        return WebPageResponse(
            url=url, type="web_page", markdown="",
            metadata={"error": str(e)},
        )

    if hasattr(response, "markdown") and response.markdown:
        response.markdown = clip_content(response.markdown, MAX_CRAWL_BYTES, force_large)
    if hasattr(response, "content") and response.content:
        response.content = clip_content(response.content, MAX_CRAWL_BYTES, force_large)

    return response


async def _crawl_pdf(url: str, force_large: bool = False) -> WebPageResponse:
    """Parse a PDF URL and extract text content."""
    from crawl4ai.processors.pdf import PDFCrawlerStrategy, PDFContentScrapingStrategy

    pdf_crawler = PDFCrawlerStrategy()
    pdf_scraper = PDFContentScrapingStrategy(extract_images=False)
    run_config = CrawlerRunConfig(scraping_strategy=pdf_scraper, verbose=False)

    async with AsyncWebCrawler(crawler_strategy=pdf_crawler) as crawler:
        result = await crawler.arun(url=url, config=run_config)

    # Extract markdown — crawl4ai may set success=False even with valid content
    markdown = ""
    if hasattr(result.markdown, "raw_markdown"):
        markdown = result.markdown.raw_markdown or ""
    elif result.markdown:
        markdown = result.markdown if isinstance(result.markdown, str) else ""

    if not markdown.strip():
        return WebPageResponse(
            url=url, type="web_page", markdown="",
            metadata={"error": result.error_message or "PDF parsing failed"},
        )

    if not force_large:
        markdown = clip_content(markdown, MAX_CRAWL_BYTES, force_large)

    return WebPageResponse(
        url=url,
        type="web_page",
        markdown=markdown,
        metadata=result.metadata if result.metadata else None,
    )


async def crawl_site(
    url: str,
    query: str | None = None,
    selector: str | None = None,
    cache: bool = False,
    max_depth: int = 2,
    max_pages: int = 50,
    force_large: bool = False,
) -> dict:
    """Deep crawl a site using BFS strategy, return wrapper object with results."""
    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
    from crawl4ai.deep_crawling.filters import FilterChain, ContentTypeFilter
    from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

    filters = [ContentTypeFilter(allowed_types=["text/html"])]

    scorer = None
    if query:
        scorer = KeywordRelevanceScorer(keywords=query.split(), weight=0.7)

    strategy = BFSDeepCrawlStrategy(
        max_depth=max_depth,
        max_pages=max_pages,
        include_external=False,
        filter_chain=FilterChain(filters) if filters else None,
        url_scorer=scorer,
    )

    run_config = _build_run_config(
        query=query,
        selector=selector,
        cache=cache,
        deep_crawl_strategy=strategy,
        stream=True,
    )

    pages = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(url, config=run_config):
            if result.success:
                md = result.markdown
                if query and hasattr(md, "fit_markdown") and md.fit_markdown:
                    content = md.fit_markdown
                else:
                    content = md.raw_markdown if hasattr(md, "raw_markdown") else str(md)

                content = clip_content(content, MAX_CRAWL_BYTES, force_large)
                pages.append({
                    "url": result.url,
                    "depth": result.metadata.get("depth", 0) if result.metadata else 0,
                    "score": result.metadata.get("score", 0) if result.metadata else 0,
                    "markdown": content,
                })

    return {"total": len(pages), "pages": pages}


async def crawl_research(
    url: str,
    query: str,
    cache: bool = False,
    max_pages: int = 30,
    confidence: float = 0.7,
    strategy: str = "statistical",
    selector: str | None = None,
) -> dict:
    """Adaptive crawl — stop when confidence threshold is met."""
    from crawl4ai import AdaptiveCrawler, AdaptiveConfig

    config = AdaptiveConfig(
        confidence_threshold=confidence,
        max_pages=max_pages,
        top_k_links=5,
        strategy=strategy,
        n_query_variations=0,
    )

    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler, config)

        try:
            result = await adaptive.digest(start_url=url, query=query)
        except ImportError as e:
            if "sentence_transformers" in str(e):
                return {
                    "mode": "research",
                    "error": (
                        "Embedding strategy requires sentence-transformers.\n"
                        "Install: pip install 'crawler[research]'\n"
                        "Or use: --strategy statistical"
                    ),
                    "query": query,
                }
            raise

        sources_data = adaptive.get_relevant_content(top_k=5)

        return {
            "mode": "research",
            "query": query,
            "strategy": strategy,
            "confidence": round(result.metrics.get("confidence", 0), 3) if result.metrics else 0,
            "pages_crawled": result.metrics.get("pages_crawled", 0) if result.metrics else 0,
            "sources": [
                {
                    "url": s["url"],
                    "score": round(s.get("score", 0), 3),
                    "content": s.get("content", ""),
                }
                for s in sources_data
            ],
        }


async def download(url: str, output_path: str, force_large: bool = False, force_binary: bool = False) -> None:
    from .github_url import build_raw_url

    classification = classify_url(url)
    download_url = url

    if classification.url_type == URLType.GH_FILE and classification.owner and classification.repo and classification.ref:
        try:
            download_url = build_raw_url(
                classification.owner, classification.repo,
                classification.ref, classification.path
            )
            logger.info("Translated blob URL to raw URL: %s", download_url)
        except Exception:
            pass

    if not force_large:
        ct, cl = await check_url(download_url)
        if cl and cl > MAX_DOWNLOAD_BYTES:
            logger.error("File too large: %d bytes", cl)
            print(
                f"Error: File is {cl} bytes ({cl/1024/1024:.1f} MB), "
                f"exceeds {MAX_DOWNLOAD_BYTES/1024/1024:.0f} MB limit.\n"
                f"Use --force-large to download the full file.",
                file=sys.stderr,
            )
            sys.exit(1)

    async with httpx.AsyncClient() as client:
        async with client.stream("GET", download_url, follow_redirects=True, timeout=120) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)

    logger.info("Saved to %s", output_path)
    print(f"Saved to {output_path}", file=sys.stderr)
