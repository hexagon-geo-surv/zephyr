from abc import ABC, abstractmethod
from typing import Any, Dict


class RobotTwisterHarness(ABC):
    """Abstract base class for Robot Framework Twister integration"""
    
    @abstractmethod
    def connect_to_device(self, build_dir: str, device_type: str, **kwargs) -> bool:
        """Connect to device using Twister harness"""
        pass
    
    @abstractmethod
    def send_command(self, command: str, timeout: float = None) -> str:
        """Send command to device and return response"""
        pass
    
    @abstractmethod
    def read_response(self, timeout: float = None) -> str:
        """Read response from device"""
        pass
    
    @abstractmethod
    def wait_for_prompt(self, prompt: str, timeout: float = None) -> bool:
        """Wait for specific prompt"""
        pass
    
    @abstractmethod
    def disconnect_from_device(self):
        """Disconnect from device"""
        pass
