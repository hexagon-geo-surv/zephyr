*** Settings ***
Documentation    Hardware testing keywords for Zephyr
Library         Process
Library         String

*** Variables ***
${SERIAL_PORT}          /dev/ttyACM0
${HELLO_WORLD_MESSAGE}  Hello World to Robot-Framework!

*** Keywords ***
Reset Hardware Board
    [Documentation]    Reset the hardware board using kernel reboot command
    Log    Resetting hardware board...

    # Clear any existing data in buffer
    Run Process    timeout 0.5 cat ${SERIAL_PORT} > /dev/null 2>&1    shell=True

    # Send kernel reboot command
    Run Process    printf "kernel reboot\\r\\n" > ${SERIAL_PORT}    shell=True

    # Wait for reboot to complete
    Sleep    1s
    Log    ✓ Board reset complete

Wait For Hello World Message
    [Documentation]    Wait for Hello World message to appear after reboot
    Log    Waiting for Hello World message: '${HELLO_WORLD_MESSAGE}'

    ${found}=    Set Variable    ${FALSE}
    ${all_output}=    Set Variable    ${EMPTY}

    # Wait up to 8 seconds for the message
    FOR    ${i}    IN RANGE    100
        # Read serial output
        ${output}=    Run Process    timeout 1 cat ${SERIAL_PORT}    shell=True
        ${all_output}=    Set Variable    ${all_output}${output.stdout}

        # Check if Hello World message is in the output
        IF    "${HELLO_WORLD_MESSAGE}" in """${all_output}"""
            ${found}=    Set Variable    ${TRUE}
            Log    ✓ Hello World message found after ${i + 1} seconds
            BREAK
        END

        Sleep    0.1s
    END

    IF    not ${found}
        Fail    Hello World message '${HELLO_WORLD_MESSAGE}' not found within 10 seconds. Output received: ${all_output}
    END

    RETURN    ${all_output}

Verify Hello World On Boot
    [Documentation]    Reset device and verify Hello World message appears on boot
    Log    Starting Hello World verification...

    # Reset the board
    Reset Hardware Board

    # Wait for Hello World message
    ${boot_output}=    Wait For Hello World Message

    Log    ✓ Hello World verification passed
    RETURN    ${boot_output}

Execute Command
    [Documentation]    Execute a command on the board and return response
    [Arguments]    ${command}

    # Clear buffer
    Run Process    timeout 0.3 cat ${SERIAL_PORT} > /dev/null 2>&1    shell=True

    # Send command
    Run Process    printf "${command}\\r\\n" > ${SERIAL_PORT}    shell=True
    Sleep    0.5s

    # Read response
    ${response}=    Run Process    timeout 3 cat ${SERIAL_PORT}    shell=True
    RETURN    ${response.stdout}

Verify Board Responsive
    [Documentation]    Verify the board is responsive to commands
    Log    Verifying board responsiveness...

    ${response}=    Execute Command    help
    Should Contain    ${response}    Available commands
    Log    ✓ Board is responsive

Hardware Test Setup
    [Documentation]    Setup for hardware tests
    Log    Hardware test setup started...
    # Ensure clean state by clearing buffer
    Run Process    timeout 0.5 cat ${SERIAL_PORT} > /dev/null 2>&1    shell=True
    Log    Hardware test setup complete

Hardware Test Teardown
    [Documentation]    Teardown for hardware tests
    Log    Hardware test teardown started...
    Log    Hardware test teardown complete
