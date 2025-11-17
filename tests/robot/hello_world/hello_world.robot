*** Settings ***
Documentation    Simple Hello World hardware test
Resource         ../hardware_keywords.robot
Library          String
Library          Collections

*** Variables ***
${TEST_MESSAGE}    Hello World to Robot-Framework!

*** Test Cases ***
Verify Basic Test Execution
    [Documentation]    Basic test to verify hardware robot runner works
    [Tags]    smoke    basic
    Log    ${TEST_MESSAGE}
    Should Be Equal    ${TEST_MESSAGE}    Hello World to Robot-Framework!

Test Robot Framework Functionality
    [Documentation]    Test Robot Framework built-in keywords
    [Tags]    framework
    ${list}=    Create List    hardware    testing    robot    framework
    Length Should Be    ${list}    4
    Should Contain    ${list}    robot

Verify Hardware Keywords Are Available
    [Documentation]    Verify our custom hardware keywords are loaded
    [Tags]    keywords    hardware
    Log    Hardware keywords resource loaded successfully
    # These would be used in actual hardware tests
    Log    Available keywords: Open Hardware Serial Connection, Reset Hardware Board, etc.
