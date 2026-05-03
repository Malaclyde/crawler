"""Extract repository metadata from GitHub pages."""

import re
from typing import Any

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CrawlResult

from .models import RepoMetadata, LanguageStats
from .raw_fetcher import fetch_raw_license


def _parse_count(text: str | None) -> int | None:
    """Parse count from text like '1.2k' or '1,234' or '1.2k stars'."""
    if not text:
        return None
    
    text = text.strip().lower()
    
    # Remove words like 'stars', 'forks', etc.
    text = re.sub(r'(stars|forks|watching|issues|pull\s*requests|prs)', '', text).strip()
    
    if not text:
        return None
    
    # Handle 'k' suffix (e.g., '1.2k' -> 1200)
    if 'k' in text:
        try:
            num = float(text.replace('k', '').strip())
            return int(num * 1000)
        except ValueError:
            return None
    
    # Handle comma-separated numbers
    try:
        return int(text.replace(',', '').strip())
    except ValueError:
        return None


async def fetch_repo_metadata(owner: str, repo: str, ref: str = "main") -> RepoMetadata:
    """
    Crawl the repo root page and extract full repo metadata.
    
    Use this when you need repo metadata but are on a sub-page
    (file, directory, issues, etc.) that may not have the full sidebar stats.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch/tag/commit ref
        
    Returns:
        RepoMetadata with extracted fields
    """
    repo_root_url = f"https://github.com/{owner}/{repo}"
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            excluded_tags=["header", "nav", "footer"],
            exclude_social_media_links=True,
        )
        result = await crawler.arun(repo_root_url, config=config)
        return await extract_repo_metadata(result, owner, repo, ref=ref)


