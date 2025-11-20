# tests/robot/robot_with_pytest/robot_tests/serial_communication_test.robot
*** Settings ***
Documentation    Test actual serial communication with the flashed device
Library          Collections
Library          String
Library          OperatingSystem
Library          SerialKeywords.py

Suite Setup      Log Device Information
Suite Teardown   Close Serial Port If Open

*** Variables ***
${SERIAL_PORT}    ${DEVICE_SERIAL}
${BAUDRATE}       ${DEVICE_BAUDRATE}
${RESPONSE_TIMEOUT}    10

*** Test Cases ***
Test Device Responds To Commands
    [Documentation]    Verify the flashed device actually responds over serial
    Open Serial Port    ${SERIAL_PORT}    ${BAUDRATE}
    Wait For Device Ready

    # Send a command to the device
    Write Serial Data    HELP

    # Wait for and verify the response
    ${response}=    Read Serial Data Until    Available commands:    ${RESPONSE_TIMEOUT}
    Should Contain    ${response}    ECHO
    Should Contain    ${response}    VERSION
    Should Contain    ${response}    HELP

Test Version Command
    [Documentation]    Test VERSION command response
    Open Serial Port    ${SERIAL_PORT}    ${BAUDRATE}
    Wait For Device Ready

    Write Serial Data    VERSION
    ${response}=    Read Serial Data Until    FIRMWARE_VERSION:    ${RESPONSE_TIMEOUT}
    Should Contain    ${response}    1.0.0
    Should Contain    ${response}    ${DEVICE_PLATFORM}

Test Echo Command
    [Documentation]    Test ECHO command functionality
    Open Serial Port    ${SERIAL_PORT}    ${BAUDRATE}
    Wait For Device Ready

    Write Serial Data    ECHO Hello from Robot Framework
    ${response}=    Read Serial Data Until    ECHO: Hello from Robot Framework    ${RESPONSE_TIMEOUT}
    Should Contain    ${response}    Hello from Robot Framework

*** Keywords ***
Log Device Information
    [Documentation]    Log information about the test environment
    Log    Testing device: ${DEVICE_PLATFORM}
    Log    Serial port: ${DEVICE_SERIAL}
    Log    Baud rate: ${DEVICE_BAUDRATE}
    Log    Build directory: ${BUILD_DIR}

Wait For Device Ready
    [Documentation]    Wait for device to be ready for commands
    Sleep    2s    # Wait for device to initialize
    Clear Serial Buffer

Close Serial Port If Open
    [Documentation]    Ensure serial port is closed after tests
    Close Serial Port
