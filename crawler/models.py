"""Pydantic models for structured JSON responses."""

from typing import Literal

from pydantic import BaseModel


class CrawlResponse(BaseModel):
    """Base response model for all crawl results."""
    url: str
    type: str


class WebPageResponse(CrawlResponse):
    """Response for non-GitHub web pages."""
    type: Literal["web_page"]
    markdown: str
    metadata: dict | None


class LanguageStats(BaseModel):
    """Statistics for a programming language."""
    name: str
    percentage: float


class RepoMetadata(BaseModel):
    """Metadata for a GitHub repository."""
    owner: str
    name: str
    description: str | None = None
    stars: int | None = None
    forks: int | None = None
    watchers: int | None = None
    open_issues: int | None = None
    open_prs: int | None = None
    languages: list[LanguageStats] | None = None
    default_branch: str | None = None
    license: str | None = None
    topics: list[str] = []


class FileEntry(BaseModel):
    """Entry for a file or directory in a listing."""
    name: str
    href: str
    type: Literal["file", "dir"]


class ReadmeContent(BaseModel):
    """README file content."""
    filename: str
    content: str


class GitHubRepoResponse(CrawlResponse):
    """Response for GitHub repo root or directory pages."""
    type: Literal["github_repo", "github_directory"]
    repo: RepoMetadata
    readme: ReadmeContent | None
    files: list[FileEntry]
    pagination: dict[str, str] | None


class FileMetadata(BaseModel):
    """Metadata for a file."""
    name: str
    path: str
    size: str | None
    lines: int | None


class GitHubFileResponse(CrawlResponse):
    """Response for GitHub file (blob) pages."""
    type: Literal["github_file"]
    repo: RepoMetadata
    file: FileMetadata
    raw_url: str
    content: str


class GitHubSecondaryResponse(CrawlResponse):
    """Response for GitHub secondary pages (issues, PRs, releases, wiki, etc.)."""
    type: Literal[
        "github_issues",
        "github_issue",
        "github_pulls",
        "github_pull",
        "github_releases",
        "github_wiki",
        "github_commits",
        "github_commit",
        "github_page",
    ]
    repo: RepoMetadata | None
    markdown: str
    metadata: dict | None
