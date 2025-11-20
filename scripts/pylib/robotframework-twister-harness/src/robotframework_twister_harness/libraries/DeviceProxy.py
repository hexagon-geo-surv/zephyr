# robotframework-twister-harness/libraries/DeviceProxy.py
import threading
import queue
import logging
import time
from typing import Dict, List, Tuple, Optional
from twister_harness.device.factory import DeviceFactory
from twister_harness.twister_harness_config import DeviceConfig
from pathlib import Path

logger = logging.getLogger(__name__)


class DeviceProxy:
    """
    Proxy that manages exclusive device access and allows multiple consumers
    to communicate with the device without resource contention.
    """
    _instance: Optional['DeviceProxy'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.device = None
        self._command_queue = queue.Queue()
        self._response_queues: Dict[str, queue.Queue] = {}
        self._broadcast_queue = queue.Queue()
        self._reader_thread = None
        self._broadcast_thread = None
        self._running = False
        self._device_lock = threading.RLock()
        self._clients_lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        self._initialized = True
    
    def connect_device(self, build_dir: str, device_type: str, **kwargs) -> bool:
        """Connect to device - should be called once by Twister"""
        with self._device_lock:
            if self.device is not None:
                self.logger.info("Device already connected")
                return True
                
            try:
                device_config = DeviceConfig(
                    type=device_type,
                    build_dir=Path(build_dir),
                    serial=kwargs.get('serial_port', ''),
                    baud=kwargs.get('baudrate', 115200),
                    platform=kwargs.get('platform', ''),
                    runner=kwargs.get('runner', '')
                )
                
                device_class = DeviceFactory.get_device(device_type)
                self.device = device_class(device_config)
                self.device.launch()
                
                # Start reader and broadcast threads
                self._running = True
                self._reader_thread = threading.Thread(
                    target=self._read_loop, 
                    daemon=True,
                    name="DeviceReader"
                )
                self._reader_thread.start()
                
                self._broadcast_thread = threading.Thread(
                    target=self._broadcast_loop,
                    daemon=True,
                    name="BroadcastHandler"
                )
                self._broadcast_thread.start()
                
                self.logger.info(f"Device proxy connected to {device_type} at {build_dir}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to connect device: {e}")
                return False
    
    def register_client(self, client_id: str) -> queue.Queue:
        """Register a new client (e.g., Robot Framework) and return response queue"""
        with self._clients_lock:
            if client_id in self._response_queues:
                self.logger.warning(f"Client {client_id} already registered")
                return self._response_queues[client_id]
                
            response_queue = queue.Queue()
            self._response_queues[client_id] = response_queue
            self.logger.info(f"Client {client_id} registered")
            return response_queue
    
    def unregister_client(self, client_id: str):
        """Unregister a client"""
        with self._clients_lock:
            if client_id in self._response_queues:
                self._response_queues.pop(client_id)
                self.logger.info(f"Client {client_id} unregistered")
    
    def send_command(self, client_id: str, command: str, timeout: float = 30.0) -> str:
        """Send command to device on behalf of a client and wait for response"""
        if not self._running or not self.device:
            raise RuntimeError("Device not connected")
        
        # Create a unique marker for this command
        command_marker = f"CMD_{client_id}_{time.time()}"
        
        with self._device_lock:
            try:
                # Send command to device
                self.device.write(f"{command}\n".encode())
                self.logger.debug(f"Client {client_id} sent command: {command}")
                
                # Wait for response
                response_queue = self._response_queues.get(client_id)
                if not response_queue:
                    raise RuntimeError(f"Client {client_id} not registered")
                
                # Collect responses until timeout
                start_time = time.time()
                responses = []
                
                while time.time() - start_time < timeout:
                    try:
                        response = response_queue.get(timeout=0.1)
                        responses.append(response)
                        
                        # Check if we have a complete response (heuristic)
                        if self._is_response_complete(responses, command):
                            full_response = "\n".join(responses)
                            self.logger.debug(f"Client {client_id} received response: {full_response}")
                            return full_response
                            
                    except queue.Empty:
                        continue
                
                # Timeout occurred
                partial_response = "\n".join(responses)
                self.logger.warning(f"Timeout waiting for response from command: {command}")
                return partial_response or "TIMEOUT"
                
            except Exception as e:
                self.logger.error(f"Error sending command {command}: {e}")
                raise
    
    def _is_response_complete(self, responses: List[str], command: str) -> bool:
        """Heuristic to determine if response is complete"""
        if not responses:
            return False
            
        full_response = "\n".join(responses).lower()
        command_lower = command.lower()
        
        # Common completion indicators
        completion_indicators = [
            "uart",  # Prompt
            "zephyr",  # Common in boot messages
            "error",   # Error messages
            "success", # Success messages
            "done",    # Completion
        ]
        
        # If we see a prompt-like pattern, consider it complete
        for indicator in completion_indicators:
            if indicator in full_response and command_lower not in full_response:
                return True
        
        # If we have multiple lines and last line looks like prompt
        if len(responses) > 1 and any(indicator in responses[-1].lower() for indicator in completion_indicators):
            return True
            
        return False
    
    def _read_loop(self):
        """Continuously read from device and distribute to clients"""
        self.logger.info("Starting device read loop")
        
        while self._running and self.device:
            try:
                response = self.device.readline(timeout=0.5)
                if response and response.strip():
                    self.logger.debug(f"Device output: {response.strip()}")
                    
                    # Broadcast to all registered clients
                    with self._clients_lock:
                        for client_id, response_queue in self._response_queues.items():
                            try:
                                response_queue.put(response, timeout=1.0)
                            except queue.Full:
                                self.logger.warning(f"Response queue full for client {client_id}")
                
            except Exception as e:
                if self._running:  # Only log if we're supposed to be running
                    self.logger.debug(f"Read error (may be normal): {e}")
    
    def _broadcast_loop(self):
        """Handle broadcast messages to all clients"""
        while self._running:
            try:
                message = self._broadcast_queue.get(timeout=1.0)
                with self._clients_lock:
                    for client_id, response_queue in self._response_queues.items():
                        try:
                            response_queue.put(f"BROADCAST: {message}", timeout=0.5)
                        except queue.Full:
                            pass
            except queue.Empty:
                continue
    
    def broadcast_message(self, message: str):
        """Broadcast a message to all clients"""
        self._broadcast_queue.put(message)
    
    def get_client_count(self) -> int:
        """Get number of registered clients"""
        with self._clients_lock:
            return len(self._response_queues)
    
    def disconnect(self):
        """Disconnect device and cleanup"""
        self.logger.info("Disconnecting device proxy")
        
        self._running = False
        
        with self._device_lock:
            if self.device:
                try:
                    self.device.close()
                except Exception as e:
                    self.logger.error(f"Error closing device: {e}")
                finally:
                    self.device = None
        
        # Clear all client queues
        with self._clients_lock:
            for client_id, response_queue in self._response_queues.items():
                try:
                    response_queue.put("DEVICE_DISCONNECTED")
                except:
                    pass
            self._response_queues.clear()
        
        self.logger.info("Device proxy disconnected")


# Global instance
device_proxy = DeviceProxy()
