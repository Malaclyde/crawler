"""Fallback parser for generic GitHub pages."""

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from ..models import GitHubSecondaryResponse, RepoMetadata
from ..repo_metadata import extract_repo_metadata
from ..url_classifier import classify_url


async def parse_fallback(url: str) -> GitHubSecondaryResponse:
    """
    Parse any GitHub page not covered by specific parsers.
    
    Handles: user profiles, orgs, gists, actions, discussions, search, settings, etc.
    """
    classification = classify_url(url)
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            excluded_tags=["header", "nav", "footer", "aside"],
            excluded_selector=".js-notification-shelf, .js-header-wrapper, .footer, .Header",
            exclude_social_media_links=True,
            remove_forms=True,
        )
        result = await crawler.arun(url, config=config)
        
        # Try to extract repo metadata if applicable
        repo_meta = None
        if classification.owner and classification.repo:
            repo_meta = await extract_repo_metadata(
                result,
                classification.owner,
                classification.repo,
                ref=classification.ref or "main",
            )
        
        return GitHubSecondaryResponse(
            url=url,
            type="github_page",
            repo=repo_meta,
            markdown=result.markdown or "",
            metadata=result.metadata if result.metadata else None,
        )
