Robot Framework with Pytest Twister Harness Example
===================================================

This example demonstrates how to use Robot Framework with the pytest-twister-harness
to test Zephyr applications on hardware.

Features
--------

- Zephyr application with command interface over UART
- Robot Framework tests for hardware validation
- Integration with Twister test harness
- Serial communication testing
- Device configuration validation

Requirements
------------

- Zephyr RTOS environment
- nucleo_g474re board
- Python packages:
  - pytest-twister-harness
  - robotframework
  - robotframework-seriallibrary
  - pyserial

Building and Testing
--------------------

1. Build the application::

    twister --platform nucleo_g474re --build-only -T test/robot/robot_with_pytest

2. Run Robot Framework tests::

    twister --platform nucleo_g474re --device-testing \
      --twister-with-robot \
      --twister-robot-test-dir=test/robot/robot_with_pytest/robot_tests \
      --twister-robot-vars=test/robot/robot_with_pytest/robot_tests/variables.py \
      -T test/robot/robot_with_pytest \
      -v

Test Structure
--------------

- ``src/main.c``: Zephyr application with UART command interface
- ``robot_tests/``: Robot Framework test suites
- ``sample.yaml``: Twister test configuration

Available Commands
------------------

The firmware supports these commands over UART:

- ``ECHO <text>`` - Echo back text
- ``LED ON|OFF`` - Control onboard LED
- ``VERSION`` - Show firmware version
- ``HELP`` - Show available commands
- ``RESET`` - Reset the device
