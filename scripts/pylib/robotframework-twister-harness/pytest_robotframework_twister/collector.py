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


class RobotFrameworkTestFile(pytest.File):
    """Collector for Robot Framework test files."""

    def collect(self):
        """Collect test items from Robot Framework files."""
        logger.info(f"RobotFrameworkTestFile.collect called for: {self.path}")
        # Yield a single test item that will run the entire Robot Framework suite
        item = RobotFrameworkTestItem.from_parent(self, name=self.path.name)
        logger.info(f"Created test item: {item}")
        yield item


class RobotFrameworkTestItem(pytest.Item):
    """Test item for running Robot Framework tests."""

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.add_marker("twister_robot")
        logger.info(f"RobotFrameworkTestItem created: {name}")

    def setup(self):
        """Setup the test item."""
        logger.info(f"RobotFrameworkTestItem.setup called for: {self.name}")
        super().setup()

    def runtest(self):
        """Execute the Robot Framework test."""
        logger.info(f"Running Robot Framework test: {self.name}")
        
        try:
            # Get the build directory from the config
            build_dir = Path(self.config.getoption("--build-dir"))
            
            # For now, use mock device configuration since fixture access is complex
            # In a real implementation, we would get this from device_object fixture
            device_config = {
                "DEVICE_SERIAL": "/dev/ttyACM0",  # Mock data for now
                "DEVICE_BAUDRATE": "115200",
                "DEVICE_RUNNER": "openocd", 
                "DEVICE_PLATFORM": "nucleo_g474re",
                "BUILD_DIR": str(build_dir),
            }
            
            logger.info(f"Device config: {device_config}")
            
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
                output_dir = build_dir / "robot_results"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Build Robot Framework command
                cmd = [
                    "robot",
                    "--variablefile", var_file_path,
                    "--outputdir", str(output_dir),
                    "--log", "log.html", 
                    "--report", "report.html",
                    "--xunit", "xunit.xml",
                    str(self.parent.path)
                ]
                
                logger.info(f"Running Robot Framework command: {' '.join(cmd)}")
                
                # Run Robot Framework
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                
                logger.info(f"Robot Framework result: returncode={result.returncode}")
                
                # Check if test passed
                if result.returncode != 0:
                    raise RobotFrameworkTestFailure(self.name, result)
                
            finally:
                # Clean up
                if os.path.exists(var_file_path):
                    os.unlink(var_file_path)
                    
        except Exception as e:
            logger.error(f"Error running Robot Framework test: {e}")
            raise

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        logger.info(f"RobotFrameworkTestItem.repr_failure called: {excinfo}")
        if isinstance(excinfo.value, RobotFrameworkTestFailure):
            return f"Robot Framework test failed:\n{excinfo.value.result['stdout']}\n{excinfo.value.result['stderr']}"
        return super().repr_failure(excinfo)

    def reportinfo(self):
        logger.info(f"RobotFrameworkTestItem.reportinfo called")
        return self.parent.path, 0, f"Robot Framework test: {self.name}"
