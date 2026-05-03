"""Parser for GitHub repo and directory pages."""

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from ..models import GitHubRepoResponse, FileEntry, RepoMetadata
from ..raw_fetcher import fetch_raw_readme
from ..repo_metadata import extract_repo_metadata, fetch_repo_metadata
from ..url_classifier import classify_url, URLType


async def parse_repo_page(url: str) -> GitHubRepoResponse:
    """
    Parse a GitHub repo root or directory page.
    
    Args:
        url: GitHub repo/directory URL
        
    Returns:
        GitHubRepoResponse with repo metadata and file listing
    """
    classification = classify_url(url)
    ref = classification.ref or "main"
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            excluded_tags=["header", "nav", "footer"],
            exclude_social_media_links=True,
        )
        result = await crawler.arun(url, config=config)
        
        # For repo root, extract metadata directly from the page
        # For directories, fetch from repo root to get full sidebar stats
        if classification.url_type == URLType.GH_DIRECTORY and classification.owner and classification.repo:
            repo_meta = await fetch_repo_metadata(
                classification.owner,
                classification.repo,
                ref=ref,
            )
        elif classification.owner and classification.repo:
            repo_meta = await extract_repo_metadata(
                result,
                classification.owner,
                classification.repo,
                ref=ref,
            )
        else:
            repo_meta = None
        
        # Extract file listing from links
        files = []
        internal_links = result.links.get("internal", []) if result.links else []
        
        for link in internal_links:
            href = link.get("href", "")
            text = link.get("text", "")
            
            # Check if it's a file or directory
            if "/blob/" in href:
                file_type = "file"
            elif "/tree/" in href:
                file_type = "dir"
            else:
                continue
            
            # Only include direct children for current path
            files.append(FileEntry(
                name=text or href.split("/")[-1],
                href=href,
                type=file_type,
            ))
        
        # Try to fetch README
        readme = None
        if classification.owner and classification.repo:
            readme = await fetch_raw_readme(
                classification.owner,
                classification.repo,
                ref,
                classification.path or ""
            )
        
        return GitHubRepoResponse(
            url=url,
            type="github_repo" if classification.url_type == URLType.GH_REPO else "github_directory",
            repo=repo_meta,
            readme=readme,
            files=files,
            pagination=None,
        )
