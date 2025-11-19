*** Settings ***
Documentation    Simple Robot Framework test for Twister integration
Library          Collections
Library          String
Library          OperatingSystem

*** Variables ***

*** Test Cases ***
Verify Device Configuration From Twister
    [Documentation]    Verify that Twister provides device configuration
    Log    Testing device: ${DEVICE_PLATFORM}
    Log    Serial port: ${DEVICE_SERIAL}
    Log    Baud rate: ${DEVICE_BAUDRATE}
    Log    Build directory: ${BUILD_DIR}
    
    Should Not Be Empty    ${DEVICE_PLATFORM}
    Should Not Be Empty    ${DEVICE_SERIAL}
    Should Not Be Empty    ${BUILD_DIR}
    Should Be Equal    ${DEVICE_BAUDRATE}    115200

Verify Build Artifacts Exist
    [Documentation]    Verify that build artifacts were created by Twister
    Directory Should Exist    ${BUILD_DIR}
    File Should Exist    ${BUILD_DIR}/zephyr/zephyr.elf
    File Should Exist    ${BUILD_DIR}/zephyr/zephyr.bin

Test Summary
    [Documentation]    Final test summary
    Log    Robot Framework test executed successfully with Twister harness!
