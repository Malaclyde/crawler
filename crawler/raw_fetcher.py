"""Fetch raw content from raw.githubusercontent.com using crawl4ai."""

import re

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from .models import ReadmeContent


async def fetch_raw_content(owner: str, repo: str, ref: str, filepath: str) -> str | None:
    """
    Fetch raw file content from raw.githubusercontent.com.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch/tag/commit ref
        filepath: Path to file in repo
        
    Returns:
        Raw file content or None if not found
    """
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{filepath}"
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(only_text=True)
        result = await crawler.arun(raw_url, config=config)
        
        if result.success:
            return result.markdown
    return None


async def fetch_raw_license(
    owner: str,
    repo: str,
    ref: str,
    candidates: list[str] | None = None,
) -> str | None:
    """
    Fetch license name from the first line of a LICENSE file.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch/tag/commit ref
        candidates: List of license filename candidates to try
                   (default: LICENSE, LICENSE.md, LICENSE.txt, license, license.md)
                   
    Returns:
        License name (first line of the file) or None if not found
    """
    if candidates is None:
        candidates = ["LICENSE", "LICENSE.md", "LICENSE.txt", "license", "license.md"]
    
    async with AsyncWebCrawler() as crawler:
        for candidate in candidates:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{candidate}"
            
            config = CrawlerRunConfig(only_text=True)
            result = await crawler.arun(raw_url, config=config)
            
            if result.success and result.markdown:
                content = result.markdown.strip()
                # Strip markdown code fences that crawl4ai may add
                if content.startswith("```"):
                    content = re.sub(r'^```\w*\n?', '', content)
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                first_line = content.split("\n")[0].strip()
                if first_line:
                    return first_line.lstrip("#").strip()
    
    return None


async def fetch_raw_readme(
    owner: str,
    repo: str,
    ref: str,
    dir_path: str = "",
    candidates: list[str] | None = None,
) -> ReadmeContent | None:
    """
    Fetch README content by trying multiple candidate filenames.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch/tag/commit ref
        dir_path: Directory path within repo (default: "")
        candidates: List of README filename candidates to try
                   (default: README.md, readme.md, README.rst, README.txt, README)
                   
    Returns:
        ReadmeContent with filename and content, or None if not found
    """
    if candidates is None:
        candidates = ["README.md", "readme.md", "README.rst", "README.txt", "README"]
    
    # Build path with directory prefix if provided
    base_path = f"{dir_path}/" if dir_path else ""
    
    async with AsyncWebCrawler() as crawler:
        for candidate in candidates:
            filepath = f"{base_path}{candidate}"
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{filepath}"
            
            config = CrawlerRunConfig(only_text=True)
            result = await crawler.arun(raw_url, config=config)
            
            if result.success and result.markdown:
                return ReadmeContent(
                    filename=candidate,
                    content=result.markdown
                )
    
    return None
