"""Test URL classifier with parametrized tests covering all URL types and edge cases."""

import pytest

from crawler.url_classifier import Classification, URLType, classify_url


@pytest.mark.parametrize(
    "url,expected_type,expected_owner,expected_repo",
    [
        # Non-GitHub URLs
        ("https://example.com", URLType.WEB_PAGE, None, None),
        ("https://example.com/path", URLType.WEB_PAGE, None, None),
        ("https://google.com/search?q=test", URLType.WEB_PAGE, None, None),
        
        # GitHub repo root
        ("https://github.com/unclecode/crawl4ai", URLType.GH_REPO, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/", URLType.GH_REPO, "unclecode", "crawl4ai"),  # trailing slash
        
        # GitHub directory (tree)
        ("https://github.com/unclecode/crawl4ai/tree/main", URLType.GH_DIRECTORY, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/tree/main/src", URLType.GH_DIRECTORY, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/tree/main/tests/fixtures", URLType.GH_DIRECTORY, "unclecode", "crawl4ai"),
        
        # GitHub file (blob)
        ("https://github.com/unclecode/crawl4ai/blob/main/README.md", URLType.GH_FILE, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/blob/main/src/crawler.py", URLType.GH_FILE, "unclecode", "crawl4ai"),
        
        # GitHub issues
        ("https://github.com/unclecode/crawl4ai/issues", URLType.GH_ISSUES, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/issues/1", URLType.GH_ISSUE, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/issues/123", URLType.GH_ISSUE, "unclecode", "crawl4ai"),
        
        # GitHub pulls
        ("https://github.com/unclecode/crawl4ai/pulls", URLType.GH_PULLS, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/pull/1", URLType.GH_PULL, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/pull/456", URLType.GH_PULL, "unclecode", "crawl4ai"),
        
        # GitHub releases
        ("https://github.com/unclecode/crawl4ai/releases", URLType.GH_RELEASES, "unclecode", "crawl4ai"),
        
        # GitHub wiki
        ("https://github.com/unclecode/crawl4ai/wiki", URLType.GH_WIKI, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/wiki/Home", URLType.GH_WIKI_PAGE, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/wiki/Getting-Started", URLType.GH_WIKI_PAGE, "unclecode", "crawl4ai"),
        
        # GitHub commits
        ("https://github.com/unclecode/crawl4ai/commits/main", URLType.GH_COMMITS, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/commit/abc123", URLType.GH_COMMIT, "unclecode", "crawl4ai"),
        
        # GitHub actions
        ("https://github.com/unclecode/crawl4ai/actions", URLType.GH_ACTIONS, "unclecode", "crawl4ai"),
        
        # GitHub discussions
        ("https://github.com/unclecode/crawl4ai/discussions", URLType.GH_DISCUSSIONS, "unclecode", "crawl4ai"),
        ("https://github.com/unclecode/crawl4ai/discussions/42", URLType.GH_DISCUSSION, "unclecode", "crawl4ai"),
        
        # GitHub user profile
        ("https://github.com/unclecode", URLType.GH_USER, "unclecode", None),
        
        # GitHub org
        ("https://github.com/orgs/github", URLType.GH_ORG, None, None),
        
        # GitHub gist
        ("https://gist.github.com/12345678", URLType.GH_GIST, None, None),
        ("https://gist.github.com/user/12345678", URLType.GH_GIST, None, None),
    ]
)
def test_url_classification(url, expected_type, expected_owner, expected_repo):
    """Test URL classification for various URL types."""
    result = classify_url(url)
    assert result.url_type == expected_type
    assert result.owner == expected_owner
    assert result.repo == expected_repo


@pytest.mark.parametrize(
    "url,expected_ref,expected_path",
    [
        # Tree URLs
        ("https://github.com/owner/repo/tree/main", "main", ""),
        ("https://github.com/owner/repo/tree/main/src", "main", "src"),
        ("https://github.com/owner/repo/tree/main/tests/fixtures", "main", "tests/fixtures"),
        
        # Blob URLs
        ("https://github.com/owner/repo/blob/main/README.md", "main", "README.md"),
        ("https://github.com/owner/repo/blob/main/src/crawler.py", "main", "src/crawler.py"),
    ]
)
def test_tree_blob_parsing(url, expected_ref, expected_path):
    """Test that tree and blob URLs correctly extract ref and path."""
    result = classify_url(url)
    assert result.ref == expected_ref
    assert result.path == expected_path


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner/repo/issues?q=test",  # query params
        "https://github.com/owner/repo/issues#top",  # fragment
        "https://github.com/owner/repo/tree/feature/branch/",  # trailing slash
    ]
)
def test_edge_cases(url):
    """Test edge cases like query params, fragments, trailing slashes."""
    result = classify_url(url)
    assert result.url_type in [URLType.GH_ISSUES, URLType.GH_DIRECTORY]


@pytest.mark.parametrize(
    "url,expected_type",
    [
        ("https://github.com/owner/repo/settings", URLType.GH_OTHER),
        ("https://github.com/owner/repo/stargazers", URLType.GH_OTHER),
        ("https://github.com/owner/repo/network", URLType.GH_OTHER),
    ]
)
def test_github_other_paths(url, expected_type):
    """Test other GitHub paths that don't have specific types."""
    result = classify_url(url)
    assert result.url_type == expected_type
    assert result.owner == "owner"
    assert result.repo == "repo"


def test_classification_dataclass():
    """Test Classification dataclass structure."""
    result = classify_url("https://github.com/owner/repo/blob/main/file.py")
    assert hasattr(result, 'url_type')
    assert hasattr(result, 'owner')
    assert hasattr(result, 'repo')
    assert hasattr(result, 'ref')
    assert hasattr(result, 'path')


def test_url_type_enum_values():
    """Test that URLType enum has all expected values."""
    assert URLType.WEB_PAGE.value == "web_page"
    assert URLType.GH_REPO.value == "github_repo"
    assert URLType.GH_DIRECTORY.value == "github_directory"
    assert URLType.GH_FILE.value == "github_file"
    assert URLType.GH_ISSUES.value == "github_issues"
    assert URLType.GH_ISSUE.value == "github_issue"
    assert URLType.GH_PULLS.value == "github_pulls"
    assert URLType.GH_PULL.value == "github_pull"
    assert URLType.GH_RELEASES.value == "github_releases"
    assert URLType.GH_WIKI.value == "github_wiki"
    assert URLType.GH_WIKI_PAGE.value == "github_wiki_page"
    assert URLType.GH_COMMITS.value == "github_commits"
    assert URLType.GH_COMMIT.value == "github_commit"
    assert URLType.GH_ACTIONS.value == "github_actions"
    assert URLType.GH_DISCUSSIONS.value == "github_discussions"
    assert URLType.GH_DISCUSSION.value == "github_discussion"
    assert URLType.GH_OTHER.value == "github_other"
    assert URLType.GH_GIST.value == "github_gist"
    assert URLType.GH_USER.value == "github_user"
    assert URLType.GH_ORG.value == "github_org"
