"""Integration tests for the crawler."""

import pytest
from unittest.mock import patch, AsyncMock

from crawler.crawler import crawl
from crawler.models import WebPageResponse, GitHubRepoResponse, GitHubFileResponse, GitHubSecondaryResponse
from crawler.url_classifier import URLType


class MockParser:
    """Mock parser result."""
    def __init__(self, result):
        self.result = result
    
    async def __call__(self, url):
        return self.result


@pytest.mark.asyncio
async def test_crawl_web_page():
    """Test crawling a non-GitHub URL."""
    from crawler.models import WebPageResponse
    
    mock_result = WebPageResponse(
        url="https://example.com",
        type="web_page",
        markdown="# Test",
        metadata=None,
    )
    
    with patch('crawler.crawler.parse_web_page', return_value=mock_result):
        result = await crawl("https://example.com")
    
    assert result.type == "web_page"
    assert result.url == "https://example.com"


@pytest.mark.asyncio
async def test_crawl_github_repo():
    """Test crawling a GitHub repo URL."""
    from crawler.models import GitHubRepoResponse, RepoMetadata
    
    mock_result = GitHubRepoResponse(
        url="https://github.com/owner/repo",
        type="github_repo",
        repo=RepoMetadata(
            owner="owner",
            name="repo",
            description=None,
            stars=None,
            forks=None,
            watchers=None,
            open_issues=None,
            open_prs=None,
            default_branch=None,
            license=None,
            topics=[],
        ),
        readme=None,
        files=[],
        pagination=None,
    )
    
    with patch('crawler.crawler.parse_repo_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo")
    
    assert result.type == "github_repo"


@pytest.mark.asyncio
async def test_crawl_github_file():
    """Test crawling a GitHub file URL."""
    from crawler.models import GitHubFileResponse, RepoMetadata, FileMetadata
    
    mock_result = GitHubFileResponse(
        url="https://github.com/owner/repo/blob/main/file.py",
        type="github_file",
        repo=RepoMetadata(
            owner="owner",
            name="repo",
            description=None,
            stars=None,
            forks=None,
            watchers=None,
            open_issues=None,
            open_prs=None,
            default_branch=None,
            license=None,
            topics=[],
        ),
        file=FileMetadata(
            name="file.py",
            path="file.py",
            size=None,
            lines=None,
        ),
        raw_url="",
        content="",
    )
    
    with patch('crawler.crawler.parse_file_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo/blob/main/file.py")
    
    assert result.type == "github_file"


@pytest.mark.asyncio
async def test_crawl_github_issues():
    """Test crawling GitHub issues."""
    from crawler.models import GitHubSecondaryResponse
    
    mock_result = GitHubSecondaryResponse(
        url="https://github.com/owner/repo/issues",
        type="github_issues",
        repo=None,
        markdown="# Issues",
        metadata=None,
    )
    
    with patch('crawler.crawler.parse_issues_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo/issues")
    
    assert result.type == "github_issues"


@pytest.mark.asyncio
async def test_crawl_github_pulls():
    """Test crawling GitHub pull requests."""
    from crawler.models import GitHubSecondaryResponse
    
    mock_result = GitHubSecondaryResponse(
        url="https://github.com/owner/repo/pulls",
        type="github_pulls",
        repo=None,
        markdown="# Pull Requests",
        metadata=None,
    )
    
    with patch('crawler.crawler.parse_pulls_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo/pulls")
    
    assert result.type == "github_pulls"


@pytest.mark.asyncio
async def test_crawl_github_releases():
    """Test crawling GitHub releases."""
    from crawler.models import GitHubSecondaryResponse
    
    mock_result = GitHubSecondaryResponse(
        url="https://github.com/owner/repo/releases",
        type="github_releases",
        repo=None,
        markdown="# Releases",
        metadata=None,
    )
    
    with patch('crawler.crawler.parse_releases_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo/releases")
    
    assert result.type == "github_releases"


@pytest.mark.asyncio
async def test_crawl_github_wiki():
    """Test crawling GitHub wiki."""
    from crawler.models import GitHubSecondaryResponse
    
    mock_result = GitHubSecondaryResponse(
        url="https://github.com/owner/repo/wiki",
        type="github_wiki",
        repo=None,
        markdown="# Wiki",
        metadata=None,
    )
    
    with patch('crawler.crawler.parse_wiki_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo/wiki")
    
    assert result.type == "github_wiki"


@pytest.mark.asyncio
async def test_crawl_github_commits():
    """Test crawling GitHub commits."""
    from crawler.models import GitHubSecondaryResponse
    
    mock_result = GitHubSecondaryResponse(
        url="https://github.com/owner/repo/commits/main",
        type="github_commits",
        repo=None,
        markdown="# Commits",
        metadata=None,
    )
    
    with patch('crawler.crawler.parse_commits_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo/commits/main")
    
    assert result.type == "github_commits"


@pytest.mark.asyncio
async def test_crawl_error_handling():
    """Test that errors are handled gracefully."""
    with patch('crawler.crawler.parse_web_page', side_effect=Exception("Test error")):
        result = await crawl("https://example.com")
    
    # Should return error response
    assert result is not None
    if hasattr(result, 'metadata') and result.metadata:
        assert "error" in str(result.metadata)


@pytest.mark.asyncio
async def test_crawl_json_serialization():
    """Test that response can be serialized to JSON."""
    from crawler.models import WebPageResponse
    
    mock_result = WebPageResponse(
        url="https://example.com",
        type="web_page",
        markdown="# Test",
        metadata={"key": "value"},
    )
    
    with patch('crawler.crawler.parse_web_page', return_value=mock_result):
        result = await crawl("https://example.com")
    
    # Test JSON serialization
    import json
    data = json.loads(result.model_dump_json())
    assert data["url"] == "https://example.com"
    assert data["type"] == "web_page"


@pytest.mark.asyncio
async def test_crawl_github_directory():
    """Test crawling GitHub directory."""
    from crawler.models import GitHubRepoResponse, RepoMetadata
    
    mock_result = GitHubRepoResponse(
        url="https://github.com/owner/repo/tree/main/src",
        type="github_directory",
        repo=RepoMetadata(
            owner="owner",
            name="repo",
            description=None,
            stars=None,
            forks=None,
            watchers=None,
            open_issues=None,
            open_prs=None,
            default_branch=None,
            license=None,
            topics=[],
        ),
        readme=None,
        files=[],
        pagination=None,
    )
    
    with patch('crawler.crawler.parse_repo_page', return_value=mock_result):
        result = await crawl("https://github.com/owner/repo/tree/main/src")
    
    assert result.type == "github_directory"
