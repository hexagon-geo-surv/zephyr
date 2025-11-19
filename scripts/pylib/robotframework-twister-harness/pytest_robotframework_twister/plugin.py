"""Plugin for running Robot Framework tests with Twister harness."""
import pytest
from typing import Dict, Any, Optional
import logging

# Import the collector classes
from .collector import RobotFrameworkTestFile

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add Robot Framework specific options to twister harness."""
    # Use a unique prefix to avoid conflicts
    group = parser.getgroup("twister-robot")
    
    # Use completely unique option names
    group.addoption(
        "--twister-with-robot",
        action="store_true",
        default=False,
        help="Run Robot Framework tests with Twister harness"
    )
    group.addoption(
        "--twister-robot-test-dir",
        action="store",
        default="robot_tests",
        help="Directory containing Robot Framework test files for Twister"
    )
    group.addoption(
        "--twister-robot-vars",
        action="append",
        default=[],
        help="Robot Framework variable files for Twister tests"
    )
    logger.info("Robot Framework Twister options added")


def pytest_configure(config):
    """Configure the plugin."""
    logger.info(f"pytest_configure called, twister-with-robot: {config.getoption('--twister-with-robot')}")
    if config.getoption("--twister-with-robot"):
        # Register our marker
        config.addinivalue_line(
            "markers",
            "twister_robot: mark test as Robot Framework test to run with Twister harness"
        )
        logger.info("Robot Framework Twister plugin configured")


@pytest.hookimpl(tryfirst=True)
def pytest_collect_file(file_path, path, parent):
    """Collect Robot Framework test files when the option is enabled."""
    twister_with_robot = parent.config.getoption("--twister-with-robot")
    logger.info(f"pytest_collect_file: {file_path}, twister-with-robot: {twister_with_robot}")
    
    if not twister_with_robot:
        return None

    logger.info(f"Checking file: {file_path}, suffix: {file_path.suffix}")
    
    if file_path.suffix.lower() in ('.robot', '.resource'):
        logger.info(f"Collecting Robot Framework file: {file_path}")
        return RobotFrameworkTestFile.from_parent(parent, path=file_path)
    
    return None
