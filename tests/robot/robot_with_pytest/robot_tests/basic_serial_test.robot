# [file name]: tests/robot/robot_with_pytest/robot_tests/basic_serial_test.robot
*** Settings ***
Documentation    Basic serial communication test with debugging
Library          SerialLibrary
Library          Collections
Library          String
Library          Process

*** Variables ***
${SERIAL_PORT}    ${DEVICE_SERIAL}
${BAUDRATE}       ${DEVICE_BAUDRATE}

*** Test Cases ***
Test Serial Connection
    [Documentation]    Basic test that serial connection works
    Log    Testing serial connection to ${SERIAL_PORT} at ${BAUDRATE} baud

    # Open serial port with correct arguments
    Open Port    ${SERIAL_PORT}
    Set Baudrate    ${BAUDRATE}

    # Clear any existing data
    ${initial_data}=    Read Data
    Log    Initial data in buffer: ${initial_data}

    # Send a simple command
    Write Data    HELP\n
    Log    Sent HELP command

    # Try to read response with multiple attempts
    FOR    ${i}    IN RANGE    10
        ${response}=    Read Data    timeout=1
        Log    Attempt ${i}: Received: ${response}
        ${contains_commands}=    Evaluate    'Available commands:' in '''${response}'''
        Exit For Loop If    ${contains_commands}
        Sleep    0.5s
    END

    # Check if we got the expected response
    Should Contain    ${response}    Available commands:
    Should Contain    ${response}    HELP

    Close Port

Test Simple Echo
    [Documentation]    Test basic echo functionality
    Open Port    ${SERIAL_PORT}
    Set Baudrate    ${BAUDRATE}

    # Clear buffer
    Read Data    timeout=0.5

    # Send echo command
    Write Data    ECHO Test123\n

    # Read response
    FOR    ${i}    IN RANGE    10
        ${response}=    Read Data    timeout=1
        Log    Echo attempt ${i}: ${response}
        ${contains_echo}=    Evaluate    'ECHO:' in '''${response}''' and 'Test123' in '''${response}'''
        Exit For Loop If    ${contains_echo}
        Sleep    0.5s
    END

    Should Contain    ${response}    ECHO: Test123
    Close Port

Test Version Command
    [Documentation]    Test version command
    Open Port    ${SERIAL_PORT}
    Set Baudrate    ${BAUDRATE}

    # Clear buffer
    Read Data    timeout=0.5

    # Send version command
    Write Data    VERSION\n

    # Read response
    FOR    ${i}    IN RANGE    10
        ${response}=    Read Data    timeout=1
        Log    Version attempt ${i}: ${response}
        ${contains_version}=    Evaluate    'FIRMWARE_VERSION:' in '''${response}'''
        Exit For Loop If    ${contains_version}
        Sleep    0.5s
    END

    Should Contain    ${response}    FIRMWARE_VERSION:
    Should Contain    ${response}    1.0.0
    Should Contain    ${response}    ${DEVICE_PLATFORM}

    Close Port
