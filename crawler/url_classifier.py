"""Classify URLs by type (GitHub vs web, page subtype)."""

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class URLType(Enum):
    """URL type enumeration."""
    WEB_PAGE = "web_page"
    GH_REPO = "github_repo"
    GH_DIRECTORY = "github_directory"
    GH_FILE = "github_file"
    GH_ISSUES = "github_issues"
    GH_ISSUE = "github_issue"
    GH_PULLS = "github_pulls"
    GH_PULL = "github_pull"
    GH_RELEASES = "github_releases"
    GH_WIKI = "github_wiki"
    GH_WIKI_PAGE = "github_wiki_page"
    GH_COMMITS = "github_commits"
    GH_COMMIT = "github_commit"
    GH_ACTIONS = "github_actions"
    GH_DISCUSSIONS = "github_discussions"
    GH_DISCUSSION = "github_discussion"
    GH_OTHER = "github_other"
    GH_GIST = "github_gist"
    GH_USER = "github_user"
    GH_ORG = "github_org"


@dataclass
class Classification:
    """Classification result for a URL."""
    url_type: URLType
    owner: str | None = None
    repo: str | None = None
    ref: str | None = None
    path: str | None = None


def classify_url(url: str) -> Classification:
    """
    Classify a URL string and determine its type.
    
    Args:
        url: URL string to classify
        
    Returns:
        Classification dataclass with url_type, owner, repo, ref, path
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path.rstrip("/")
    path_segments = [s for s in path.split("/") if s]
    
    # Handle gist.github.com
    if host == "gist.github.com":
        return Classification(url_type=URLType.GH_GIST)
    
    # Handle non-GitHub URLs
    if host != "github.com":
        return Classification(url_type=URLType.WEB_PAGE)
    
    # Handle github.com paths
    if len(path_segments) == 0:
        # github.com (homepage)
        return Classification(url_type=URLType.WEB_PAGE)
    
    if len(path_segments) == 1:
        # github.com/{user} or github.com/orgs/{org}
        if path_segments[0] == "orgs":
            return Classification(url_type=URLType.GH_ORG)
        return Classification(url_type=URLType.GH_USER, owner=path_segments[0])
    
    owner = path_segments[0]
    repo_or_org = path_segments[1]
    
    # Handle orgs/{org} pattern
    if owner == "orgs":
        return Classification(url_type=URLType.GH_ORG)
    
    # github.com/{owner}/{repo}
    if len(path_segments) == 2:
        return Classification(
            url_type=URLType.GH_REPO,
            owner=owner,
            repo=repo_or_org
        )
    
    # Check for special GitHub pages
    third_segment = path_segments[2]
    
    if third_segment == "tree":
        # /{owner}/{repo}/tree/{ref}/...
        ref = path_segments[3] if len(path_segments) > 3 else None
        path_str = "/".join(path_segments[4:]) if len(path_segments) > 4 else ""
        return Classification(
            url_type=URLType.GH_DIRECTORY,
            owner=owner,
            repo=repo_or_org,
            ref=ref,
            path=path_str
        )
    
    if third_segment == "blob":
        # /{owner}/{repo}/blob/{ref}/...
        ref = path_segments[3] if len(path_segments) > 3 else None
        path_str = "/".join(path_segments[4:]) if len(path_segments) > 4 else ""
        return Classification(
            url_type=URLType.GH_FILE,
            owner=owner,
            repo=repo_or_org,
            ref=ref,
            path=path_str
        )
    
    if third_segment == "issues":
        if len(path_segments) > 3:
            # /{owner}/{repo}/issues/{num}
            return Classification(
                url_type=URLType.GH_ISSUE,
                owner=owner,
                repo=repo_or_org
            )
        return Classification(
            url_type=URLType.GH_ISSUES,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "pulls":
        return Classification(
            url_type=URLType.GH_PULLS,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "pull":
        # /{owner}/{repo}/pull/{num}
        return Classification(
            url_type=URLType.GH_PULL,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "releases":
        return Classification(
            url_type=URLType.GH_RELEASES,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "wiki":
        if len(path_segments) > 3:
            # /{owner}/{repo}/wiki/{page}
            return Classification(
                url_type=URLType.GH_WIKI_PAGE,
                owner=owner,
                repo=repo_or_org
            )
        return Classification(
            url_type=URLType.GH_WIKI,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "commits":
        return Classification(
            url_type=URLType.GH_COMMITS,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "commit":
        # /{owner}/{repo}/commit/{sha}
        return Classification(
            url_type=URLType.GH_COMMIT,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "actions":
        return Classification(
            url_type=URLType.GH_ACTIONS,
            owner=owner,
            repo=repo_or_org
        )
    
    if third_segment == "discussions":
        if len(path_segments) > 3:
            # /{owner}/{repo}/discussions/{num}
            return Classification(
                url_type=URLType.GH_DISCUSSION,
                owner=owner,
                repo=repo_or_org
            )
        return Classification(
            url_type=URLType.GH_DISCUSSIONS,
            owner=owner,
            repo=repo_or_org
        )
    
    # Other GitHub paths
    return Classification(
        url_type=URLType.GH_OTHER,
        owner=owner,
        repo=repo_or_org
    )
