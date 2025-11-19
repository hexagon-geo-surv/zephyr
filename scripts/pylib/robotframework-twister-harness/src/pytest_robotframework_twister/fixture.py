"""Fixtures for Robot Framework Twister integration."""
import logging

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
def robot_framework_variables(request):
    """Provide common variables for Robot Framework tests."""
    # This fixture can be used by tests that need Robot Framework variables
    build_dir = request.config.getoption("--build-dir", "")

    return {
        "BUILD_DIR": build_dir,
        "DEVICE_PLATFORM": request.config.getoption("--platform", ""),
    }
