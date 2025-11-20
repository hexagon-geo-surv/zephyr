# robotframework-twister-harness/handlers/RobotHandler.py
import os
import subprocess
import logging
import time
from pathlib import Path
from twisterlib.test import Test
from twisterlib.handlers import Handler

# Import our proxy components
import sys
sys.path.append(str(Path(__file__).parent.parent))
from libraries.DeviceProxy import device_proxy
from libraries.SocketBridge import socket_bridge

logger = logging.getLogger(__name__)


class RobotHandler(Handler):
    """Handler for Robot Framework tests in Twister with shared device access"""
    
    def __init__(self, test: Test, **kwargs):
        super().__init__(test, **kwargs)
        self.robot_file = test.robot_file
        self.resource_dir = test.resource_dir
        self.proxy_started = False
    
    def run(self) -> bool:
        """Execute Robot Framework test with shared device access"""
        build_dir = Path(self.test.build_dir)
        
        # Start device proxy and socket bridge if not already running
        if not self.proxy_started:
            if not self._start_proxy_infrastructure(build_dir):
                return False
            self.proxy_started = True
        
        # Set up environment for Robot Framework
        env = os.environ.copy()
        env['TWISTER_BUILD_DIR'] = str(build_dir)
        env['TWISTER_DEVICE_TYPE'] = self.test.platform.name
        env['TWISTER_SERIAL_PORT'] = self.test.serial or ''
        env['DEVICE_PROXY_HOST'] = 'localhost'
        env['DEVICE_PROXY_PORT'] = '8888'
        env['ROBOT_CLIENT_ID'] = f"twister_{self.test.name}_{int(time.time())}"
        
        # Construct Robot Framework command
        output_dir = build_dir / 'robot_results'
        output_dir.mkdir(exist_ok=True)
        
        cmd = [
            'robot',
            '--outputdir', str(output_dir),
            '--log', 'log.html',
            '--report', 'report.html', 
            '--xunit', 'xunit.xml',
            '--variable', f'PROXY_HOST:localhost',
            '--variable', f'PROXY_PORT:8888',
            '--variable', f'BUILD_DIR:{build_dir}',
            '--variable', f'DEVICE_TYPE:{self.test.platform.name}',
        ]
        
        # Add resource files if specified
        if self.resource_dir:
            for resource in Path(self.resource_dir).glob('*.resource'):
                cmd.extend(['--resource', str(resource)])
        
        # Add the main robot test file
        cmd.append(str(self.robot_file))
        
        logger.info('Running Robot Framework test with shared device access')
        logger.debug('Command: %s', ' '.join(cmd))
        
        try:
            result = subprocess.run(
                cmd,
                cwd=build_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.test.timeout
            )
            
            # Log output for debugging
            if result.stdout:
                logger.debug("Robot Framework stdout:\n%s", result.stdout)
            if result.stderr:
                logger.debug("Robot Framework stderr:\n%s", result.stderr)
            
            return self._parse_results(result)
            
        except subprocess.TimeoutExpired:
            logger.error('Robot Framework test timed out after %s seconds', self.test.timeout)
            return False
        except Exception as e:
            logger.error('Failed to run Robot Framework test: %s', e)
            return False
    
    def _start_proxy_infrastructure(self, build_dir: Path) -> bool:
        """Start device proxy and socket bridge"""
        try:
            # Connect device to proxy
            success = device_proxy.connect_device(
                build_dir=str(build_dir),
                device_type=self.test.platform.name,
                serial_port=self.test.serial or '',
                platform=self.test.platform.name
            )
            
            if not success:
                logger.error("Failed to connect device to proxy")
                return False
            
            # Start socket bridge
            if not socket_bridge.start():
                logger.error("Failed to start socket bridge")
                device_proxy.disconnect()
                return False
            
            # Wait a moment for infrastructure to stabilize
            time.sleep(2)
            
            logger.info("Device proxy and socket bridge started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to start proxy infrastructure: %s", e)
            return False
    
    def _parse_results(self, result: subprocess.CompletedProcess) -> bool:
        """Parse Robot Framework execution results"""
        if result.returncode == 0:
            self.test.status = "passed"
            logger.info("Robot Framework test passed")
            return True
        else:
            self.test.status = "failed"
            logger.error("Robot Framework test failed with return code %s", result.returncode)
            return False
    
    def cleanup(self):
        """Cleanup proxy infrastructure"""
        if self.proxy_started:
            socket_bridge.stop()
            device_proxy.disconnect()
            self.proxy_started = False
            logger.info("Robot handler cleanup completed")
