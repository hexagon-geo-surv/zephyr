# robotframework-twister-harness/setup.py
#!/usr/bin/env python3

import os
from setuptools import setup, find_packages

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Function to include .robot files in package data
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.robot'):
                paths.append(os.path.join('..', path, filename))
    return paths

setup(
    name="robotframework-twister-harness",
    version="1.0.0",
    description="Robot Framework integration for Zephyr Twister with shared device access",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Zephyr Project",
    author_email="devel@lists.zephyrproject.org",
    url="https://github.com/zephyrproject-rtos/robotframework-twister-harness",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "robotframework_twister_harness": package_files("resources") + package_files("robot_tests")
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov',
            'twine',
            'wheel',
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-timeout',
        ],
    },
    entry_points={
        'pytest11': [
            'robotframework_twister_harness = robotframework_twister_harness.conftest',
        ],
        'twister.harness': [
            'robot = robotframework_twister_harness.handlers.RobotHandler:RobotHandler',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Embedded Systems",
        "Framework :: Robot Framework",
        "Framework :: Pytest",
    ],
    keywords="zephyr,twister,robot-framework,testing,embedded",
    project_urls={
        "Documentation": "https://docs.zephyrproject.org/latest/develop/test/twister.html",
        "Source": "https://github.com/zephyrproject-rtos/robotframework-twister-harness",
        "Tracker": "https://github.com/zephyrproject-rtos/robotframework-twister-harness/issues",
    },
)
