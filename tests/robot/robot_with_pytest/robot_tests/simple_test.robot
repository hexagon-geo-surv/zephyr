*** Settings ***
Documentation    Test serial communication with device
Library          Serial
Library          Collections
Library          String

*** Variables ***
${PORT}        ${DEVICE_SERIAL}
${BAUDRATE}    ${DEVICE_BAUDRATE}

*** Test Cases ***
Test Serial Communication
    [Documentation]    Test basic serial communication
    Serial.Open Port    ${PORT}    baudrate=${BAUDRATE}

    # Send command
    Serial.Write String    HELP\n

    # Read response
    ${response}=    Serial.Read String    expected=Available commands:    timeout=10
    Should Contain    ${response}    Available commands:
    Should Contain    ${response}    HELP

    Serial.Close Port
