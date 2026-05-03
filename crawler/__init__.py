"""GitHub-aware web crawler package."""

import logging
import sys

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.async_logger import AsyncLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
    stream=sys.stderr,
)

# Suppress crawl4ai's verbose initialization output
_silent_logger = AsyncLogger(verbose=False)
_original_crawler_init = AsyncWebCrawler.__init__


def _silent_crawler_init(self, *args, **kwargs):
    if "logger" not in kwargs:
        kwargs["logger"] = _silent_logger
    _original_crawler_init(self, *args, **kwargs)


AsyncWebCrawler.__init__ = _silent_crawler_init

# Make CrawlerRunConfig default verbose=False via user defaults
CrawlerRunConfig._user_defaults["verbose"] = False

# Monkey-patch EmbeddingStrategy to support n_query_variations=0 offline
try:
    from crawl4ai.adaptive_crawler import EmbeddingStrategy
    from crawl4ai.utils import get_text_embeddings
    _original_map = EmbeddingStrategy.map_query_semantic_space

    async def _patched_map_semantic(self, query: str, n_synthetic: int = 10):
        if n_synthetic <= 0:
            emb = await get_text_embeddings([query])
            return emb, [query]
        return await _original_map(self, query, n_synthetic)

    EmbeddingStrategy.map_query_semantic_space = _patched_map_semantic
except (ImportError, AttributeError):
    pass

