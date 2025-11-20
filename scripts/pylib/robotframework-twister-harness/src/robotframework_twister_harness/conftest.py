# robotframework-twister-harness/conftest.py
import pytest
import logging
from handlers.RobotHandler import RobotHandler

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add Robot Framework specific options"""
    parser.addoption('--robot-file', help='Robot Framework test file')
    parser.addoption('--robot-resource-dir', help='Robot Framework resource directory')
    parser.addoption('--proxy-host', default='localhost', help='Device proxy host')
    parser.addoption('--proxy-port', default=8888, type=int, help='Device proxy port')


# robotframework-twister-harness/setup.py
from setuptools import setup, find_packages

setup(
    name="robotframework-twister-harness",
    version="1.0.0",
    description="Robot Framework integration for Zephyr Twister with shared device access",
    packages=find_packages(),
    install_requires=[
        "robotframework>=6.0",
        "twister-harness>=1.0",
    ],
    python_requires=">=3.8",
)
