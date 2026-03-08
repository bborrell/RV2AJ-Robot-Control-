"""
RV-2AJ Serial Communication Library

This library provides a clean interface for serial communication with the
Mitsubishi RV-2AJ robot controller. Configuration is loaded from rv2aj_config.json.

Usage:
    from rv2aj_serial import RV2AJSerial
    
    robot = RV2AJSerial()
    robot.connect()
    robot.send_command("SRVON")
    response = robot.read_response()
    robot.disconnect()
"""

import json
import serial
import time
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from rv2aj_response_parser import RV2AJResponseParser, ParsedResponse
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    ParsedResponse = None


class RV2AJSerialException(Exception):
    """Custom exception for RV-2AJ serial communication errors."""
    pass


class RV2AJSerial:
    """
    Serial communication handler for Mitsubishi RV-2AJ robot controller.
    
    Attributes:
        port (str): Serial port name (e.g., 'COM3')
        baudrate (int): Baud rate for serial communication
        parity (str): Parity setting ('EVEN', 'ODD', 'NONE', etc.)
        stopbits (int): Number of stop bits
        bytesize (int): Number of data bits
        timeout (float): Read timeout in seconds
        prefix (str): Command prefix (typically '1;1;')
    """
    
    def __init__(self, config_path: str = "RV2AJ_Reference_JSONs/rv2aj_config.json", 
                 use_parser: bool = True, verbose_callback=None):
        """
        Initialize the serial communication handler.
        
        Args:
            config_path (str): Path to the configuration JSON file
            use_parser (bool): Whether to use response parser for automatic parsing
            verbose_callback: Optional callback function for verbose logging (func(message: str))
        """
        self.config_path = config_path
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.use_parser = use_parser and PARSER_AVAILABLE
        self.verbose_callback = verbose_callback
        
        # Initialize response parser if available
        self.parser = RV2AJResponseParser() if self.use_parser else None
        
        # Load configuration
        self._load_config()
        
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Serial port settings
            self.port = config.get('port', 'COM3')
            self.baudrate = int(config.get('baudrate', 9600))
            self.bytesize = int(config.get('bytesize', 8))
            self.stopbits = int(config.get('stopbits', 2))
            self.timeout = float(config.get('timeout', 1.0))
            
            # Command settings
            self.prefix = config.get('prefix', '1;1;')
            self.lowercase = config.get('lowercase', True)
            self.edit_slot = int(config.get('edit_slot', 9))
            
            # Convert parity string to pyserial constant
            parity_str = config.get('parity', 'EVEN').upper()
            parity_map = {
                'NONE': serial.PARITY_NONE,
                'EVEN': serial.PARITY_EVEN,
                'ODD': serial.PARITY_ODD,
                'MARK': serial.PARITY_MARK,
                'SPACE': serial.PARITY_SPACE
            }
            self.parity = parity_map.get(parity_str, serial.PARITY_EVEN)
            
        except FileNotFoundError as e:
            raise RV2AJSerialException(f"Configuration error: {e}")
        except json.JSONDecodeError as e:
            raise RV2AJSerialException(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise RV2AJSerialException(f"Error loading configuration: {e}")
    
    def connect(self) -> bool:
        """
        Establish serial connection to the robot controller.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            RV2AJSerialException: If connection fails
        """
        if self.is_connected:
            print("Already connected to robot controller.")
            return True
        
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout
            )
            
            time.sleep(0.5)  # Allow time for connection to stabilize
            
            if self.serial_port.is_open:
                self.is_connected = True
                print(f"Connected to robot controller on {self.port}")
                return True
            else:
                raise RV2AJSerialException("Serial port failed to open")
                
        except serial.SerialException as e:
            raise RV2AJSerialException(f"Failed to connect to {self.port}: {e}")
        except Exception as e:
            raise RV2AJSerialException(f"Unexpected error during connection: {e}")
    
    def disconnect(self) -> None:
        """Close the serial connection."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.is_connected = False
            print("Disconnected from robot controller.")
    
    def send_command(self, command: str, use_prefix: bool = True, 
                    terminator: str = "\r\r\n") -> None:
        """
        Send a command to the robot controller.
        
        Args:
            command (str): Command to send (e.g., 'SRVON', 'RSTALRM')
            use_prefix (bool): Whether to prepend the command prefix (default: True)
            terminator (str): Line terminator to append (default: '\r\r\n')
            
        Raises:
            RV2AJSerialException: If not connected or send fails
        """
        if not self.is_connected or not self.serial_port:
            raise RV2AJSerialException("Not connected to robot controller")
        
        try:
            # Build full command
            if use_prefix:
                full_command = f"{self.prefix}{command}"
            else:
                full_command = command
            
            # Add terminator
            full_command += terminator
            
            # Log if verbose callback is set
            if self.verbose_callback:
                self.verbose_callback(f"TX → {repr(full_command)}")
            
            # Encode and send
            command_bytes = full_command.encode('utf-8')
            self.serial_port.write(command_bytes)
            
        except serial.SerialException as e:
            raise RV2AJSerialException(f"Failed to send command: {e}")
        except Exception as e:
            raise RV2AJSerialException(f"Unexpected error sending command: {e}")
    
    def send_no_response(self, command: str, use_prefix: bool = True, 
                         terminator: str = "\r\r\n", clear_buffer: bool = True) -> None:
        """
        Send command without waiting for or parsing response (fire-and-forget).
        Used for high-speed continuous operations like jogging.
        
        Args:
            command (str): Command to send
            use_prefix (bool): Whether to prepend the command prefix
            terminator (str): Line terminator to append
            clear_buffer (bool): Whether to clear input buffer after send
            
        Note:
            This method does NOT wait for QoK response. Use for time-critical
            operations where response isn't needed (e.g., continuous JOG).
            Input buffer is cleared to prevent overflow during rapid commands.
        """
        if not self.is_connected or not self.serial_port:
            raise RV2AJSerialException("Not connected to robot controller")
        
        try:
            # Build and send command
            if use_prefix:
                full_command = f"{self.prefix}{command}"
            else:
                full_command = command
            
            full_command += terminator
            
            # Log if verbose callback is set
            if self.verbose_callback:
                self.verbose_callback(f"TX → {repr(full_command)} [no-wait]")
            
            # Send command
            command_bytes = full_command.encode('utf-8')
            self.serial_port.write(command_bytes)
            self.serial_port.flush()  # Ensure sent immediately
            
            # Clear input buffer to prevent overflow from accumulating QoK responses
            if clear_buffer and self.serial_port.in_waiting > 0:
                self.serial_port.reset_input_buffer()
            
        except serial.SerialException as e:
            raise RV2AJSerialException(f"Failed to send command: {e}")
        except Exception as e:
            raise RV2AJSerialException(f"Unexpected error sending command: {e}")
    
    def read_response(self, timeout: Optional[float] = None, 
                     parse: Optional[bool] = None):
        """
        Read response from the robot controller.
        
        Args:
            timeout (float, optional): Override default timeout for this read
            parse (bool, optional): Whether to parse response (defaults to use_parser setting)
            
        Returns:
            ParsedResponse if parsing enabled, str otherwise
            
        Raises:
            RV2AJSerialException: If not connected or read fails
        """
        if not self.is_connected or not self.serial_port:
            raise RV2AJSerialException("Not connected to robot controller")
        
        try:
            if timeout is not None:
                original_timeout = self.serial_port.timeout
                self.serial_port.timeout = timeout
            
            response = self.serial_port.readline()
            response_str = response.decode('utf-8').strip()
            
            # Log if verbose callback is set
            if self.verbose_callback:
                self.verbose_callback(f"RX ← {repr(response_str)}")
            
            if timeout is not None:
                self.serial_port.timeout = original_timeout
            
            # Decide whether to parse
            should_parse = parse if parse is not None else self.use_parser
            
            if should_parse and self.parser:
                return self.parser.parse(response_str)
            else:
                return response_str
            
        except serial.SerialException as e:
            raise RV2AJSerialException(f"Failed to read response: {e}")
        except UnicodeDecodeError as e:
            raise RV2AJSerialException(f"Failed to decode response: {e}")
        except Exception as e:
            raise RV2AJSerialException(f"Unexpected error reading response: {e}")
    
    def send_and_read(self, command: str, use_prefix: bool = True,
                     read_delay: float = 0.2, parse: Optional[bool] = None):
        """
        Send a command and read the response.
        
        Args:
            command (str): Command to send
            use_prefix (bool): Whether to prepend the command prefix
            read_delay (float): Delay before reading response (seconds)
            parse (bool, optional): Whether to parse response (defaults to use_parser setting)
            
        Returns:
            ParsedResponse if parsing enabled, str otherwise
        """
        self.send_command(command, use_prefix=use_prefix)
        time.sleep(read_delay)
        return self.read_response(parse=parse)
    
    def clear_buffer(self) -> None:
        """Clear the input buffer."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.reset_input_buffer()
    
    def servo_on(self):
        """
        Turn on robot servos.
        
        Returns:
            ParsedResponse if parsing enabled, str otherwise
        """
        return self.send_and_read("SRVON")
    
    def servo_off(self):
        """
        Turn off robot servos.
        
        Returns:
            ParsedResponse if parsing enabled, str otherwise
        """
        return self.send_and_read("SRVOFF")
    
    def reset_alarm(self):
        """
        Reset controller alarm.
        
        Returns:
            ParsedResponse if parsing enabled, str otherwise
        """
        return self.send_and_read("RSTALRM")
    
    def control_on(self):
        """
        Turn on controller.
        
        Returns:
            ParsedResponse if parsing enabled, str otherwise
        """
        return self.send_and_read("CNTLON")
    
    def get_position(self):
        """
        Get current joint positions using JPOSF command.
        
        Returns:
            ParsedResponse with position data if parsing enabled, str otherwise
        """
        return self.send_and_read("JPOSF")
    
    def get_coordinates(self):
        """
        Get current XYZ coordinates using WH command.
        
        Returns:
            ParsedResponse with coordinate data if parsing enabled, str otherwise
        """
        return self.send_and_read("WH")
    
    def get_error(self):
        """
        Read current error code using ER command.
        
        Returns:
            ParsedResponse if parsing enabled, str otherwise
        """
        return self.send_and_read("ER")
    
    def initialize_robot(self) -> Dict[str, str]:
        """
        Initialize robot: reset alarm, turn on controller, and enable servos.
        
        Returns:
            dict: Dictionary with responses for each step
        """
        responses = {}
        
        print("Resetting alarm...")
        responses['reset_alarm'] = self.reset_alarm()
        time.sleep(0.2)
        
        print("Turning on controller...")
        responses['control_on'] = self.control_on()
        time.sleep(0.5)
        
        print("Turning on servos...")
        responses['servo_on'] = self.servo_on()
        
        print("Robot initialized successfully!")
        return responses
    
    def shutdown_robot(self) -> str:
        """
        Safely shut down robot by turning off servos.
        
        Returns:
            str: Response from controller
        """
        print("Shutting down robot...")
        response = self.servo_off()
        print("Robot servos disabled.")
        return response
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def __del__(self):
        """Destructor to ensure port is closed."""
        if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
            self.serial_port.close()