async def extract_repo_metadata(crawl_result: CrawlResult, owner: str, repo: str, ref: str = "main") -> RepoMetadata:
    """
    Extract repository metadata from crawl result.
    
    Args:
        crawl_result: CrawlResult from crawl4ai
        owner: Repository owner
        repo: Repository name
        
    Returns:
        RepoMetadata with extracted fields
    """
    html = crawl_result.html or ""
    metadata = crawl_result.metadata or {}
    links = crawl_result.links or {}
    
    # Extract description from metadata or og:description
    description = metadata.get("description") or metadata.get("og:description") or ""
    
    # Extract from HTML if available
    stars = None
    forks = None
    watchers = None
    open_issues = None
    open_prs = None
    languages = []
    default_branch = None
    license_name = None
    topics = []
    
    # Try to extract from links
    internal_links = links.get("internal", [])
    
    for link in internal_links:
        href = link.get("href", "").lower()
        text = link.get("text", "").lower()
        
        # Check for topics
        if "/topics/" in href:
            topic = href.split("/topics/")[-1].split("/")[0]
            if topic and topic not in topics:
                topics.append(topic)
        
        # Check for language
        if "language" in text or (href and "/languages/" in href):
            lang_match = re.search(r'([a-zA-Z+]+)\s*[\d.]+%?', text)
            if lang_match:
                language = lang_match.group(1).strip()
    
    # Extract stats using GitHub's current HTML structure
    # Look for anchor tags with specific href patterns and extract count from <strong> or counter spans
    
    # Stars: <a href="/owner/repo/stargazers">...<strong>64.9k</strong> stars</a>
    star_match = re.search(r'href="/[^/]+/[^/]+/stargazers"[^>]*>.*?<strong>([\d,.]+k?)</strong>', html, re.IGNORECASE | re.DOTALL)
    if star_match:
        stars = _parse_count(star_match.group(1))
    
    # Forks: <a href="/owner/repo/forks">...<strong>6.6k</strong> forks</a>
    fork_match = re.search(r'href="/[^/]+/[^/]+/forks"[^>]*>.*?<strong>([\d,.]+k?)</strong>', html, re.IGNORECASE | re.DOTALL)
    if fork_match:
        forks = _parse_count(fork_match.group(1))
    
    # Watchers: <a href="/owner/repo/watchers">...<strong>361</strong> watching</a>
    watch_match = re.search(r'href="/[^/]+/[^/]+/watchers"[^>]*>.*?<strong>([\d,.]+k?)</strong>', html, re.IGNORECASE | re.DOTALL)
    if watch_match:
        watchers = _parse_count(watch_match.group(1))
    
    # Open issues: Look for the counter by its ID attribute
    # Pattern: <span id="issues-repo-tab-count">23</span>
    issues_id_match = re.search(r'id="issues-repo-tab-count"[^>]*>([\d,.]+k?)</', html, re.IGNORECASE)
    if issues_id_match:
        open_issues = _parse_count(issues_id_match.group(1))
    else:
        # Fallback: extract anchor content and look for count
        issues_anchor = re.search(r'<a[^>]*href="/[^/]+/[^/]+/issues"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        if issues_anchor:
            issues_content = issues_anchor.group(1)
            issues_count = re.search(r'<strong>([\d,.]+k?)</strong>', issues_content, re.IGNORECASE)
            if issues_count:
                open_issues = _parse_count(issues_count.group(1))
    
    # Open PRs: Look for the counter by its ID attribute  
    # Pattern: <span id="pull-requests-repo-tab-count">58</span>
    pr_id_match = re.search(r'id="pull-requests-repo-tab-count"[^>]*>([\d,.]+k?)</', html, re.IGNORECASE)
    if pr_id_match:
        open_prs = _parse_count(pr_id_match.group(1))
    else:
        # Fallback: extract anchor content and look for count
        pr_anchor = re.search(r'<a[^>]*href="/[^/]+/[^/]+/pulls"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        if pr_anchor:
            pr_content = pr_anchor.group(1)
            pr_count = re.search(r'<strong>([\d,.]+k?)</strong>', pr_content, re.IGNORECASE)
            if pr_count:
                open_prs = _parse_count(pr_count.group(1))
    
    # Extract all languages with percentages from the Languages section
    # Pattern 1: Languages with links (e.g., Python)
    # <li><a ... href="/owner/repo/search?l=python">...<span>Python</span><span>98.8%</span></a></li>
    lang_link_pattern = r'<li[^>]*>.*?href="/[^/]+/[^/]+/search\?l=([^"]+)".*?<span[^>]*>([^<]+)</span>\s*<span>([\d.]+%)</span>'
    for match in re.finditer(lang_link_pattern, html, re.IGNORECASE | re.DOTALL):
        lang_name = match.group(2).strip()
        percentage_str = match.group(3).replace('%', '').strip()
        try:
            percentage = float(percentage_str)
            languages.append(LanguageStats(name=lang_name, percentage=percentage))
        except ValueError:
            pass
    
    # Pattern 2: Languages without links (e.g., "Other")
    # <li><span>...<svg>...</svg><span>Other</span><span>1.2%</span></span></li>
    # Only add if not already captured above
    other_pattern = r'<span[^>]*class="[^"]*text-bold[^"]*"[^>]*>(Other)</span>\s*<span>([\d.]+%)</span>'
    for match in re.finditer(other_pattern, html, re.IGNORECASE | re.DOTALL):
        lang_name = match.group(1).strip()
        percentage_str = match.group(2).replace('%', '').strip()
        # Check if this language is not already in the list
        if not any(lang.name == lang_name for lang in languages):
            try:
                percentage = float(percentage_str)
                languages.append(LanguageStats(name=lang_name, percentage=percentage))
            except ValueError:
                pass
    
    # Set primary language (first in the list, or use old method as fallback)
    if not languages:
        # Fallback: try to find any language reference
        lang_match = re.search(r'programmingLanguage["\']?\s*[:=]\s*["\']?([a-zA-Z+]+)', html)
        if lang_match:
            languages.append(LanguageStats(name=lang_match.group(1), percentage=100.0))
    
    # License: fetch from LICENSE file in the repo
    license_name = await fetch_raw_license(owner, repo, ref)
    
    # Default branch
    branch_match = re.search(r'defaultBranch["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)', html)
    if branch_match:
        default_branch = branch_match.group(1)
    
    return RepoMetadata(
        owner=owner,
        name=repo,
        description=description if description else None,
        stars=stars,
        forks=forks,
        watchers=watchers,
        open_issues=open_issues,
        open_prs=open_prs,
        languages=languages if languages else None,
        default_branch=default_branch,
        license=license_name,
        topics=topics,
    )
