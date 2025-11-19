"""Fixtures for Robot Framework Twister integration."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="function")
def robot_framework_runner(dut, pytestconfig, request):
    """Fixture to run Robot Framework tests with Twister device integration."""

    class RobotFrameworkRunner:
        def __init__(self, device, config):
            self.device = device
            self.config = config
            self.build_dir = Path(config.getoption("--build-dir"))

        def run_test(self, test_file: str, variables: dict[str, Any] = None) -> dict[str, Any]:
            """Run a Robot Framework test file with device context."""
            if variables is None:
                variables = {}

            # Add device configuration to variables
            device_vars = {
                "DEVICE_SERIAL": getattr(self.device.device_config, 'serial', ''),
                "DEVICE_BAUDRATE": getattr(self.device.device_config, 'baudrate', '115200'),
                "DEVICE_RUNNER": getattr(self.device.device_config, 'runner', ''),
                "DEVICE_PLATFORM": getattr(self.device.device_config, 'platform', ''),
                "BUILD_DIR": str(self.build_dir),
            }
            device_vars.update(variables)

            # Create temporary variable file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as var_file:
                var_file.write("def get_variables():\n")
                var_file.write("    return {\n")
                for key, value in device_vars.items():
                    var_file.write(f'        "{key}": "{value}",\n')
                var_file.write("    }\n")
                var_file_path = var_file.name

            try:
                # Set up output directory
                output_dir = self.build_dir / "robot_results"
                output_dir.mkdir(parents=True, exist_ok=True)

                # Build Robot Framework command
                cmd = [
                    "robot",
                    "--variablefile", var_file_path,
                    "--outputdir", str(output_dir),
                    "--log", "log.html",
                    "--report", "report.html", 
                    "--xunit", "xunit.xml",
                    test_file
                ]

                # Run the test
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=os.getcwd(),
                    timeout=300  # 5 minute timeout
                )

                return {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "output_dir": output_dir,
                    "success": result.returncode == 0
                }

            finally:
                # Clean up temporary variable file
                if os.path.exists(var_file_path):
                    os.unlink(var_file_path)

    return RobotFrameworkRunner(dut, pytestconfig)


@pytest.fixture(scope="session")
def robot_framework_variables(dut, pytestconfig) -> dict[str, Any]:
    """Provide common variables for Robot Framework tests."""
    build_dir = Path(pytestconfig.getoption("--build-dir"))

    return {
        "DEVICE_SERIAL": getattr(dut.device_config, 'serial', ''),
        "DEVICE_BAUDRATE": getattr(dut.device_config, 'baudrate', '115200'),
        "DEVICE_RUNNER": getattr(dut.device_config, 'runner', ''),
        "DEVICE_PLATFORM": getattr(dut.device_config, 'platform', ''),
        "BUILD_DIR": str(build_dir),
        "ZEPHYR_BASE": os.environ.get("ZEPHYR_BASE", ""),
    }
