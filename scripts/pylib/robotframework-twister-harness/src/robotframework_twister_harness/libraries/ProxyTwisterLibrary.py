# robotframework-twister-harness/libraries/ProxyTwisterLibrary.py
import socket
import logging
import time
import json
from typing import Any, List, Optional
from abstract.RobotTwisterHarness import RobotTwisterHarness

logger = logging.getLogger(__name__)


class ProxyTwisterLibrary(RobotTwisterHarness):
    """
    Robot Framework library that communicates with device via proxy/socket bridge
    """
    
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = '1.0'
    
    def __init__(self, proxy_host: str = 'localhost', proxy_port: int = 8888):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.client_id = f"robot_{int(time.time())}"
        self.logger = logging.getLogger(__name__)
    
    def connect_to_device(self, build_dir: str, device_type: str, **kwargs) -> bool:
        """
        Connect to device via proxy - note: device should already be connected by Twister
        
        For Robot Framework usage, the device is pre-connected by Twister handler.
        This method just establishes connection to the proxy.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30.0)  # Connection timeout
            self.socket.connect((self.proxy_host, self.proxy_port))
            self.socket.settimeout(10.0)  # Operation timeout
            
            # Test connection
            self.socket.send(b"PING\n")
            response = self.socket.recv(1024).decode().strip()
            
            if response == "PONG":
                self.connected = True
                self.logger.info(f"Connected to device proxy at {self.proxy_host}:{self.proxy_port}")
                return True
            else:
                raise RuntimeError(f"Unexpected ping response: {response}")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to device proxy: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def send_command(self, command: str, timeout: float = None) -> str:
        """Send command to device via proxy and return response"""
        if not self.connected or not self.socket:
            raise RuntimeError("Not connected to device proxy")
        
        try:
            if timeout:
                original_timeout = self.socket.gettimeout()
                self.socket.settimeout(timeout)
            
            # Send command
            self.socket.send(f"COMMAND:{command}\n".encode('utf-8'))
            
            # Wait for response
            response_data = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in response_data:
                    break
            
            response = response_data.decode('utf-8').strip()
            
            # Parse response
            if response.startswith("RESPONSE:"):
                return response[9:]
            elif response.startswith("ERROR:"):
                raise RuntimeError(response[6:])
            else:
                return response
                
        except socket.timeout:
            raise RuntimeError(f"Timeout waiting for response to command: {command}")
        except Exception as e:
            raise RuntimeError(f"Error sending command: {e}")
        finally:
            if timeout and 'original_timeout' in locals():
                self.socket.settimeout(original_timeout)
    
    def read_response(self, timeout: float = None) -> str:
        """Read response from device - for Proxy, use send_command instead"""
        self.logger.warning("read_response not typically used with proxy - use send_command")
        return self.send_command("", timeout)
    
    def wait_for_prompt(self, prompt: str, timeout: float = 30.0) -> bool:
        """Wait for specific prompt to appear"""
        start_time = time.time()
        accumulated_output = ""
        
        while time.time() - start_time < timeout:
            try:
                # Send empty command to get current output
                response = self.send_command("", timeout=2.0)
                accumulated_output += response + "\n"
                
                if prompt in accumulated_output:
                    self.logger.info(f"Found prompt: {prompt}")
                    return True
                    
            except RuntimeError as e:
                if "Timeout" not in str(e):
                    raise
        
        self.logger.error(f"Timeout waiting for prompt: {prompt}")
        return False
    
    def disconnect_from_device(self):
        """Disconnect from device proxy"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
        self.logger.info("Disconnected from device proxy")
    
    # Robot Framework specific keyword aliases
    def open_device_connection(self, proxy_host: str = None, proxy_port: int = None):
        """Robot Framework keyword: Open connection to device proxy"""
        if proxy_host:
            self.proxy_host = proxy_host
        if proxy_port:
            self.proxy_port = proxy_port
            
        return self.connect_to_device("", "")  # Device is pre-connected
    
    def write_to_device(self, data: str, timeout: float = 30.0):
        """Robot Framework keyword: Write data to device"""
        return self.send_command(data, timeout)
    
    def read_from_device(self, timeout: float = 10.0) -> str:
        """Robot Framework keyword: Read from device"""
        return self.send_command("", timeout)
    
    def close_device_connection(self):
        """Robot Framework keyword: Close device connection"""
        return self.disconnect_from_device()
    
    def execute_command_and_verify(self, command: str, expected: str, timeout: float = 30.0) -> str:
        """Execute command and verify response contains expected text"""
        response = self.send_command(command, timeout)
        if expected not in response:
            raise AssertionError(f"Expected '{expected}' in response, but got: {response}")
        return response
    
    def get_proxy_status(self) -> dict:
        """Get proxy status information"""
        try:
            self.socket.send(b"STATUS\n")
            response = self.socket.recv(1024).decode().strip()
            if response.startswith("STATUS:"):
                return json.loads(response[7:])
            return {"error": "Invalid status response"}
        except Exception as e:
            return {"error": str(e)}
