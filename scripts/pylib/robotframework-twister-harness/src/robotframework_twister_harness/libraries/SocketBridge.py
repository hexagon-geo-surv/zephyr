# robotframework-twister-harness/libraries/SocketBridge.py
import socket
import threading
import logging
import json
import time
from typing import Dict, Any
from DeviceProxy import device_proxy

logger = logging.getLogger(__name__)


class SocketBridge:
    """Socket bridge that provides TCP access to the device proxy"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888):
        self.host = host
        self.port = port
        self._running = False
        self._server_thread = None
        self._client_threads: List[threading.Thread] = []
        self._clients: List[socket.socket] = []
        self._clients_lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> bool:
        """Start the socket bridge server"""
        if self._running:
            self.logger.warning("Socket bridge already running")
            return True
            
        try:
            self._running = True
            self._server_thread = threading.Thread(
                target=self._server_loop, 
                daemon=True,
                name="SocketBridgeServer"
            )
            self._server_thread.start()
            
            self.logger.info(f"Socket bridge started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start socket bridge: {e}")
            self._running = False
            return False
    
    def stop(self):
        """Stop the socket bridge server"""
        self.logger.info("Stopping socket bridge")
        self._running = False
        
        with self._clients_lock:
            for client_socket in self._clients:
                try:
                    client_socket.close()
                except:
                    pass
            self._clients.clear()
        
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=5.0)
    
    def _server_loop(self):
        """Main server loop accepting client connections"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.settimeout(1.0)  # Allow checking self._running
            
            try:
                server_socket.bind((self.host, self.port))
                server_socket.listen(5)
                
                self.logger.info(f"Socket bridge listening on {self.host}:{self.port}")
                
                while self._running:
                    try:
                        client_socket, address = server_socket.accept()
                        self.logger.info(f"Client connected from {address}")
                        
                        # Handle client in separate thread
                        client_thread = threading.Thread(
                            target=self._handle_client,
                            args=(client_socket, address),
                            daemon=True
                        )
                        client_thread.start()
                        
                        with self._clients_lock:
                            self._clients.append(client_socket)
                            self._client_threads.append(client_thread)
                            
                    except socket.timeout:
                        continue
                    except OSError as e:
                        if self._running:
                            self.logger.error(f"Socket error: {e}")
                        break
                        
            except Exception as e:
                self.logger.error(f"Server loop error: {e}")
            finally:
                self.logger.info("Socket bridge server loop ended")
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle communication with a single client"""
        client_id = f"{address[0]}:{address[1]}"
        
        try:
            # Register client with device proxy
            response_queue = device_proxy.register_client(client_id)
            client_socket.settimeout(1.0)
            
            self.logger.info(f"Starting client handler for {client_id}")
            
            while self._running and client_socket.fileno() != -1:
                try:
                    # Check for incoming data from client
                    try:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                            
                        message = data.decode('utf-8').strip()
                        if message:
                            self._process_client_message(client_id, client_socket, message)
                            
                    except socket.timeout:
                        continue
                    
                    # Check for outgoing data from device
                    try:
                        response = response_queue.get(timeout=0.1)
                        if response:
                            client_socket.send(f"{response}\n".encode('utf-8'))
                    except queue.Empty:
                        continue
                        
                except (socket.error, ConnectionResetError, BrokenPipeError) as e:
                    self.logger.info(f"Client {client_id} disconnected: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Client handler error for {client_id}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Client setup error for {client_id}: {e}")
        finally:
            # Cleanup
            device_proxy.unregister_client(client_id)
            
            with self._clients_lock:
                if client_socket in self._clients:
                    self._clients.remove(client_socket)
            
            try:
                client_socket.close()
            except:
                pass
            
            self.logger.info(f"Client handler for {client_id} ended")
    
    def _process_client_message(self, client_id: str, client_socket: socket.socket, message: str):
        """Process message from client"""
        try:
            # Simple protocol: "COMMAND:actual_command" or just the command
            if message.startswith("COMMAND:"):
                command = message[8:].strip()
                response = device_proxy.send_command(client_id, command)
                client_socket.send(f"RESPONSE:{response}\n".encode('utf-8'))
            elif message.startswith("PING"):
                client_socket.send(b"PONG\n")
            elif message.startswith("STATUS"):
                status = {
                    "clients": device_proxy.get_client_count(),
                    "running": device_proxy._running
                }
                client_socket.send(f"STATUS:{json.dumps(status)}\n".encode('utf-8'))
            else:
                # Treat as direct command
                response = device_proxy.send_command(client_id, message)
                client_socket.send(f"{response}\n".encode('utf-8'))
                
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            client_socket.send(f"{error_msg}\n".encode('utf-8'))
            self.logger.error(f"Error processing message from {client_id}: {e}")


# Global instance
socket_bridge = SocketBridge()
