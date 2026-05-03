"""Test Pydantic response models."""

import json

import pytest
from pydantic import ValidationError

from crawler.models import (
    CrawlResponse,
    FileEntry,
    FileMetadata,
    GitHubFileResponse,
    GitHubRepoResponse,
    GitHubSecondaryResponse,
    LanguageStats,
    ReadmeContent,
    RepoMetadata,
    WebPageResponse,
)


def test_web_page_response():
    """Test WebPageResponse instantiation and serialization."""
    response = WebPageResponse(
        url="https://example.com",
        type="web_page",
        markdown="# Hello\n\nWorld",
        metadata={"title": "Example"}
    )
    
    assert response.url == "https://example.com"
    assert response.type == "web_page"
    assert response.markdown == "# Hello\n\nWorld"
    assert response.metadata == {"title": "Example"}
    
    data = json.loads(response.model_dump_json())
    assert data["type"] == "web_page"
    assert data["markdown"] == "# Hello\n\nWorld"


def test_repo_metadata():
    """Test RepoMetadata instantiation."""
    metadata = RepoMetadata(
        owner="unclecode",
        name="crawl4ai",
        description="Test repo",
        stars=100,
        forks=20,
        watchers=150,
        open_issues=5,
        open_prs=3,

        languages=[
            LanguageStats(name="Python", percentage=98.8),
            LanguageStats(name="Other", percentage=1.2),
        ],
        default_branch="main",
        license="MIT",
        topics=["crawler", "ai"],
    )
    
    assert metadata.owner == "unclecode"
    assert metadata.name == "crawl4ai"
    assert metadata.stars == 100

    assert len(metadata.languages) == 2
    assert metadata.languages[0].name == "Python"
    assert metadata.languages[0].percentage == 98.8
    assert metadata.topics == ["crawler", "ai"]
    
    data = json.loads(metadata.model_dump_json())
    assert data["stars"] == 100
    assert data["languages"][0]["name"] == "Python"


def test_language_stats():
    """Test LanguageStats instantiation."""
    lang = LanguageStats(name="Python", percentage=98.8)
    assert lang.name == "Python"
    assert lang.percentage == 98.8
    
    data = json.loads(lang.model_dump_json())
    assert data["name"] == "Python"
    assert data["percentage"] == 98.8


def test_file_entry():
    """Test FileEntry instantiation."""
    entry = FileEntry(name="README.md", href="/owner/repo/blob/main/README.md", type="file")
    
    assert entry.name == "README.md"
    assert entry.type == "file"
    
    data = json.loads(entry.model_dump_json())
    assert data["type"] == "file"


def test_readme_content():
    """Test ReadmeContent instantiation."""
    readme = ReadmeContent(filename="README.md", content="# Title\n\nContent")
    
    assert readme.filename == "README.md"
    assert readme.content == "# Title\n\nContent"
    
    data = json.loads(readme.model_dump_json())
    assert data["filename"] == "README.md"


def test_github_repo_response():
    """Test GitHubRepoResponse instantiation."""
    repo = RepoMetadata(
        owner="unclecode",
        name="crawl4ai",
        description=None,
        stars=None,
        forks=None,
        watchers=None,
        open_issues=None,
        open_prs=None,
        default_branch=None,
        license=None,
        topics=[],
    )
    
    response = GitHubRepoResponse(
        url="https://github.com/unclecode/crawl4ai",
        type="github_repo",
        repo=repo,
        readme=None,
        files=[FileEntry(name="README.md", href="/blob/main/README.md", type="file")],
        pagination=None,
    )
    
    assert response.type == "github_repo"
    assert response.repo.owner == "unclecode"
    assert len(response.files) == 1
    
    data = json.loads(response.model_dump_json())
    assert data["type"] == "github_repo"
    assert data["repo"]["owner"] == "unclecode"


def test_github_file_response():
    """Test GitHubFileResponse instantiation."""
    repo = RepoMetadata(
        owner="unclecode",
        name="crawl4ai",
        description=None,
        stars=None,
        forks=None,
        watchers=None,
        open_issues=None,
        open_prs=None,
        default_branch=None,
        license=None,
        topics=[],
    )
    
    file_meta = FileMetadata(
        name="test.py",
        path="tests/test.py",
        size="1.2 KB",
        lines=50,
    )
    
    response = GitHubFileResponse(
        url="https://github.com/unclecode/crawl4ai/blob/main/tests/test.py",
        type="github_file",
        repo=repo,
        file=file_meta,
        raw_url="https://raw.githubusercontent.com/unclecode/crawl4ai/main/tests/test.py",
        content="print('hello')",
    )
    
    assert response.type == "github_file"
    assert response.file.name == "test.py"
    assert response.content == "print('hello')"
    
    data = json.loads(response.model_dump_json())
    assert data["type"] == "github_file"
    assert data["file"]["name"] == "test.py"


def test_github_secondary_response():
    """Test GitHubSecondaryResponse instantiation."""
    repo = RepoMetadata(
        owner="unclecode",
        name="crawl4ai",
        description=None,
        stars=None,
        forks=None,
        watchers=None,
        open_issues=None,
        open_prs=None,
        default_branch=None,
        license=None,
        topics=[],
    )
    
    response = GitHubSecondaryResponse(
        url="https://github.com/unclecode/crawl4ai/issues",
        type="github_issues",
        repo=repo,
        markdown="# Issues\n\n- Issue 1",
        metadata={"count": 5},
    )
    
    assert response.type == "github_issues"
    assert response.repo is not None
    assert response.repo.owner == "unclecode"
    
    data = json.loads(response.model_dump_json())
    assert data["type"] == "github_issues"


def test_github_secondary_response_no_repo():
    """Test GitHubSecondaryResponse with no repo (e.g., user profile)."""
    response = GitHubSecondaryResponse(
        url="https://github.com/unclecode",
        type="github_page",
        repo=None,
        markdown="# Profile\n\nContent",
        metadata=None,
    )
    
    assert response.type == "github_page"
    assert response.repo is None
    
    data = json.loads(response.model_dump_json())
    assert data["repo"] is None


def test_repo_metadata_optional_fields():
    """Test RepoMetadata with all None values."""
    metadata = RepoMetadata(
        owner="test",
        name="test-repo",
        description=None,
        stars=None,
        forks=None,
        watchers=None,
        open_issues=None,
        open_prs=None,
        default_branch=None,
        license=None,
        topics=[],
    )
    
    assert metadata.description is None
    assert metadata.stars is None
    assert metadata.topics == []
    
    data = json.loads(metadata.model_dump_json())
    assert data["description"] is None


def test_file_metadata_optional_fields():
    """Test FileMetadata with optional fields."""
    file_meta = FileMetadata(
        name="test.txt",
        path="test.txt",
        size=None,
        lines=None,
    )

    assert file_meta.size is None
    assert file_meta.lines is None

    data = json.loads(file_meta.model_dump_json())
    assert data["size"] is None


@pytest.mark.parametrize("page_type", [
    "github_issues",
    "github_issue",
    "github_pulls",
    "github_pull",
    "github_releases",
    "github_wiki",
    "github_commits",
    "github_commit",
    "github_page",
])
def test_github_secondary_types(page_type):
    """Test all GitHubSecondaryResponse type variants."""
    response = GitHubSecondaryResponse(
        url="https://github.com/test/repo",
        type=page_type,
        repo=None,
        markdown="content",
        metadata=None,
    )
    assert response.type == page_type
