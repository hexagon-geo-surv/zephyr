*** Settings ***
Documentation    Simple Robot Framework test for Twister integration
Library          Collections
Library          String
Library          OperatingSystem

*** Variables ***

*** Test Cases ***
Verify Device Configuration
    [Documentation]    Verify that Twister provides device configuration
    Log    Testing device: ${DEVICE_PLATFORM}
    Log    Serial port: ${DEVICE_SERIAL}
    Log    Build directory: ${BUILD_DIR}
    
    Should Not Be Empty    ${DEVICE_PLATFORM}
    Should Not Be Empty    ${BUILD_DIR}

Verify Build Artifacts Exist
    [Documentation]    Verify that build artifacts were created
    Directory Should Exist    ${BUILD_DIR}
    File Should Exist    ${BUILD_DIR}/zephyr/zephyr.elf
