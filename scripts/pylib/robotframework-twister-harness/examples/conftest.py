"""Example conftest.py for Robot Framework Twister tests."""
import pytest


@pytest.fixture
def robot_custom_variables():
    """Add custom variables for Robot Framework tests."""
    return {
        "CUSTOM_TIMEOUT": "30s",
        "TEST_ITERATIONS": "5"
    }
