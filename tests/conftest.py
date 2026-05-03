"""Shared fixtures and pytest configuration."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as 'live' unless explicitly requested with -m live."""
    if not config.getoption("-m") or "live" not in config.getoption("-m"):
        for item in items:
            if "live" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="Use `pytest -m live --timeout=60` to run live tests")
                )
