"""Tests for Robot Framework Twister integration."""
import pytest


@pytest.mark.robotframework
def test_robot_framework_integration(robot_framework_runner, robot_framework_variables):
    """Test basic Robot Framework integration."""
    # This would be a real test using the fixtures
    runner = robot_framework_runner
    variables = robot_framework_variables

    # Verify we have device configuration
    assert "DEVICE_PLATFORM" in variables
    assert "BUILD_DIR" in variables
    assert runner is not None
