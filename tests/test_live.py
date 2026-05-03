"""End-to-end live tests against real GitHub pages.

Run with:
    pytest -m live --timeout=60

These tests are skipped by default (opt-in only).
"""

import json

import pytest

from crawler.crawler import crawl


pytestmark = pytest.mark.live


@pytest.fixture
def results():
    """Crawl results cache to avoid repeated network calls."""
    cache = {}

    async def get(url: str):
        if url not in cache:
            cache[url] = await crawl(url)
        return cache[url]

    return get


@pytest.mark.asyncio
async def test_repo_root(results):
    """Verify repo root returns files, README, and stats."""
    result = await results("https://github.com/unclecode/crawl4ai")
    data = result.model_dump()

    assert data["type"] == "github_repo"
    assert data["repo"]["owner"] == "unclecode"
    assert data["repo"]["name"] == "crawl4ai"
    assert data["repo"]["stars"] is not None and data["repo"]["stars"] > 0
    assert data["repo"]["forks"] is not None and data["repo"]["forks"] > 0
    assert len(data["files"]) > 0
    assert data["readme"] is not None
    assert data["readme"]["filename"] is not None
    assert len(data["readme"]["content"]) > 0

    # Language stats should be populated
    assert data["repo"]["languages"] is not None
    assert len(data["repo"]["languages"]) > 0
    assert data["repo"]["languages"][0]["name"] is not None
    assert data["repo"]["languages"][0]["percentage"] > 0


@pytest.mark.asyncio
async def test_repo_root_stats(results):
    """Verify specific stat values (may change, but should be reasonable)."""
    result = await results("https://github.com/unclecode/crawl4ai")
    data = result.model_dump()

    assert data["repo"]["stars"] >= 10000
    assert data["repo"]["forks"] >= 1000
    assert data["repo"]["watchers"] >= 100
    assert data["repo"]["open_issues"] >= 0
    assert data["repo"]["open_prs"] >= 0
    assert data["repo"]["license"] is not None


@pytest.mark.asyncio
async def test_directory_with_readme(results):
    """Verify directory with README returns files and readme content."""
    result = await results("https://github.com/unclecode/crawl4ai/tree/main/sbom")
    data = result.model_dump()

    assert data["type"] == "github_directory"
    assert len(data["files"]) > 0
    assert data["readme"] is not None
    assert len(data["readme"]["content"]) > 0

    # Repo stats should come from root
    assert data["repo"]["stars"] is not None and data["repo"]["stars"] > 0
    assert data["repo"]["forks"] is not None and data["repo"]["forks"] > 0


@pytest.mark.asyncio
async def test_directory_no_readme(results):
    """Verify directory without README returns files but no readme."""
    result = await results("https://github.com/unclecode/crawl4ai/tree/main/tests")
    data = result.model_dump()

    assert data["type"] == "github_directory"
    assert len(data["files"]) > 0
    assert data["readme"] is None

    # Repo stats should come from root
    assert data["repo"]["stars"] is not None and data["repo"]["stars"] > 0


@pytest.mark.asyncio
async def test_file(results):
    """Verify file page returns content and repo metadata."""
    url = "https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/adaptive_crawler%20copy.py"
    result = await results(url)
    data = result.model_dump()

    assert data["type"] == "github_file"
    # Filename may be URL-decoded or encoded depending on how the page renders it
    assert "adaptive_crawler" in data["file"]["name"]
    assert data["file"]["path"] is not None
    assert data["raw_url"] is not None
    assert data["content"] is not None and len(data["content"]) > 0

    # Repo stats should come from root (not blob page)
    assert data["repo"]["stars"] is not None and data["repo"]["stars"] > 0
    assert data["repo"]["forks"] is not None and data["repo"]["forks"] > 0
    assert data["repo"]["license"] is not None


@pytest.mark.asyncio
async def test_issues_list(results):
    """Verify issues list returns content."""
    result = await results("https://github.com/unclecode/crawl4ai/issues")
    data = result.model_dump()

    assert data["type"] == "github_issues"
    assert data["markdown"] is not None and len(data["markdown"]) > 0


@pytest.mark.asyncio
async def test_issue_detail(results):
    """Verify issue detail returns body content."""
    result = await results("https://github.com/unclecode/crawl4ai/issues/1950")
    data = result.model_dump()

    assert data["type"] == "github_issue"
    assert data["markdown"] is not None and len(data["markdown"]) > 0


@pytest.mark.asyncio
async def test_pr_list(results):
    """Verify PR list returns content."""
    result = await results("https://github.com/unclecode/crawl4ai/pulls")
    data = result.model_dump()

    assert data["type"] == "github_pulls"
    assert data["markdown"] is not None and len(data["markdown"]) > 0


@pytest.mark.asyncio
async def test_pr_detail(results):
    """Verify PR detail returns content."""
    result = await results("https://github.com/unclecode/crawl4ai/pull/1952")
    data = result.model_dump()

    assert data["type"] == "github_pull"
    assert data["markdown"] is not None and len(data["markdown"]) > 0


@pytest.mark.asyncio
async def test_json_serialization(results):
    """Verify all responses can be serialized to JSON."""
    urls = [
        "https://github.com/unclecode/crawl4ai",
        "https://github.com/unclecode/crawl4ai/tree/main/sbom",
        "https://github.com/unclecode/crawl4ai/tree/main/tests",
        "https://github.com/unclecode/crawl4ai/issues/1950",
        "https://github.com/unclecode/crawl4ai/pull/1952",
    ]

    for url in urls:
        result = await results(url)
        data = result.model_dump()
        serialized = json.dumps(data)
        assert serialized is not None
        assert len(serialized) > 0
