# robotframework-twister-harness/resources/device_communication.robot
*** Settings ***
Library    ../libraries/ProxyTwisterLibrary.py

*** Variables ***
${DEFAULT_TIMEOUT}    30s
${PROXY_HOST}         localhost
${PROXY_PORT}         8888

*** Keywords ***
Initialize Device For Testing
    [Documentation]    Initialize connection to device proxy
    [Arguments]    ${proxy_host}=${PROXY_HOST}    ${proxy_port}=${PROXY_PORT}
    Open Device Connection    proxy_host=${proxy_host}    proxy_port=${proxy_port}
    Wait For Device Boot

Wait For Device Boot
    [Documentation]    Wait for device to boot completely
    Wait For Prompt    Booting Zephyr    timeout=60s
    Wait For Prompt    uart    timeout=30s

Execute Command And Verify Response
    [Documentation]    Execute command and verify response contains expected text
    [Arguments]    ${command}    ${expected_response}    ${timeout}=${DEFAULT_TIMEOUT}
    ${response}=    Write To Device    ${command}    timeout=${timeout}
    Should Contain    ${response}    ${expected_response}
    [Return]    ${response}

Execute Command And Get Response
    [Documentation]    Execute command and return full response
    [Arguments]    ${command}    ${timeout}=${DEFAULT_TIMEOUT}
    ${response}=    Write To Device    ${command}    timeout=${timeout}
    [Return]    ${response}

Wait For Prompt
    [Documentation]    Wait for specific prompt to appear
    [Arguments]    ${prompt}    ${timeout}=${DEFAULT_TIMEOUT}
    ${success}=    Wait For Prompt    ${prompt}    timeout=${timeout}
    Should Be True    ${success}    Timeout waiting for prompt: ${prompt}

Cleanup Test Environment
    [Documentation]    Cleanup test environment
    Close Device Connection
