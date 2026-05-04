# GitHub-Aware Web Crawler

A specialized web crawler that understands GitHub's structure and extracts clean, structured data from GitHub repositories, regular web pages, PDFs, and entire sites. Designed for LLM tool integration.

## Features

- **GitHub-Specific Parsing**: Optimized handlers for repos, files, issues, PRs, releases, wiki, commits — returns structured JSON with repo metadata (stars, forks, languages, license)
- **Clean Markdown Extraction**: Removes navigation, footers, and boilerplate
- **Five Operational Modes**: `crawl`, `fetch`, `download`, `site`, `research`
- **BM25 Content Filtering**: `--query` flag returns only the content relevant to your question (via Fit Markdown)
- **CSS Scoping**: `--selector` flag targets a specific page element
- **Multi-Page Deep Crawl**: `site` mode explores an entire domain up to N levels deep
- **Adaptive Research**: `research` mode automatically stops when it has enough information to answer your query
- **Embedding Strategy**: Optional semantic understanding via local `sentence-transformers` model (no API key needed)
- **PDF Parsing**: URLs ending in `.pdf` are automatically parsed and extracted as text
- **Raw File Access**: Fetch raw content from `raw.githubusercontent.com` or any URL
- **Size & Binary Safety**: Automatic protection against large files (>15KB clipped, >1MB rejected) and binary content (detected via HEAD request + extension)
- **Caching**: `--cache` flag enables persistent cache for faster repeat crawls
- **Metadata Extraction**: Stars, forks, watchers, open issues/PRs, languages with percentages, license from LICENSE file, topics
- **OpenCode Compatible**: Exposed as a custom tool via `.opencode/tools/crawler.ts`

## Installation

```bash
# From PyPI (recommended)
pip install malaclyde-crawler

# With research extras (sentence-transformers for embedding strategy)
pip install "malaclyde-crawler[research]"
```

Or from source:

```bash
pip install -e .
pip install -e ".[research]"                # with sentence-transformers
```

## OpenCode Tool Setup

