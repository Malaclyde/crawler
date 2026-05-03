"""GitHub URL utilities for constructing raw URLs and parsing paths."""

from urllib.parse import urlparse


def build_raw_url(owner: str, repo: str, ref: str, filepath: str) -> str:
    """
    Build raw.githubusercontent.com URL.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch/tag/commit ref
        filepath: Path to file in repo
        
    Returns:
        Raw URL string
    """
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{filepath}"


def extract_blob_path(url: str) -> tuple[str, str]:
    """
    Extract ref and path from a GitHub blob URL.
    
    Args:
        url: GitHub blob URL (e.g., github.com/owner/repo/blob/ref/path)
        
    Returns:
        Tuple of (ref, path)
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    segments = [s for s in path.split("/") if s]
    
    # Expect: /{owner}/{repo}/blob/{ref}/...
    if len(segments) < 4 or segments[2] != "blob":
        raise ValueError(f"Invalid blob URL: {url}")
    
    ref = segments[3]
    filepath = "/".join(segments[4:]) if len(segments) > 4 else ""
    return ref, filepath


def extract_tree_path(url: str) -> tuple[str, str]:
    """
    Extract ref and path from a GitHub tree URL.
    
    Args:
        url: GitHub tree URL (e.g., github.com/owner/repo/tree/ref/path)
        
    Returns:
        Tuple of (ref, path)
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    segments = [s for s in path.split("/") if s]
    
    # Expect: /{owner}/{repo}/tree/{ref}/...
    if len(segments) < 4 or segments[2] != "tree":
        raise ValueError(f"Invalid tree URL: {url}")
    
    ref = segments[3]
    filepath = "/".join(segments[4:]) if len(segments) > 4 else ""
    return ref, filepath


def build_github_file_url(owner: str, repo: str, ref: str, path: str) -> str:
    """
    Build GitHub file (blob) URL.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch/tag/commit ref
        path: Path to file in repo
        
    Returns:
        GitHub blob URL string
    """
    return f"https://github.com/{owner}/{repo}/blob/{ref}/{path}"


def build_github_dir_url(owner: str, repo: str, ref: str, path: str) -> str:
    """
    Build GitHub directory (tree) URL.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch/tag/commit ref
        path: Path to directory in repo
        
    Returns:
        GitHub tree URL string
    """
    return f"https://github.com/{owner}/{repo}/tree/{ref}/{path}"
