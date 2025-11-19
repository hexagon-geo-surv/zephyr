"""Configuration for Robot Framework Twister tests."""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "robotframework: mark test as Robot Framework test to run with Twister harness"
    )
