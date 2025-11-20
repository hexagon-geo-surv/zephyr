# robotframework-twister-harness/robot_tests/shell_commands.robot
*** Settings ***
Resource    ../resources/device_communication.robot
Suite Setup    Initialize Device For Testing
Suite Teardown    Cleanup Test Environment

*** Variables ***
${SHELL_PROMPT}    uart

*** Test Cases ***
Verify Shell Boot Message
    [Documentation]    Verify device boots properly and shows shell prompt
    Wait For Prompt    ${SHELL_PROMPT}
    ${response}=    Execute Command And Get Response    echo "Hello Robot"
    Should Contain    ${response}    Hello Robot

Test Shell Version Command
    [Documentation]    Test shell version command
    Execute Command And Verify Response    shell version    Shell

Test Kernel Commands
    [Documentation]    Test various kernel commands
    Execute Command And Verify Response    kernel version    Zephyr
    Execute Command And Verify Response    kernel uptime    uptime
    Execute Command And Verify Response    kernel stacks    stacks

Test Help Command Output
    [Documentation]    Verify help command shows available commands
    ${help_output}=    Execute Command And Verify Response    help    Available commands
    Should Contain    ${help_output}    kernel
    Should Contain    ${help_output}    shell
    Should Contain    ${help_output}    version

Test Multiple Sequential Commands
    [Documentation]    Test sending multiple commands sequentially
    FOR    ${index}    IN RANGE    3
        ${response}=    Execute Command And Get Response    kernel uptime
        Should Contain    ${response}    uptime
    END

*** Keywords ***
Custom Test Setup
    [Documentation]    Custom setup for specific test needs
    Log    Starting custom test setup
    Wait For Device Boot

Custom Test Teardown
    [Documentation]    Custom teardown for specific test needs  
    Log    Performing custom test teardown
