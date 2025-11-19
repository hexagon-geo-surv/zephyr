from setuptools import setup, find_packages

setup(
    name="pytest-robotframework-twister-harness",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "pytest11": [
            "robotframework-twister = pytest_robotframework_twister.plugin",
        ]
    },
    install_requires=[
        "robotframework>=5.0.0",
    ],
    python_requires=">=3.8",
)
