"""Robot Framework integration tests for Twister harness."""
import pytest
import tempfile
import subprocess
import os
import logging
from pathlib import Path
from twister_harness import DeviceAdapter

logger = logging.getLogger(__name__)


def test_debug_device_available(dut: DeviceAdapter):
    """Debug test to verify device fixture is available."""
    logger.info("✅ DEBUG: Device fixture is available!")
    logger.info(f"✅ DEBUG: Device: {dut}")
    logger.info(f"✅ DEBUG: Device config: {dut.device_config}")
    logger.info(f"✅ DEBUG: Serial: {dut.device_config.serial}")
    logger.info(f"✅ DEBUG: Platform: {dut.device_config.platform}")
    
    # This test should always pass if device is available
    assert dut is not None
    assert hasattr(dut, 'device_config')


@pytest.mark.robotframework
def test_simple_robot_framework(dut: DeviceAdapter, request):
    """Run the simple_test.robot file using the Twister device."""
    logger.info("✅ Starting Robot Framework test with Twister device")
    logger.info(f"✅ Device available: {dut}")
    logger.info(f"✅ Device config: {dut.device_config}")
    
    # Get the build directory
    build_dir = Path(request.config.getoption("--build-dir"))
    logger.info(f"Build directory: {build_dir}")
    
    # Path to the Robot Framework test file
    robot_file = Path(__file__).parent / "simple_test.robot"
    logger.info(f"Robot Framework file: {robot_file}, exists: {robot_file.exists()}")
    
    if not robot_file.exists():
        pytest.fail(f"Robot Framework file not found: {robot_file}")
    
    # Use REAL device configuration from Twister
    device_config = {
        "DEVICE_SERIAL": getattr(dut.device_config, 'serial', ''),
        "DEVICE_BAUD_RATE": getattr(dut.device_config, 'baudrate', '115200'),
        "DEVICE_RUNNER": getattr(dut.device_config, 'runner', ''),
        "DEVICE_PLATFORM": getattr(dut.device_config, 'platform', ''),
        "BUILD_DIR": str(build_dir),
    }
    
    logger.info(f"✅ Using device config: {device_config}")
    
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
        logger.info(f"Output directory: {output_dir}")
        
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
        
        logger.info(f"Running Robot Framework command: {' '.join(cmd)}")
        
        # Run Robot Framework with timeout
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd(),
            timeout=60
        )
        
        logger.info(f"Robot Framework completed: returncode={result.returncode}")
        
        # Check if test passed
        if result.returncode != 0:
            pytest.fail(f"Robot Framework test failed:\n{result.stdout}\n{result.stderr}")
        
        logger.info("✅ Robot Framework test PASSED")
        
    except subprocess.TimeoutExpired:
        pytest.fail("Robot Framework command timed out after 60 seconds")
    finally:
        # Clean up temporary variable file
        if os.path.exists(var_file_path):
            os.unlink(var_file_path)
