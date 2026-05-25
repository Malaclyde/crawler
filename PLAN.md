# Crawler Hermes Plugin — Implementation Plan

## Overview
Add a Hermes plugin at the root of this repo. Move `crawler.ts` to `opencode/`, create Python Hermes plugin at root.

## Step 1: Move OpenCode tool
Move `crawler.ts` → `opencode/crawler.ts`
No CI changes needed (no workflow references to crawler.ts at root).

## Step 2: Create Hermes plugin at root

### `plugin.yaml`
```yaml
name: crawler
version: "1.0.0"
description: "GitHub-aware web crawler — extract clean markdown from repos, docs, and websites"
```

### `__init__.py`
Register 4 tools via `ctx.register_tool()`:
- `crawler_crawl`, `crawler_site`, `crawler_research`, `crawler_fetch`

All handlers shell out to `python3 -m crawler <mode> <url> [options]`
Use `subprocess.run()` with `capture_output=True, timeout=120`.

### Tool Schemas

**`crawler_crawl`**: `url` (required), `query` (optional BM25 filter), `selector` (optional CSS selector)
**`crawler_site`**: `url` (required), `max_depth` (optional int, default 2), `max_pages` (optional int, default 20), `query` (optional)
**`crawler_research`**: `url` (required), `query` (required research question), `max_pages` (optional int, default 10)
**`crawler_fetch`**: `url` (required)

### Handler Pattern (all 4 tools)
```python
import subprocess, json, shlex

def _run_crawler(mode: str, url: str, **kwargs) -> str:
    cmd = ["python3", "-m", "crawler", mode, url]
    for k, v in kwargs.items():
        if v is not None:
            cmd.extend([f"--{k.replace('_', '-')}", str(v)])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return json.dumps({"error": r.stderr})
        return r.stdout or json.dumps({"result": "ok"})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "crawler timed out after 120s"})
```

## Step 3: Update README
- Add Hermes Plugin section with install instructions and tool docs
- Update architecture diagram to show new structure
- Note: requires `pip install malaclyde-crawler` in Hermes environment
