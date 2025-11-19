# [file name]: scripts/pylib/robotframework-twister-harness/src/pytest_robotframework_twister/collector.py
"""Robot Framework test file collector for pytest-twister-harness."""
import pytest
from pathlib import Path
import tempfile
import subprocess
import os
import logging

logger = logging.getLogger(__name__)


class RobotFrameworkTestFailure(Exception):
    """Exception raised when Robot Framework tests fail."""
    
    def __init__(self, test_name, result):
        self.test_name = test_name
        self.result = result
        super().__init__(f"Robot Framework test {test_name} failed")


def pytest_collect_file(file_path, parent):
    """Convert .robot files to pytest test items."""
    # Only collect .robot files when the option is enabled
    if (file_path.suffix.lower() == '.robot' and 
        parent.config.getoption("--twister-with-robot")):
        logger.info(f"✅ Collecting Robot Framework file: {file_path}")
        return RobotFrameworkTestFile.from_parent(parent, path=file_path)
    return None


class RobotFrameworkTestFile(pytest.File):
    """Represents a Robot Framework test file as a pytest test item."""

    def collect(self):
        """Collect test items from Robot Framework file."""
        logger.info(f"📁 Collecting tests from: {self.path}")
        
        # Yield one test item per Robot test suite
        yield RobotFrameworkTestItem.from_parent(
            self, 
            name=f"robot_{self.path.stem}"
        )


class RobotFrameworkTestItem(pytest.Item):
    """Test item that runs a Robot Framework test file."""

    def __init__(self, name, parent, **kwargs):
        super().__init__(name, parent, **kwargs)
        self.add_marker("robotframework")
        self.robot_file = parent.path
        logger.debug(f"Created RobotFrameworkTestItem: {name}")

    def runtest(self):
        """Execute the Robot Framework test file."""
        logger.info(f"🚀 Running Robot Framework test: {self.robot_file}")
        
        if not self.robot_file.exists():
            raise RobotFrameworkTestFailure(self.name, {
                "stdout": "",
                "stderr": f"Robot Framework file not found: {self.robot_file}",
                "returncode": 1
            })

        # Get device configuration from Twister command line
        device_config = self._get_device_config()
        logger.debug(f"Device config: {device_config}")
        
        self._run_robot_test(device_config)

    def _get_device_config(self):
        """Extract device configuration from command line arguments."""
        config = self.config
        return {
            "DEVICE_SERIAL": config.getoption("--device-serial", ""),
            "DEVICE_BAUDRATE": config.getoption("--device-serial-baud", "115200"),
            "DEVICE_RUNNER": config.getoption("--runner", ""),
            "DEVICE_PLATFORM": config.getoption("--platform", ""),
            "BUILD_DIR": config.getoption("--build-dir", ""),
        }

    def _run_robot_test(self, device_config):
        """Run Robot Framework test with given configuration."""
        # Create temporary variable file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as var_file:
            var_file.write("def get_variables():\n")
            var_file.write("    return {\n")
            for key, value in device_config.items():
                var_file.write(f'        "{key}": "{value}",\n')
            var_file.write("    }\n")
            var_file_path = var_file.name

        try:
            build_dir = Path(self.config.getoption("--build-dir"))
            output_dir = build_dir / "robot_results"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                "robot",
                "--variablefile", var_file_path,
                "--outputdir", str(output_dir),
                "--log", "log.html", 
                "--report", "report.html",
                "--xunit", "xunit.xml",
                str(self.robot_file)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode != 0:
                raise RobotFrameworkTestFailure(self.name, {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                })
                
            logger.info("✅ Robot Framework test PASSED")
            
        except subprocess.TimeoutExpired:
            raise RobotFrameworkTestFailure(self.name, {
                "stdout": "",
                "stderr": "Robot Framework command timed out",
                "returncode": 1
            })
        finally:
            if os.path.exists(var_file_path):
                os.unlink(var_file_path)

    def repr_failure(self, excinfo):
        """Provide better failure reporting."""
        if isinstance(excinfo.value, RobotFrameworkTestFailure):
            failure = excinfo.value.result
            return f"Robot Framework test failed (returncode={failure['returncode']}):\nSTDOUT:\n{failure['stdout']}\nSTDERR:\n{failure['stderr']}"
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.robot_file, 0, f"Robot Framework: {self.name}"
