"""Configuration for Robot Framework Twister tests."""
import time
from typing import Generator

import pytest
import serial


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "robotframework: mark test as Robot Framework test to run with Twister harness"
    )


@pytest.fixture
def serial_connection(device) -> Generator[serial.Serial, None, None]:
    """Create a serial connection to the device."""
    ser = serial.Serial(
        port=device.device_config.serial,
        baudrate=int(device.device_config.baudrate),
        timeout=5.0,
        write_timeout=5.0
    )

    # Clear any pending data
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    yield ser

    # Cleanup
    ser.close()


@pytest.fixture
def robot_custom_variables(device, serial_connection) -> dict:
    """Add custom variables for Robot Framework tests."""
    return {
        "BOARD_NAME": "nucleo_g474re",
        "TEST_TIMEOUT": "30",
        "SERIAL_PORT": device.device_config.serial,
        "BAUD_RATE": device.device_config.baudrate,
        "COMMAND_DELAY": "0.5"
    }
