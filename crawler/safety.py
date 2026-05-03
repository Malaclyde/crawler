"""Binary and size safety checks for the crawl mode."""

import logging
import sys

from .raw_http import BINARY_ERROR_MSG, check_url, is_binary_url, _guess_type_from_extension

logger = logging.getLogger(__name__)

SIZE_CLIP_WARNING = "\n... [content clipped at {limit} bytes — use --force-large to download the full file without clipping]"

MAX_CRAWL_BYTES = 15 * 1024
MAX_FETCH_BYTES = 50 * 1024
MAX_DOWNLOAD_BYTES = 1024 * 1024


async def check_binary(url: str, force_binary: bool = False) -> None:
    if force_binary:
        return
    ext_type = _guess_type_from_extension(url)
    if ext_type == "application/octet-stream":
        logger.error("Binary detected via extension: %s", url)
        print(BINARY_ERROR_MSG, file=sys.stderr)
        sys.exit(1)
    ct, _ = await check_url(url)
    if ct and is_binary_url(url, ct):
        logger.error("Binary detected via Content-Type (%s): %s", ct, url)
        print(BINARY_ERROR_MSG, file=sys.stderr)
        sys.exit(1)


async def check_binary_for_raw_url(
    owner: str, repo: str, ref: str, filepath: str, force_binary: bool = False
) -> None:
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{filepath}"
    await check_binary(raw_url, force_binary=force_binary)


def clip_content(
    content: str,
    max_bytes: int,
    force_large: bool = False,
) -> str:
    if force_large:
        return content
    encoded = content.encode("utf-8")
    if len(encoded) > max_bytes:
        clipped = encoded[:max_bytes].decode("utf-8", errors="replace")
        clipped += SIZE_CLIP_WARNING.format(limit=max_bytes)
        return clipped
    return content
