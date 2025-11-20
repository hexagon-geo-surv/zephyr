# tests/robot/robot_with_pytest/robot_tests/SerialKeywords.py
"""Custom Robot Framework keywords for serial communication."""
import time
import serial
from serial import SerialException


class SerialKeywords:
    """Custom keywords for serial communication."""

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    
    def __init__(self):
        self.ser = None

    def open_serial_port(self, port, baudrate=115200, timeout=5):
        """Open serial port."""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=int(baudrate),
                timeout=timeout,
                write_timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            # Clear buffers and wait for stabilization
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(2.0)  # Increased wait for device boot
            return True
        except SerialException as e:
            raise AssertionError(f"Failed to open serial port {port}: {e}")

    def close_serial_port(self):
        """Close serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

    def write_serial_data(self, data):
        """Write data to serial port."""
        if not self.ser or not self.ser.is_open:
            raise AssertionError("Serial port is not open")

        # Ensure newline for commands
        if not data.endswith('\n'):
            data += '\n'
            
        self.ser.write(data.encode('utf-8'))
        self.ser.flush()
        time.sleep(0.1)  # Small delay after write

    def read_serial_data_until(self, expected, timeout=10):
        """Read serial data until expected string is found."""
        if not self.ser or not self.ser.is_open:
            raise AssertionError("Serial port is not open")

        start_time = time.time()
        buffer = ""

        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                print(f"Received: {repr(data)}")  # Debug output

                if expected in buffer:
                    return buffer

            time.sleep(0.1)

        raise AssertionError(f"Timeout waiting for '{expected}'. Got: {buffer}")

    def clear_serial_buffer(self):
        """Clear serial input buffer."""
        if self.ser and self.ser.is_open:
            self.ser.reset_input_buffer()
            time.sleep(0.1)
