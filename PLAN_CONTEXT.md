# Plan: Crawler Hermes Plugin

## Goal
Add a Hermes plugin to this repo at the root level, making the repo installable via `hermes plugins install Malaclyde/crawler`.

## Current State
- Root has: `crawler.ts`, `crawler/` (Python package), `tests/`, `pyproject.toml`, `README.md`, `.github/workflows/`
- `crawler.ts` is an OpenCode tool (TypeScript)
- The Python package `malaclyde-crawler` is published on PyPI

## What Needs to Happen

### Step 1: Move OpenCode tool
- Move `crawler.ts` → `opencode/crawler.ts`
- Update `.github/workflows/` if needed

### Step 2: Create Hermes plugin at root
Files to create:
- `plugin.yaml` — manifest
- `__init__.py` — plugin registration code

The plugin uses the `malaclyde-crawler` PyPI package (imported via `from crawler.crawler import ...` or shelling out via `python3 -m crawler ...`).

### Step 3: Register Hermes tools
The plugin should register these tools via `ctx.register_tool()`:

1. **`crawler_crawl`** — Single page with BM25 filtering
   - Parameters: `url` (required), `query` (optional BM25 filter), `selector` (optional CSS selector)
   - Calls: `python3 -m crawler crawl <url> --query <query>` or imports `crawler` directly
   - Toolset: `crawler`

2. **`crawler_site`** — Deep crawl a domain
   - Parameters: `url` (required), `max_depth` (optional, default 2), `max_pages` (optional, default 20), `query` (optional)
   - Calls: `python3 -m crawler site <url> --max-depth N --max-pages N`
   - Toolset: `crawler`

3. **`crawler_research`** — Adaptive research crawl
   - Parameters: `url` (required), `query` (required), `max_pages` (optional, default 10)
   - Calls: `python3 -m crawler research <url> --query <query>`
   - Toolset: `crawler`

4. **`crawler_fetch`** — Raw HTTP fetch
   - Parameters: `url` (required)
   - Calls: `python3 -m crawler fetch <url>`
   - Toolset: `crawler`

### Step 4: Update README
- Document the Hermes plugin alongside the OpenCode tool
- Installation instructions for both

## References
- Hermes plugin system: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- Build a Hermes plugin: https://hermes-agent.nousresearch.com/docs/guides/build-a-hermes-plugin
- Crawler CLI: `python3 -m crawler --help`
