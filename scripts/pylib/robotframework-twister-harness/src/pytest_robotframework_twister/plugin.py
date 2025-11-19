"""Main plugin for Robot Framework Twister integration."""
import logging

import pytest

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add Robot Framework specific options to twister harness."""
    group = parser.getgroup("robotframework-twister")

    group.addoption(
        "--twister-robot-test-dir",
        action="store",
        default=None,
        help="Directory containing Robot Framework test files"
    )

    group.addoption(
        "--twister-robot-vars",
        action="store", 
        default=None,
        help="Path to Robot Framework variable file"
    )

    group.addoption(
        "--twister-with-robot",
        action="store_true",
        default=False,
        help="Enable Robot Framework integration with Twister"
    )


def pytest_configure(config):
    """Configure the plugin."""
    if config.getoption("--twister-with-robot"):
        config.addinivalue_line(
            "markers",
            "robotframework: mark test as Robot Framework test to run with Twister harness"
        )


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on Robot Framework options."""
    if not config.getoption("--twister-with-robot"):
        # Remove Robot Framework tests if not enabled
        items[:] = [item for item in items if "robotframework" not in item.keywords]
