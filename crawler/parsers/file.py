"""Parser for GitHub file (blob) pages."""

import re

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from ..models import GitHubFileResponse, FileMetadata
from ..raw_fetcher import fetch_raw_content
from ..repo_metadata import fetch_repo_metadata
from ..github_url import build_raw_url
from ..url_classifier import classify_url
from ..safety import check_binary_for_raw_url, clip_content, MAX_CRAWL_BYTES


def _extract_size_and_lines(html: str) -> tuple[str | None, int | None]:
    """
    Extract size and line count from the blob page HTML.
    
    Pattern: <div data-testid="blob-size">...<span>4 lines (4 loc) · 139 Bytes</span></div>
    """
    match = re.search(
        r'<span[^>]*>([\d,.]+)\s*lines?\s*\([\d,.]+\s*loc\)?\s*·\s*([\d,.]+\s*[A-Za-z]+)</span>',
        html,
        re.IGNORECASE,
    )
    if match:
        lines_str = match.group(1).replace(",", "")
        try:
            lines = int(lines_str)
        except ValueError:
            lines = None
        size = match.group(2).strip()
        return size, lines

    return None, None


async def parse_file_page(url: str, force_large: bool = False, force_binary: bool = False) -> GitHubFileResponse:
    """
    Parse a GitHub file (blob) page.
    
    Args:
        url: GitHub file URL
        force_large: Bypass size limit clipping
        force_binary: Bypass binary detection
        
    Returns:
        GitHubFileResponse with file content and metadata
    """
    classification = classify_url(url)
    ref = classification.ref or "main"

    # Binary check on raw URL before downloading
    if classification.owner and classification.repo and classification.path:
        await check_binary_for_raw_url(
            classification.owner, classification.repo,
            ref, classification.path,
            force_binary=force_binary,
        )

    # Crawl the blob page to extract file metadata (size, lines)
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            excluded_tags=["header", "nav", "footer"],
        )
        result = await crawler.arun(url, config=config)
        size, lines = _extract_size_and_lines(result.html or "")

    # Fetch raw content
    content = None
    raw_url = None
    if classification.owner and classification.repo and classification.path:
        raw_url = build_raw_url(
            classification.owner,
            classification.repo,
            ref,
            classification.path
        )
        content = await fetch_raw_content(
            classification.owner,
            classification.repo,
            ref,
            classification.path
        )
        if content:
            content = clip_content(content, MAX_CRAWL_BYTES, force_large)

    # Fetch repo metadata from the repo root (file pages don't have full sidebar stats)
    if classification.owner and classification.repo:
        repo_meta = await fetch_repo_metadata(
            classification.owner,
            classification.repo,
            ref=ref,
        )
    else:
        repo_meta = None

    file_meta = FileMetadata(
        name=classification.path.split("/")[-1] if classification.path else "",
        path=classification.path or "",
        size=size,
        lines=lines,
    )

    return GitHubFileResponse(
        url=url,
        type="github_file",
        repo=repo_meta,
        file=file_meta,
        raw_url=raw_url or "",
        content=content or "",
    )
