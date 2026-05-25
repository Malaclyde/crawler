"""Crawler plugin for Hermes Agent — wraps malaclyde-crawler."""
import json
import logging
import subprocess

logger = logging.getLogger(__name__)


def register(ctx):
    tools = [
        {
            "name": "crawler_crawl",
            "description": "Extract structured content from a single URL with optional BM25 filtering. Best for: reading docs, GitHub repos, issues, PRs, or any single page.",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to crawl"},
                    "query": {"type": "string", "description": "Optional BM25 content filter — returns only text relevant to this query"},
                    "selector": {"type": "string", "description": "Optional CSS selector to scope extraction"},
                },
                "required": ["url"],
            },
        },
        {
            "name": "crawler_site",
            "description": "Deep crawl an entire domain up to N levels deep. Returns structured JSONL. Best for: documentation sites, blogs, knowledge bases.",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Starting URL for deep crawl"},
                    "max_depth": {"type": "integer", "default": 2, "minimum": 1, "maximum": 5, "description": "Maximum crawl depth"},
                    "max_pages": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100, "description": "Maximum pages to crawl"},
                    "query": {"type": "string", "description": "Optional keyword relevance filter"},
                },
                "required": ["url"],
            },
        },
        {
            "name": "crawler_research",
            "description": "Adaptive crawl that stops when confident about answering a question. Best for: answering a specific question by searching across a domain.",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Starting URL for research"},
                    "query": {"type": "string", "description": "The research question to answer"},
                    "max_pages": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50, "description": "Maximum pages to crawl"},
                },
                "required": ["url", "query"],
            },
        },
        {
            "name": "crawler_fetch",
            "description": "Raw HTTP fetch — returns the raw text/HTML content from a URL without any processing.",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                },
                "required": ["url"],
            },
        },
    ]

    for t in tools:
        name = t["name"]
        handler = _make_handler(name)
        ctx.register_tool(
            name=name,
            toolset="crawler",
            schema=t["schema"],
            handler=handler,
            description=t["description"],
        )


def _make_handler(mode):
    def handler(params, **kwargs):
        return _run_crawler(mode, params)
    return handler


def _run_crawler(mode, params):
    # Strip "crawler_" prefix if present to get the CLI mode
    cli_mode = mode.replace("crawler_", "")
    url = params.get("url", "")
    cmd = ["python3", "-m", "crawler", cli_mode, url]

    flag_map = {
        "crawler_crawl": [("query", "--query"), ("selector", "--selector")],
        "crawler_site": [("query", "--query"), ("max_depth", "--max-depth"), ("max_pages", "--max-pages")],
        "crawler_research": [("query", "--query"), ("max_pages", "--max-pages")],
        "crawler_fetch": [],
    }

    for param_key, flag in flag_map.get(mode, []):
        val = params.get(param_key)
        if val is not None:
            cmd.extend([flag, str(val)])

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            error_msg = r.stderr.strip() or f"Exit code {r.returncode}"
            return json.dumps({"error": error_msg})
        output = r.stdout.strip()
        if not output:
            return json.dumps({"result": "ok"})
        return output
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "crawler timed out after 120s"})
    except FileNotFoundError:
        return json.dumps({
            "error": "malaclyde-crawler not installed. Run: pip install malaclyde-crawler",
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