To use this crawler as a tool inside [OpenCode](https://opencode.ai), copy the tool definition file:

```bash
cp crawler.ts ~/.config/opencode/tools/crawler.ts
```

On the first call within an opencode session, the tool will:

1. Create a Python virtual environment at `~/.cache/opencode/crawler-venv/`
2. Install `malaclyde-crawler` (with research extras) into it via pip
3. Run the requested crawl

This bootstrap takes ~30-60 seconds on the first call (due to downloading dependencies like PyTorch). Subsequent calls use the cached venv and complete normally. The venv is entirely isolated from your system Python — nothing is installed globally.

## Usage

### CLI Overview

```
python -m crawler [mode] <url> [options]

Modes:
  crawl     [default] Extract structured content. Returns JSON.
  fetch     Raw HTTP fetch (no crawl4ai, no GitHub parsing). Returns text.
  download  Download content to disk. Requires -o.
  site      Deep crawl a domain up to N levels. Returns JSONL.
  research  Adaptive crawl — stops when confident about query. Returns JSON.

Flags:
  --query TEXT              BM25 content filter (crawl/site/research)
  --selector CSS            CSS selector scope (crawl/site/research)
  --cache                   Enable persistent cache
  --force-large             Bypass size limits
  --force-binary            Bypass binary detection (download only)
  --skip-preformatting      Skip GitHub recognition (crawl only)
  -o PATH                   Output path (download only)
  --max-depth N             Max crawl depth (site, default: 2)
  --max-pages N             Max pages (site/research, default: 50)
  --confidence 0.0-1.0      Confidence threshold (research, default: 0.7)
  --strategy statistical|embedding  Research strategy (default: statistical)
```

### Examples

```bash
# Crawl a GitHub repository
python -m crawler crawl https://github.com/unclecode/crawl4ai

# Crawl a file (clipped at 15KB)
python -m crawler crawl https://github.com/unclecode/crawl4ai/blob/main/README.md

# Crawl issues
python -m crawler crawl https://github.com/unclecode/crawl4ai/issues

# Crawl a regular web page
python -m crawler crawl https://example.com

# Crawl with BM25 query — only returns query-relevant sections
python -m crawler crawl https://docs.python.org/3/library/asyncio.html --query "task cancellation timeout"

# Crawl with CSS selector — only returns content from that element
python -m crawler crawl https://example.com --selector "h1"

# Crawl with caching enabled (second call is faster)
python -m crawler crawl https://example.com --cache

# Skip GitHub recognition — treat everything as a web page
python -m crawler crawl https://github.com/unclecode/crawl4ai --skip-preformatting

# Fetch raw content (bypasses crawl4ai, returns text)
python -m crawler fetch https://raw.githubusercontent.com/unclecode/crawl4ai/main/.env.txt

# Download a file to disk (blob URLs auto-translated to raw URLs)
python -m crawler download https://github.com/unclecode/crawl4ai/blob/main/.env.txt -o /tmp/env.txt

# Download with force-large (bypasses 1MB limit)
python -m crawler download https://example.com/large.zip -o /tmp/out.zip --force-large

# Site mode — deep crawl a domain
python -m crawler site https://docs.python.org/3/ --max-depth 2 --max-pages 20

# Site mode with query — only pages relevant to your topic
python -m crawler site https://docs.python.org/3/ --max-depth 1 --max-pages 10 --query "async await"

# Research mode — adaptive crawl, stops when confident (statistical strategy)
python -m crawler research https://docs.python.org/3/ --query "async event loop run" --max-pages 10

# Research mode with embedding strategy (local model, no API key needed)
python -m crawler research https://docs.python.org/3/ --query "context manager protocol" --strategy embedding

# PDF auto-detection — .pdf URLs are parsed automatically
python -m crawler crawl https://arxiv.org/pdf/2310.06825.pdf
```

## Modes in Detail

### `crawl` (default)

The primary mode. Classifies URLs (GitHub vs web), dispatches to the correct parser, and returns structured JSON. All GitHub handlers return repo metadata (stars, forks, watchers, languages, license, topics) alongside the content.

- **15KB hybrid clip** — content >15KB is truncated with a warning. `--force-large` bypasses.
- **Binary protection** — binary files are rejected with guidance to use download mode. `--force-binary` bypasses (download mode only).
- **`--query`** enables BM25 filtering. Returns only query-relevant sections via `fit_markdown`.
- **`--selector`** scopes the crawl to a specific CSS element.
- **`--cache`** persists results for faster repeat crawls.
- **PDF auto-detection** — URLs ending in `.pdf` automatically use the PDF parser.

### `fetch`

Raw HTTP fetch using `httpx`. No crawl4ai, no GitHub parsing. Returns raw text to stdout.

- **50KB hybrid clip** with streaming (only downloads first 50KB). `--force-large` bypasses.
- **Binary protection** via extension check + HEAD request Content-Type check.
- Useful for piping content to other tools.

### `download`

Download any content to disk. Requires `-o` for output path.

- **1MB hard cutoff** — pre-check via HEAD request. `--force-large` bypasses.
- **GitHub blob URL translation** — `/blob/` URLs are automatically translated to `raw.githubusercontent.com`.
- **Binary files allowed** — this is the only mode that downloads binaries.

### `site`

Deep crawl a domain using BFS strategy. Crawls up to `--max-depth` levels, limited by `--max-pages`.

- **No size/binary limits** — crawl4ai's own `ContentTypeFilter` handles content filtering.
- **`--query`** enables keyword relevance scoring for prioritized crawling.
- **Returns JSON wrapper** — `{"total": N, "pages": [{"url", "depth", "score", "markdown"}, ...]}`.
- Use for documentation sites, blogs, or any multi-page content.

### `research`

Adaptive crawl that stops when it has enough information to answer your query. Uses three metrics: coverage, consistency, and saturation.

- **No size/binary limits** — relevance scoring is the built-in guard.
- **`--query` is required**.
- **`--strategy statistical`** (default, no extra deps) — term-frequency analysis. Good for technical queries.
- **`--strategy embedding`** — semantic understanding via local `sentence-transformers/all-MiniLM-L6-v2` model. Better for conceptual queries. Requires `pip install 'crawler[research]'`.
- **Returns JSON** — `{"confidence", "pages_crawled", "sources": [{"url", "score", "content"}]}`.

## Supported URL Types

### GitHub URLs

| URL Pattern | Type | Description |
|-------------|------|-------------|
| `github.com/{owner}/{repo}` | `github_repo` | Repository root |
| `github.com/{owner}/{repo}/tree/{ref}/path` | `github_directory` | Directory listing |
| `github.com/{owner}/{repo}/blob/{ref}/path` | `github_file` | File view |
| `github.com/{owner}/{repo}/issues` | `github_issues` | Issues list |
| `github.com/{owner}/{repo}/issues/{num}` | `github_issue` | Individual issue |
| `github.com/{owner}/{repo}/pulls` | `github_pulls` | Pull requests list |
| `github.com/{owner}/{repo}/pull/{num}` | `github_pull` | Individual PR |
| `github.com/{owner}/{repo}/releases` | `github_releases` | Releases |
| `github.com/{owner}/{repo}/wiki` | `github_wiki` | Wiki main page |
| `github.com/{owner}/{repo}/wiki/{page}` | `github_wiki_page` | Wiki page |
| `github.com/{owner}/{repo}/commits/{ref}` | `github_commits` | Commits list |
| `github.com/{owner}/{repo}/commit/{sha}` | `github_commit` | Individual commit |
| `github.com/{owner}/{repo}/actions` | `github_actions` | Actions (fallback) |
| `github.com/{owner}/{repo}/discussions` | `github_discussions` | Discussions (fallback) |
| `github.com/{user}` | `github_user` | User profile (fallback) |
| `gist.github.com/{id}` | `github_gist` | Gist (fallback) |
| `github.com` | `web_page` | GitHub homepage (treated as web) |

### Non-GitHub URLs

Any URL is classified as `web_page` and processed to extract clean markdown. PDF URLs (`.pdf`) are automatically parsed using crawl4ai's PDF strategies.

## Response Models

All responses are Pydantic models serializable to JSON:

### WebPageResponse (`crawl` mode, non-GitHub)
```json
{
  "url": "https://example.com",
  "type": "web_page",
  "markdown": "# Title\n\nContent...",
  "metadata": {"title": "Example"}
}
```
When `--query` is used, `markdown` contains the BM25-filtered `fit_markdown` (only query-relevant sections).

### GitHubRepoResponse (`crawl` mode, GitHub repo/directory)
```json
{
  "url": "https://github.com/owner/repo",
  "type": "github_repo",
  "repo": {
    "owner": "owner",
    "name": "repo",
    "description": "Repo description",
    "stars": 64900,
    "forks": 6600,
    "watchers": 361,
    "open_issues": 23,
    "open_prs": 58,
    "languages": [
      {"name": "Python", "percentage": 98.8},
      {"name": "Other", "percentage": 1.2}
    ],
    "default_branch": "main",
    "license": "Apache License",
    "topics": ["web-crawler", "ai"]
  },
  "readme": {"filename": "README.md", "content": "# Repo\n\nDescription..."},
  "files": [
    {"name": "src", "href": "...", "type": "dir"},
    {"name": "README.md", "href": "...", "type": "file"}
  ],
  "pagination": null
}
```

### GitHubFileResponse (`crawl` mode, GitHub file)
```json
{
  "url": "https://github.com/owner/repo/blob/main/file.py",
  "type": "github_file",
  "repo": { "... repo metadata ..." },
  "file": {
    "name": "file.py",
    "path": "file.py",
    "size": "4.2 KB",
    "lines": 120
  },
  "raw_url": "https://raw.githubusercontent.com/...",
  "content": "print('hello')"
}
```

### GitHubSecondaryResponse (`crawl` mode, issues/PRs/releases/wiki/commits)
```json
{
  "url": "https://github.com/owner/repo/issues",
  "type": "github_issues",
  "repo": { "... repo metadata ..." },
  "markdown": "# Issues\n\n- Issue 1...",
  "metadata": {"count": 5}
}
```

### Site Mode Response
```json
{
  "total": 5,
  "pages": [
    {
      "url": "https://docs.python.org/3/",
      "depth": 0,
      "score": 0.0,
      "markdown": "# Python 3 Documentation\n\n..."
    }
  ]
}
```

### Research Mode Response
```json
{
  "mode": "research",
  "query": "async event loop",
  "strategy": "statistical",
  "confidence": 0.723,
  "pages_crawled": 8,
  "sources": [
    {
      "url": "https://docs.python.org/3/library/asyncio-eventloop.html",
      "score": 0.85,
      "content": "Event loops run asynchronous tasks..."
    }
  ]
}
```

## Python API

```python
import asyncio
from crawler.crawler import crawl

async def main():
    # Crawl a GitHub repo
    result = await crawl("https://github.com/unclecode/crawl4ai")
    print(result.type)  # "github_repo"
    print(result.repo.stars)  # 64900
    print(result.repo.languages)  # [LanguageStats(name='Python', percentage=98.8)]
    
    # Crawl with BM25 query
    result = await crawl("https://docs.python.org/3/", mode="crawl", query="async event loop")
    print(result.markdown)  # Only query-relevant sections
    
    # Deep crawl
    result = await crawl("https://docs.python.org/3/", mode="site", max_depth=2, max_pages=10)
    print(result["total"])  # Number of pages crawled
    
    # Research
    result = await crawl("https://docs.python.org/3/", mode="research", query="async await")
    print(result["confidence"])  # How confident the crawler is
    print(result["sources"])  # Most relevant pages

asyncio.run(main())
```

## Architecture

```
crawler/
├── __init__.py              # Package init, crawl4ai monkey-patches
├── __main__.py              # CLI entry point (5 modes)
├── crawler.py               # Main orchestrator + site/research/PDF handlers
├── models.py                # Pydantic response models
├── url_classifier.py        # URL type detection (20+ GitHub types)
├── github_url.py            # URL utilities (raw URL construction)
├── raw_fetcher.py           # Raw file fetching (README, license)
├── raw_http.py              # Raw HTTP client (HEAD, streaming GET)
├── repo_metadata.py         # Repo metadata extraction (stars, forks, etc.)
├── safety.py                # Binary/size limit checks
├── parsers/
│   ├── web_page.py          # Non-GitHub pages (supports --query, --selector, --cache)
│   ├── repo.py              # Repo/directory pages
│   ├── file.py              # File (blob) pages
│   ├── issues.py            # Issues pages
│   ├── pulls.py             # PR pages
│   ├── releases.py          # Releases pages
│   ├── wiki.py              # Wiki pages
│   ├── commits.py           # Commits pages
│   └── fallback.py          # Generic GitHub pages
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Saved HTML fixtures
├── collect_fixtures.py      # Fixture collection script
├── test_setup.py
├── test_models.py
├── test_url_classifier.py
├── test_github_url.py
├── test_raw_fetcher.py
├── test_repo_metadata.py
├── test_raw_http.py
├── test_safety.py
├── test_web_page.py
├── test_repo.py
├── test_file.py
├── test_crawler.py
├── test_cli.py
└── test_live.py             # Opt-in live tests (@pytest.mark.live)
.opencode/
└── tools/
    └── crawler.ts            # Opencode tool wrapper
```

## Safety Features

| Mode | Binary Protection | Size Limit | Mechanism |
|---|---|---|---|
| `crawl` | HEAD + extension check | 15KB hybrid clip | Pre-check via extension/HEAD; clip in post-processing |
| `fetch` | HEAD + extension check | 50KB hybrid clip | Streaming GET stops at 50KB |
| `download` | None (binaries allowed) | 1MB hard cutoff | HEAD pre-check, rejected before download |
| `site` | None | None | crawl4ai's ContentTypeFilter |
| `research` | None | None | Built-in relevance scoring |

All limits bypassed with `--force-large`. Binary protection bypassed with `--force-binary` (download only).

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Expected failure (binary detected, size exceeded, usage error) |
| 2 | Unexpected error (network failure, exception) |

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_url_classifier.py -v

# Run live tests (requires network, opt-in)
pytest -m live --timeout=60

# Run with coverage
pytest --cov=crawler --cov-report=html
```

## Development

1. Install dependencies: `pip install -r requirements.txt`
2. For research embedding strategy: `pip install -e ".[research]"`
3. Make changes
4. Run tests: `pytest`

## License

MIT
