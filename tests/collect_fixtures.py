"""Collect HTML fixtures from real GitHub pages for offline testing.

Usage:
    python -m tests.collect_fixtures

This will save JSON fixtures to tests/fixtures/ containing:
    url, html, cleaned_html, links, metadata
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

FIXTURES = [
    ("gh_repo_root", "https://github.com/unclecode/crawl4ai"),
    ("gh_directory_with_readme", "https://github.com/unclecode/crawl4ai/tree/main/sbom"),
    ("gh_directory_no_readme", "https://github.com/unclecode/crawl4ai/tree/main/tests"),
    ("gh_file", "https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/adaptive_crawler%20copy.py"),
    ("gh_issues_list", "https://github.com/unclecode/crawl4ai/issues"),
    ("gh_issue_detail", "https://github.com/unclecode/crawl4ai/issues/1950"),
    ("gh_pr_list", "https://github.com/unclecode/crawl4ai/pulls"),
    ("gh_pr_detail", "https://github.com/unclecode/crawl4ai/pull/1952"),
    ("gh_releases", "https://github.com/unclecode/crawl4ai/releases"),
    ("gh_wiki", "https://github.com/unclecode/crawl4ai/wiki"),
    ("gh_commits", "https://github.com/unclecode/crawl4ai/commits/main"),
    ("non_gh_page", "https://example.com"),
]


async def fetch_fixture(name: str, url: str) -> dict:
    """Fetch a page and return its data as a dict."""
    print(f"Fetching {name}...")
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig()
        result = await crawler.arun(url, config=config)

    data = {
        "url": url,
        "html": result.html or "",
        "cleaned_html": result.cleaned_html or "",
        "links": result.links if result.links else {},
        "metadata": result.metadata if result.metadata else {},
    }
    print(f"  Done: {len(data['html'])} bytes")
    return data


async def main():
    os.makedirs(FIXTURES_DIR, exist_ok=True)

    for name, url in FIXTURES:
        fixture_path = os.path.join(FIXTURES_DIR, f"{name}.json")
        if os.path.exists(fixture_path):
            print(f"Skipping {name} — already exists")
            continue

        try:
            data = await fetch_fixture(name, url)
            with open(fixture_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  Saved to {fixture_path}")
        except Exception as e:
            print(f"  ERROR fetching {name}: {e}")

    print("\nDone! Verifying fixtures...")
    for name, _ in FIXTURES:
        fixture_path = os.path.join(FIXTURES_DIR, f"{name}.json")
        if os.path.exists(fixture_path):
            with open(fixture_path) as f:
                data = json.load(f)
            assert "url" in data
            assert "html" in data
            assert len(data["html"]) > 0, f"{name} has empty html"
            print(f"  {name}: {len(data['html'])} bytes — OK")
        else:
            print(f"  {name}: MISSING")

    print("\nAll fixtures verified!")


if __name__ == "__main__":
    asyncio.run(main())