# Example usage
if __name__ == "__main__":
    # Example 1: Basic usage with automatic parsing
    try:
        robot = RV2AJSerial()  # Parser enabled by default
        robot.connect()
        
        # Initialize robot
        print("\nInitializing robot...")
        responses = robot.initialize_robot()
        
        # Check responses
        for cmd, response in responses.items():
            if hasattr(response, 'is_success'):
                status = "✓ Success" if response.is_success else f"✗ Error: {response.error_message}"
            else:
                status = response
            print(f"  {cmd}: {status}")
        
        # Get position with automatic parsing
        print("\nGetting position...")
        response = robot.get_position()
        if hasattr(response, 'is_success') and response.is_success:
            if robot.parser:
                positions = robot.parser.parse_position(response.raw)
                print(f"  Joint positions: {positions}")
            else:
                print(f"  Raw response: {response}")
        
        # Send custom command
        print("\nSending custom command...")
        response = robot.send_and_read("JPOSF")
        print(f"  Response type: {response.response_type.value if hasattr(response, 'response_type') else 'raw'}")
        
        # Shutdown
        robot.shutdown_robot()
        robot.disconnect()
        
    except RV2AJSerialException as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Using without parser (raw strings)
    try:
        robot = RV2AJSerial(use_parser=False)
        robot.connect()
        
        response = robot.send_and_read("SRVON")
        print(f"Raw response: {response}")
        
        robot.disconnect()
        
    except RV2AJSerialException as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Using context manager
    try:
        with RV2AJSerial() as robot:
            responses = robot.initialize_robot()
            
            # Get error status
            error_response = robot.get_error()
            if hasattr(error_response, 'is_error') and error_response.is_error:
                print(f"Controller has error: {error_response.error_message}")
            
            robot.shutdown_robot()
            
    except RV2AJSerialException as e:
        print(f"Error: {e}")
