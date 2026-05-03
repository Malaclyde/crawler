"""Raw HTTP client for fetch and download modes (bypasses crawl4ai)."""

import logging
from typing import Tuple
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".rst", ".txt",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".html", ".htm", ".css", ".scss", ".less",
    ".c", ".cpp", ".h", ".hpp", ".java", ".rs", ".go", ".rb",
    ".sh", ".bash", ".zsh", ".fish",
    ".xml", ".svg", ".csv", ".log",
    ".sql", ".r", ".lua", ".php", ".pl", ".pm",
    ".tex", ".bib",
    ".gitignore", ".env", ".editorconfig",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".ttf", ".otf", ".woff", ".woff2",
    ".o", ".a", ".lib", ".obj",
    ".class", ".jar",
    ".db", ".sqlite",
    ".wasm",
}

BINARY_ERROR_MSG = (
    "Error: URL points to a binary file.\n"
    "Use download mode to fetch binaries:\n"
    "  python -m crawler download <url> -o <path>\n"
    "Add --force-binary to bypass this check:\n"
    "  python -m crawler download <url> -o <path> --force-binary"
)


def _guess_type_from_extension(url: str) -> str | None:
    path = urlparse(url).path.lower()
    for ext in TEXT_EXTENSIONS:
        if path.endswith(ext):
            return "text/plain"
    for ext in BINARY_EXTENSIONS:
        if path.endswith(ext):
            return "application/octet-stream"
    return None


async def check_url(url: str) -> Tuple[str | None, int | None]:
    logger.info("HEAD %s", url)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.head(url, follow_redirects=True, timeout=30)
            if r.status_code >= 400:
                logger.warning("HEAD %s returned %d", url, r.status_code)
                return None, None
            ct = r.headers.get("content-type")
            cl = r.headers.get("content-length")
            cl = int(cl) if cl else None
            return ct, cl
        except httpx.TimeoutException:
            logger.warning("HEAD %s timed out", url)
            return None, None
        except Exception as e:
            logger.warning("HEAD %s failed: %s", url, e)
            return None, None


def is_binary_url(url: str, content_type: str | None = None) -> bool:
    ext_type = _guess_type_from_extension(url)
    if ext_type is not None:
        return ext_type == "application/octet-stream"
    if content_type:
        ct = content_type.lower()
        if "text/" in ct or "application/json" in ct or "application/xml" in ct:
            return False
        if "application/octet-stream" in ct or "application/x-binary" in ct:
            return True
        if ct.startswith("application/") and any(x in ct for x in ["javascript", "ecmascript"]):
            return False
    return False


async def fetch_raw(url: str, max_bytes: int | None = None) -> str:
    logger.info("GET %s (max_bytes=%s)", url, max_bytes)
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url, follow_redirects=True, timeout=60) as r:
            r.raise_for_status()
            if max_bytes is None:
                content = await r.aread()
                return content.decode("utf-8", errors="replace")
            chunks = []
            total = 0
            async for chunk in r.aiter_bytes():
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    break
            content = b"".join(chunks)[:max_bytes].decode("utf-8", errors="replace")
            if total > max_bytes:
                content += f"\n... [content clipped at {max_bytes} bytes — use --force-large to download the full file]"
            return content
