"""Plugin for running Robot Framework tests with Twister harness."""
import logging

import pytest

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add Robot Framework specific options to twister harness."""
    group = parser.getgroup("twister")

    group.addoption(
        "--twister-with-robot",
        action="store_true", 
        default=False,
        help="Run Robot Framework tests with Twister harness"
    )


def pytest_configure(config):
    """Configure the plugin."""
    if config.getoption("--twister-with-robot"):
        config.addinivalue_line(
            "markers",
            "robotframework: mark test as Robot Framework test to run with Twister harness"
        )
        logger.info("✅ Robot Framework Twister plugin configured")


# Import collector to register the hook
from .collector import pytest_collect_file
