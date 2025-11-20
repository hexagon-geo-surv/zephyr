# robotframework-twister-harness/README.rst
==============================
Robot Framework Twister Harness
==============================

A Robot Framework integration for Zephyr Twister that enables shared device access
without resource contention.

Overview
--------

This package provides:

- Shared device access between Robot Framework and other test tools
- No serial port contention issues
- Full integration with Zephyr Twister test framework
- Robot Framework native keywords and syntax
- Support for all Twister device types (native, QEMU, hardware)

Installation
------------

.. code-block:: bash

    pip install robotframework-twister-harness

    # Or from source
    git clone https://github.com/zephyrproject-rtos/robotframework-twister-harness
    cd robotframework-twister-harness
    pip install -e .

Usage with Twister
------------------

.. code-block:: bash

    # Run Robot Framework tests with Twister
    ./scripts/twister -p native_sim -T samples/robot_tests/ --robot-handler

    # Mixed pytest and Robot Framework tests
    ./scripts/twister -p qemu_x86 -T tests/ --test-type pytest,robot

Standalone Usage
----------------

.. code-block:: robot

    *** Settings ***
    Library    robotframework_twister_harness.libraries.ProxyTwisterLibrary

    *** Test Cases ***
    Example Test
        Open Device Connection    proxy_host=localhost    proxy_port=8888
        Write To Device    help
        ${response}=    Read From Device
        Should Contain    ${response}    Available commands
        Close Device Connection

Architecture
------------

The solution uses a device proxy pattern:

1. **DeviceProxy**: Manages exclusive device access
2. **SocketBridge**: Provides TCP access to the proxy  
3. **RobotHandler**: Twister integration handler
4. **ProxyTwisterLibrary**: Robot Framework library

This eliminates resource contention by having a single process manage the device
connection while multiple clients (Robot Framework, pytest, etc.) communicate
through the proxy.

License
-------

Apache 2.0
