"""Parser for GitHub wiki pages."""

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from ..models import GitHubSecondaryResponse, RepoMetadata
from ..repo_metadata import extract_repo_metadata
from ..url_classifier import classify_url


async def parse_wiki_page(url: str) -> GitHubSecondaryResponse:
    """Parse GitHub wiki page."""
    classification = classify_url(url)
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            excluded_tags=["header", "nav", "footer"],
        )
        result = await crawler.arun(url, config=config)
        
        repo_meta = None
        if classification.owner and classification.repo:
            repo_meta = await extract_repo_metadata(
                result,
                classification.owner,
                classification.repo,
                ref=classification.ref or "main",
            )
        
        page_type = "github_wiki_page" if "/wiki/" in url and len(url.split("/wiki/")[-1].split("/")) > 1 else "github_wiki"
        
        return GitHubSecondaryResponse(
            url=url,
            type=page_type,
            repo=repo_meta,
            markdown=result.markdown or "",
            metadata=result.metadata if result.metadata else None,
        )
