from setuptools import find_packages, setup

setup(
    name="pytest-robotframework-twister-harness",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "pytest11": [
            "robotframework-twister = pytest_robotframework_twister.plugin",
        ]
    },
    install_requires=[
        "robotframework>=5.0.0",
        "robotframework-seriallibrary>=0.4.0",
    ],
    python_requires=">=3.8",
)
