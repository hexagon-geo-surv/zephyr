"""Robot Framework test file collector for pytest-twister-harness."""
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


class RobotFrameworkTestFailure(Exception):
    """Exception raised when Robot Framework tests fail."""

    def __init__(self, test_name, result):
        self.test_name = test_name
        self.result = result
        super().__init__(f"Robot Framework test {test_name} failed")


def pytest_collect_file(file_path, parent):
    """Convert .robot files to pytest test items."""
    if file_path.suffix.lower() == '.robot' and parent.config.getoption("--twister-with-robot"):
        logger.info(f"✅ Collecting Robot Framework file: {file_path}")
        return RobotFrameworkTestFile.from_parent(parent, path=file_path)
    return None


class RobotFrameworkTestFile(pytest.File):
    """Represents a Robot Framework test file as a pytest test item."""

    def collect(self):
        """Collect a single test item for the Robot Framework file."""
        logger.info(f"📁 Collecting test from Robot Framework file: {self.path}")

        # Create a test item that will run the entire Robot Framework suite
        item = RobotFrameworkTestItem.from_parent(self, name=f"robot_{self.path.stem}")
        logger.info(f"✅ Created test item: {item}")
        yield item


class RobotFrameworkTestItem(pytest.Item):
    """Test item that runs a Robot Framework test file."""

    def __init__(self, name, parent, **kwargs):
        super().__init__(name, parent, **kwargs)
        self.add_marker("robotframework")
        self.robot_file = parent.path
        logger.info(f"🧪 Created RobotFrameworkTestItem: {name}")

    def runtest(self):
        """Execute the Robot Framework test file."""
        logger.info(f"🚀 Running Robot Framework test: {self.robot_file}")

        # Get device configuration from command line (device is already flashed by Twister)
        device_config = self._get_device_config()

        # Run Robot Framework with device configuration
        self._run_robot_framework_test(device_config)

    def _get_device_config(self):
        """Get device configuration from command line arguments."""
        # Device is already flashed and ready by Twister at this point
        # We just need to pass the configuration to Robot Framework
        config = {
            "DEVICE_SERIAL": self.config.getoption("--device-serial", ""),
            "DEVICE_BAUDRATE": self.config.getoption("--device-serial-baud", "115200"),
            "DEVICE_RUNNER": self.config.getoption("--runner", ""),
            "DEVICE_PLATFORM": self.config.getoption("--platform", ""),
            "BUILD_DIR": self.config.getoption("--build-dir", ""),
        }
        logger.info(f"⚙️ Device config: {config}")
        return config

    def _run_robot_framework_test(self, device_config):
        """Execute Robot Framework test with device configuration."""
        # Check if the Robot Framework file exists
        robot_file = Path(self.robot_file)
        logger.info(f"🤖 Robot Framework file: {robot_file}, exists: {robot_file.exists()}")

        if not robot_file.exists():
            raise RobotFrameworkTestFailure(self.name, {
                "stdout": "",
                "stderr": f"Robot Framework file not found: {robot_file}",
                "returncode": 1
            })

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
            build_dir = Path(self.config.getoption("--build-dir"))
            output_dir = build_dir / "robot_results"
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Output directory: {output_dir}")

            # Build Robot Framework command
            cmd = [
                "robot",
                "--variablefile", var_file_path,
                "--outputdir", str(output_dir),
                "--log", "log.html", 
                "--report", "report.html",
                "--xunit", "xunit.xml",
                str(robot_file)
            ]

            logger.info(f"▶️ Running Robot Framework command: {' '.join(cmd)}")

            # Run Robot Framework with timeout
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd(),
                timeout=120  # 2 minute timeout
            )

            logger.info(f"✅ Robot Framework completed: returncode={result.returncode}")

            # Check if test passed
            if result.returncode != 0:
                raise RobotFrameworkTestFailure(self.name, {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                })

            logger.info("🎉 Robot Framework test PASSED")

        except subprocess.TimeoutExpired:
            raise RobotFrameworkTestFailure(self.name, {  # noqa: B904
                "stdout": "",
                "stderr": "Robot Framework command timed out after 120 seconds",
                "returncode": 1
            })
        finally:
            # Clean up temporary variable file
            if os.path.exists(var_file_path):
                os.unlink(var_file_path)

    def repr_failure(self, excinfo):
        """Provide better failure reporting."""
        if isinstance(excinfo.value, RobotFrameworkTestFailure):
            return f"Robot Framework test failed:\n{excinfo.value.result['stdout']}\n{excinfo.value.result['stderr']}"  # noqa: E501
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.robot_file, 0, f"Robot Framework test: {self.name}"
