*** Settings ***
Documentation    Hello World Hardware Test Suite
Metadata         Version          1.0
Metadata         Hardware         Any MCU with the CONFIG_SHELL=y
Metadata         Test Type        Hardware Serial
Metadata         Description      Tests Hello World output on hardware with reboot

*** Variables ***
${SUITE_DESCRIPTION}    Hello World hardware serial tests for Any Board
