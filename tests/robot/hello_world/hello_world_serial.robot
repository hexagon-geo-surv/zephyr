*** Settings ***
Documentation    Hello World hardware test with serial communication
Resource         ../hardware_keywords.robot
Suite Setup      Hardware Test Setup
Suite Teardown   Hardware Test Teardown

*** Test Cases ***
Verify Hello World Output On Boot
    [Documentation]    Reset device and verify Hello World message appears on boot
    [Tags]    hello-world    boot    hardware

    Log    \n🎯 TEST 1: Verify Hello World Output On Boot
    Log    ============================================

    # This will reset the board and verify Hello World message
    ${boot_output}=    Verify Hello World On Boot

    Log    Full boot output received:
    Log    ${boot_output}

    Log    ✅ SUCCESS: Hello World message verified after reboot!

Verify Board Responsive After Hello World
    [Documentation]    Verify board is responsive after Hello World boot
    [Tags]    responsiveness    hardware

    Log    \n🔌 TEST 2: Verify Board Responsive After Hello World
    Log    ===================================================

    Verify Board Responsive
    Log    ✅ SUCCESS: Board is fully responsive after Hello World boot!

Complete Hello World Integration Test
    [Documentation]    Complete integration test with reset and verification
    [Tags]    integration    hello-world

    Log    \n🚀 TEST 3: Complete Hello World Integration Test
    Log    ================================================

    # Step 1: Reset and verify Hello World
    Log    Step 1: Resetting board and verifying Hello World message...
    ${boot_output}=    Verify Hello World On Boot

    # Step 2: Verify board responsiveness
    Log    Step 2: Verifying board responsiveness...
    Verify Board Responsive

    # Step 3: Test additional commands to ensure full functionality
    Log    Step 3: Testing additional commands...
    ${version_output}=    Execute Command    kernel version
    # Just verify we got some response (not empty)
    Should Not Be Equal    ${version_output}    ${EMPTY}
    Log    ✓ Kernel version command working - Output: ${version_output}

    ${devices_output}=    Execute Command    device list
    Should Contain    ${devices_output}    READY
    Log    ✓ Device list command working

    Log    ✅ SUCCESS: Complete Hello World integration test passed!
