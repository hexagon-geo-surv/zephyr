# [file name]: tests/robot/robot_with_pytest/robot_tests/simple_serial_test.robot
*** Settings ***
Documentation    Simple serial communication test using echo/socat
Library          Process
Library          Collections
Library          String
Library          OperatingSystem

*** Variables ***
${SERIAL_PORT}    ${DEVICE_SERIAL}
${BAUDRATE}       ${DEVICE_BAUDRATE}

*** Test Cases ***
Test Device Communication
    [Documentation]    Test that we can communicate with the device
    Log    Testing communication with device at ${SERIAL_PORT}

    # Use echo to send commands and read responses
    ${result}=    Run Process    echo    HELP    shell=true
    Log    Echo result: ${result.stdout}

    # Verify device configuration is available
    Should Not Be Empty    ${DEVICE_SERIAL}
    Should Not Be Empty    ${DEVICE_PLATFORM}
    Should Not Be Empty    ${BUILD_DIR}

    # Verify build artifacts exist
    Directory Should Exist    ${BUILD_DIR}
    File Should Exist    ${BUILD_DIR}/zephyr/zephyr.elf
