"""CLI entry point for the crawler with site and research modes."""

import argparse
import asyncio
import json
import sys

from .crawler import crawl, download


def build_parser():
    """Build argument parser."""
    p = argparse.ArgumentParser(
        prog="python -m crawler",
        description="GitHub-aware web crawler",
        usage="python -m crawler [mode] <url> [options]",
    )
    p.add_argument(
        "mode", nargs="?",
        help="Operation mode: crawl (default), fetch, download, site, research",
    )
    p.add_argument("url", help="URL to process")
    p.add_argument("-o", "--output", help="Output file path (required for download mode)")
    p.add_argument("--force-large", action="store_true", help="Bypass size limits")
    p.add_argument("--force-binary", action="store_true", help="Bypass binary detection (download mode only)")
    p.add_argument("--skip-preformatting", action="store_true", help="Skip GitHub recognition (crawl mode only)")
    p.add_argument("--query", help="Content query for BM25 filtering (crawl/site/research)")
    p.add_argument("--selector", help="CSS selector to scope crawling")
    p.add_argument("--cache", action="store_true", help="Enable crawl4ai cache")
    p.add_argument("--max-depth", type=int, default=2, help="Max crawl depth (site mode)")
    p.add_argument("--max-pages", type=int, default=50, help="Max pages to crawl (site/research)")
    p.add_argument("--confidence", type=float, default=0.7, help="Confidence threshold (research mode)")
    p.add_argument("--strategy", default="statistical", choices=["statistical", "embedding"],
                   help="Adaptive strategy (research mode)")
    return p


async def main():
    known_modes = {"crawl", "fetch", "download", "site", "research"}
    raw = sys.argv[1:] if len(sys.argv) > 1 else []

    if not raw:
        build_parser().print_help()
        sys.exit(1)

    mode = "crawl"
    rest = list(raw)

    if rest[0] in known_modes:
        mode = rest.pop(0)

    parser = build_parser()
    args = parser.parse_args([mode] + rest)

    if args.mode == "download" and not args.output:
        parser.error("download mode requires -o/--output")
    if args.force_binary and args.mode != "download":
        parser.error("--force-binary is only valid in download mode")
    if args.skip_preformatting and args.mode != "crawl":
        parser.error("--skip-preformatting is only valid in crawl mode")
    if args.mode == "research" and not args.query:
        parser.error("research mode requires --query")
    if args.strategy == "embedding" and args.mode != "research":
        parser.error("--strategy embedding is only valid in research mode")

    try:
        if args.mode in ("crawl", "fetch"):
            result = await crawl(
                args.url,
                mode=args.mode,
                force_large=args.force_large,
                force_binary=args.force_binary,
                skip_preformatting=args.skip_preformatting,
                query=args.query,
                selector=args.selector,
                cache=args.cache,
            )
            if args.mode == "crawl":
                json.dump(result.model_dump(), sys.stdout, indent=2)
                print()
            else:
                sys.stdout.write(result)
                sys.stdout.flush()

        elif args.mode == "site":
            result = await crawl(
                args.url,
                mode="site",
                query=args.query,
                selector=args.selector,
                cache=args.cache,
                max_depth=args.max_depth,
                max_pages=args.max_pages,
                force_large=args.force_large,
            )
            json.dump(result, sys.stdout, indent=2)
            print()

        elif args.mode == "research":
            result = await crawl(
                args.url,
                mode="research",
                query=args.query,
                cache=args.cache,
                max_pages=args.max_pages,
                confidence=args.confidence,
                strategy=args.strategy,
                selector=args.selector,
            )
            json.dump(result, sys.stdout, indent=2)
            print()

        elif args.mode == "download":
            await download(
                args.url,
                args.output,
                force_large=args.force_large,
                force_binary=args.force_binary,
            )

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
