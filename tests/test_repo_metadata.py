"""Test repo metadata extraction."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from crawler.repo_metadata import extract_repo_metadata, _parse_count
from crawler.models import RepoMetadata


class MockCrawlResult:
    """Mock CrawlResult for testing."""
    def __init__(self, html="", metadata=None, links=None):
        self.html = html
        self.metadata = metadata or {}
        self.links = links or {}


def test_parse_count_with_k():
    """Test parsing counts with 'k' suffix."""
    assert _parse_count("1.2k") == 1200
    assert _parse_count("1k") == 1000
    assert _parse_count("10k") == 10000


def test_parse_count_with_commas():
    """Test parsing counts with commas."""
    assert _parse_count("1,234") == 1234
    assert _parse_count("10,000") == 10000


def test_parse_count_plain():
    """Test parsing plain numbers."""
    assert _parse_count("123") == 123
    assert _parse_count("1000") == 1000


def test_parse_count_with_text():
    """Test parsing numbers with text."""
    assert _parse_count("1.2k stars") == 1200
    assert _parse_count("100 forks") == 100
    assert _parse_count("50 watching") == 50


def test_parse_count_none():
    """Test parsing None and empty values."""
    assert _parse_count(None) is None
    assert _parse_count("") is None
    assert _parse_count("   ") is None


@pytest.mark.asyncio
async def test_extract_repo_metadata_basic():
    """Test basic metadata extraction."""
    crawl_result = MockCrawlResult(
        html="",
        metadata={"description": "Test repo"},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    
    assert result.owner == "owner"
    assert result.name == "repo"
    assert result.description == "Test repo"


@pytest.mark.asyncio
async def test_extract_repo_metadata_from_og():
    """Test metadata extraction from og:description."""
    crawl_result = MockCrawlResult(
        html="",
        metadata={"og:description": "OG description"},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    
    assert result.description == "OG description"


@pytest.mark.asyncio
async def test_extract_repo_metadata_topics():
    """Test topic extraction from links."""
    crawl_result = MockCrawlResult(
        html="",
        metadata={},
        links={
            "internal": [
                {"href": "/topics/python", "text": "Python"},
                {"href": "/topics/machine-learning", "text": "Machine Learning"},
                {"href": "/other", "text": "Other"},
            ]
        }
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    
    assert "python" in result.topics
    assert "machine-learning" in result.topics


@pytest.mark.asyncio
async def test_extract_repo_metadata_language():
    """Test language extraction from linked language entries."""
    html = """
    <h2 class="h4 tmp-mb-3">Languages</h2>
    <ul class="list-style-none">
        <li class="d-inline">
            <a href="/owner/repo/search?l=python">
                <svg></svg>
                <span class="color-fg-default text-bold mr-1">Python</span>
                <span>98.8%</span>
            </a>
        </li>
    </ul>
    """
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    

    assert result.languages is not None
    assert len(result.languages) == 1
    assert result.languages[0].name == "Python"
    assert result.languages[0].percentage == 98.8


@pytest.mark.asyncio
async def test_extract_repo_metadata_languages_multiple():
    """Test extraction of multiple languages including non-linked ones."""
    html = """
    <h2 class="h4 tmp-mb-3">Languages</h2>
    <ul class="list-style-none">
        <li class="d-inline">
            <a href="/owner/repo/search?l=python">
                <svg></svg>
                <span class="color-fg-default text-bold mr-1">Python</span>
                <span>85.5%</span>
            </a>
        </li>
        <li class="d-inline">
            <a href="/owner/repo/search?l=javascript">
                <svg></svg>
                <span class="color-fg-default text-bold mr-1">JavaScript</span>
                <span>10.0%</span>
            </a>
        </li>
        <li class="d-inline">
            <span class="d-inline-flex flex-items-center flex-nowrap text-small tmp-mr-3">
                <svg></svg>
                <span class="color-fg-default text-bold mr-1">Other</span>
                <span>4.5%</span>
            </span>
        </li>
    </ul>
    """
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    

    assert result.languages is not None
    assert len(result.languages) == 3
    assert result.languages[0].name == "Python"
    assert result.languages[0].percentage == 85.5
    assert result.languages[1].name == "JavaScript"
    assert result.languages[1].percentage == 10.0
    assert result.languages[2].name == "Other"
    assert result.languages[2].percentage == 4.5


@pytest.mark.asyncio
async def test_extract_repo_metadata_stars():
    """Test stars extraction from HTML."""
    # GitHub's current HTML structure
    html = '<a href="/unclecode/crawl4ai/stargazers" data-view-component="true" class="Link Link--muted"><svg aria-hidden="true"></svg><strong>64.9k</strong> stars</a>'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "unclecode", "crawl4ai")
    
    assert result.stars == 64900


@pytest.mark.asyncio
async def test_extract_repo_metadata_forks():
    """Test forks extraction from HTML."""
    # GitHub's current HTML structure
    html = '<a href="/unclecode/crawl4ai/forks" data-view-component="true" class="Link Link--muted"><svg aria-hidden="true"></svg><strong>6.6k</strong> forks</a>'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "unclecode", "crawl4ai")
    
    assert result.forks == 6600


@pytest.mark.asyncio
async def test_extract_repo_metadata_watchers():
    """Test watchers extraction from HTML."""
    # GitHub's current HTML structure
    html = '<a href="/unclecode/crawl4ai/watchers" data-view-component="true" class="Link Link--muted"><svg aria-hidden="true"></svg><strong>361</strong> watching</a>'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "unclecode", "crawl4ai")
    
    assert result.watchers == 361


@pytest.mark.asyncio
async def test_extract_repo_metadata_issues():
    """Test open issues extraction from HTML."""
    # GitHub's current HTML structure with ID-based counter
    html = '<a href="/unclecode/crawl4ai/issues"><span>Issues</span><span id="issues-repo-tab-count">23</span></a>'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "unclecode", "crawl4ai")
    
    assert result.open_issues == 23


@pytest.mark.asyncio
async def test_extract_repo_metadata_prs():
    """Test open PRs extraction from HTML."""
    # GitHub's current HTML structure with ID-based counter
    html = '<a href="/unclecode/crawl4ai/pulls"><span>Pull requests</span><span id="pull-requests-repo-tab-count">58</span></a>'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "unclecode", "crawl4ai")
    
    assert result.open_prs == 58


@pytest.mark.asyncio
async def test_extract_repo_metadata_license():
    """Test license extraction fetches from LICENSE file."""
    html = '<div>some repo content</div>'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    with patch('crawler.repo_metadata.fetch_raw_license', return_value="Apache License"):
        result = await extract_repo_metadata(crawl_result, "owner", "repo", ref="main")
    
    assert result.license == "Apache License"


@pytest.mark.asyncio
async def test_extract_repo_metadata_license_none():
    """Test license is None when no LICENSE file exists."""
    html = '<div>some repo content</div>'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    with patch('crawler.repo_metadata.fetch_raw_license', return_value=None):
        result = await extract_repo_metadata(crawl_result, "owner", "repo", ref="main")
    
    assert result.license is None


@pytest.mark.asyncio
async def test_extract_repo_metadata_default_branch():
    """Test default branch extraction from HTML."""
    html = 'defaultBranch: "main"'
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    
    assert result.default_branch == "main"


@pytest.mark.asyncio
async def test_extract_repo_metadata_empty():
    """Test metadata extraction with empty data."""
    crawl_result = MockCrawlResult(
        html="",
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    
    assert result.owner == "owner"
    assert result.name == "repo"
    assert result.description is None
    assert result.stars is None
    assert result.forks is None
    assert result.topics == []


@pytest.mark.asyncio
async def test_extract_repo_metadata_all_fields():
    """Test complete metadata extraction."""
    # Use GitHub's current HTML structure with ID-based counters
    html = """
    <a href="/owner/repo/stargazers" class="Link"><svg></svg><strong>1.5k</strong> stars</a>
    <a href="/owner/repo/forks" class="Link"><svg></svg><strong>200</strong> forks</a>
    <a href="/owner/repo/watchers" class="Link"><svg></svg><strong>50</strong> watching</a>
    <a href="/owner/repo/issues" class="Link"><span>Issues</span><span id="issues-repo-tab-count">10</span></a>
    <a href="/owner/repo/pulls" class="Link"><span>Pull requests</span><span id="pull-requests-repo-tab-count">5</span></a>
    <div>MIT License</div>
    <div>defaultBranch: main</div>
    """
    crawl_result = MockCrawlResult(
        html=html,
        metadata={"description": "Complete test"},
        links={
            "internal": [
                {"href": "/topics/test", "text": "test"},
                {"href": "/topics/demo", "text": "demo"},
            ]
        }
    )
    
    result = await extract_repo_metadata(crawl_result, "owner", "repo")
    
    assert result.description == "Complete test"
    assert result.stars == 1500
    assert result.forks == 200
    assert result.watchers == 50
    assert result.open_issues == 10
    assert result.open_prs == 5
    assert "test" in result.topics
    assert "demo" in result.topics


@pytest.mark.asyncio
async def test_extract_repo_metadata_no_cross_contamination():
    """Test that stats from different anchors don't get mixed up."""
    # This tests the specific issue where issues/PRs might capture stars count
    html = """
    <a href="/unclecode/crawl4ai/stargazers"><strong>64.9k</strong> stars</a>
    <a href="/unclecode/crawl4ai/forks"><strong>6.6k</strong> forks</a>
    <a href="/unclecode/crawl4ai/watchers"><strong>361</strong> watching</a>
    <a href="/unclecode/crawl4ai/issues"><span id="issues-repo-tab-count">23</span></a>
    <a href="/unclecode/crawl4ai/pulls"><span id="pull-requests-repo-tab-count">58</span></a>
    """
    crawl_result = MockCrawlResult(
        html=html,
        metadata={},
        links={"internal": []}
    )
    
    result = await extract_repo_metadata(crawl_result, "unclecode", "crawl4ai")
    
    # Each stat should have its own correct value, not cross-contaminated
    assert result.stars == 64900  # 64.9k
    assert result.forks == 6600   # 6.6k
    assert result.watchers == 361
    assert result.open_issues == 23
    assert result.open_prs == 58
