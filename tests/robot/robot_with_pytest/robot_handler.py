# tests/robot/robot_with_pytest/robot_handler.py
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class RobotFrameworkHandler:
    """Handler for Robot Framework tests in Twister"""
    
    def __init__(self, test_instance):
        self.test = test_instance
        self.build_dir = Path(test_instance.build_dir)
        self.robot_files = []
        
    def configure(self):
        """Configure the handler"""
        # Find all .robot files in robot_tests directory
        robot_tests_dir = Path(self.test.source_dir) / "robot_tests"
        if robot_tests_dir.exists():
            for robot_file in robot_tests_dir.glob("*.robot"):
                self.robot_files.append(robot_file)
                logger.info(f"Found Robot test: {robot_file}")
        
        if not self.robot_files:
            logger.warning("No Robot Framework test files found")
            
    def run(self):
        """Run Robot Framework tests"""
        if not self.robot_files:
            logger.error("No Robot test files to run")
            return False
            
        # Set up environment variables for Robot Framework
        env = os.environ.copy()
        env['DEVICE_SERIAL'] = self.test.serial or ''
        env['DEVICE_BAUDRATE'] = str(getattr(self.test, 'baudrate', 115200))
        env['DEVICE_PLATFORM'] = self.test.platform.name
        env['BUILD_DIR'] = str(self.build_dir)
        
        # Create results directory
        results_dir = self.build_dir / "robot_results"
        results_dir.mkdir(exist_ok=True)
        
        success = True
        for robot_file in self.robot_files:
            if not self._run_single_test(robot_file, results_dir, env):
                success = False
                
        return success
    
    def _run_single_test(self, robot_file, results_dir, env):
        """Run a single Robot Framework test file"""
        try:
            cmd = [
                'robot',
                '--outputdir', str(results_dir),
                '--log', f'{robot_file.stem}_log.html',
                '--report', f'{robot_file.stem}_report.html',
                '--xunit', f'{robot_file.stem}_xunit.xml',
                '--variable', f'DEVICE_SERIAL:{env["DEVICE_SERIAL"]}',
                '--variable', f'DEVICE_BAUDRATE:{env["DEVICE_BAUDRATE"]}',
                '--variable', f'DEVICE_PLATFORM:{env["DEVICE_PLATFORM"]}',
                '--variable', f'BUILD_DIR:{env["BUILD_DIR"]}',
                str(robot_file)
            ]
            
            logger.info(f"Running Robot Framework test: {robot_file.name}")
            result = subprocess.run(
                cmd,
                cwd=self.build_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=getattr(self.test, 'timeout', 60)
            )
            
            if result.returncode == 0:
                logger.info(f"Robot test {robot_file.name} passed")
                return True
            else:
                logger.error(f"Robot test {robot_file.name} failed")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Robot test {robot_file.name} timed out")
            return False
        except Exception as e:
            logger.error(f"Error running Robot test {robot_file.name}: {e}")
            return False
