"""Fixtures for Robot Framework Twister harness."""
import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator, Dict, Any
import subprocess
import json


@pytest.fixture(scope="session")
def robot_framework_env(device_object, pytestconfig) -> Dict[str, Any]:
    """Create environment for Robot Framework tests."""
    build_dir = Path(pytestconfig.getoption("--build-dir"))
    
    return {
        "DEVICE_SERIAL": getattr(device_object.device_config, 'serial', ''),
        "DEVICE_BAUDRATE": getattr(device_object.device_config, 'baudrate', '115200'),
        "DEVICE_RUNNER": getattr(device_object.device_config, 'runner', ''),
        "DEVICE_PLATFORM": getattr(device_object.device_config, 'platform', ''),
        "BUILD_DIR": str(build_dir),
    }


@pytest.fixture(scope="function")
def robot_framework_runner(device_object, pytestconfig):
    """Fixture to run Robot Framework tests with Twister integration."""
    
    class RobotFrameworkRunner:
        def __init__(self, device, config):
            self.device = device
            self.config = config
            self.build_dir = Path(config.getoption("--build-dir"))
            
        def run_test(self, test_file: str) -> Dict[str, Any]:
            """Run a Robot Framework test file."""
            # Get device configuration
            device_config = {
                "DEVICE_SERIAL": getattr(self.device.device_config, 'serial', ''),
                "DEVICE_BAUDRATE": getattr(self.device.device_config, 'baudrate', '115200'),
                "DEVICE_RUNNER": getattr(self.device.device_config, 'runner', ''),
                "DEVICE_PLATFORM": getattr(self.device.device_config, 'platform', ''),
                "BUILD_DIR": str(self.build_dir),
            }
            
            # Create a temporary variable file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as var_file:
                var_file.write("def get_variables():\n")
                var_file.write("    return {\n")
                for key, value in device_config.items():
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
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                
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

    return RobotFrameworkRunner(device_object, pytestconfig)
