# RV-2AJ Serial Communication Library

Professional Python libraries for communicating with the Mitsubishi RV-2AJ robot controller via RS-232 serial communication.

## Features

### `rv2aj_commands.py` - High-Level Command Interface ⭐ **Recommended**
- Complete high-level API for all RV-2AJ commands
- Intuitive method names and parameter handling
- Automatic formatting and validation
- Built-in response parsing
- 50+ ready-to-use command methods including:
  - Motion control (joint, Cartesian, linear)
  - Position teaching and recall
  - Gripper/hand control
  - Speed and timing control
  - I/O operations
  - Status queries

### `rv2aj_serial.py` - Serial Communication Handler
- Clean, object-oriented interface for serial communication
- Configuration loaded from `rv2aj_config.json`
- Automatic connection management
- Context manager support for automatic cleanup
- Built-in methods for common commands (servo on/off, position reading, etc.)
- Optional automatic response parsing

### `rv2aj_response_parser.py` - Response Parser
- Comprehensive parsing of all RV-2AJ response types:
  - **QoK** - Success responses
  - **QeR** - Error responses with detailed error information
  - **Q** - Data responses (position, coordinates, etc.)
- Automatic error code lookup from `RV2AJ_ErrorCodes.json`
- Specialized parsers for position and coordinate data
- Detailed error information including cause and recommended measures

## Installation

No special installation required. Simply ensure you have the required dependencies:

```bash
pip install pyserial
```

## Configuration

Edit `rv2aj_config.json` to set your COM port and serial settings:

```json
{
  "port": "COM3",
  "baudrate": 9600,
  "parity": "EVEN",
  "stopbits": 2,
  "bytesize": 8,
  "timeout": 1.0,
  "prefix": "1;1;",
  "lowercase": true
}
```

## Quick Start

### Recommended: High-Level Command Interface

```python
from rv2aj_commands import RV2AJCommands

# Create robot interface
robot = RV2AJCommands()
robot.connect()

# Initialize robot
robot.initialize()

# Move joints
robot.move_joint(j1=10.0, j2=-5.0, j3=15.0)

# Move to position
robot.move_to_position(10)

# Get current position
response = robot.get_position()
if response.is_success:
    positions = robot.parser.parse_position(response.raw)
    print(f"Joint positions: {positions}")

# Gripper control
robot.grip_open()
robot.grip_close()

# Shutdown
robot.shutdown()
robot.disconnect()
```

### Using Context Manager (Recommended)

```python
from rv2aj_commands import RV2AJCommands

with RV2AJCommands() as robot:
    robot.initialize()
    
    # Save current position
    robot.here(20)
    
    # Move to Cartesian position
    robot.move_position(100.0, 200.0, 300.0)
    
    # Set speed
    robot.set_speed(75)
    
    # Move back to saved position
    robot.move_to_position(20)
    
    robot.shutdown()
# Automatically disconnected
```

### Alternative: Low-Level Serial Interface

```python
from rv2aj_serial import RV2AJSerial

with RV2AJSerial() as robot:
    robot.initialize_robot()
    
    # Send raw commands
    response = robot.send_and_read("JPOSF")
    
    robot.shutdown_robot()
```

### Error Handling

```python
from rv2aj_serial import RV2AJSerial, RV2AJSerialException

try:
    with RV2AJSerial() as robot:
        # Check for errors
        response = robot.get_error()
        
        if response.is_error:
            print(f"Error Code: {response.error_code}")
            print(f"Level: {response.error_level}")
            print(f"Message: {response.error_message}")
            
            if response.error_info:
                print(f"Cause: {response.error_info.cause}")
                print(f"Measures: {response.error_info.measures}")
                
except RV2AJSerialException as e:
    print(f"Communication error: {e}")
```

### Using Without Parser (Raw Strings)

```python
# Disable automatic parsing to get raw string responses
robot = RV2AJSerial(use_parser=False)
robot.connect()

response = robot.servo_on()  # Returns: "QoK"
print(f"Raw response: {response}")

# Manual parsing if needed
if response.startswith("QoK"):
    print("Success!")

robot.disconnect()
```

## Response Parsing

### Response Types

All controller responses start with a specific prefix:

| Prefix | Type | Description |
|--------|------|-------------|
| `QoK` | Success | Command executed successfully |
| `QeR` | Error | Command failed with error code |
| `Q` | Data | Informational response with data |

### Parsing Examples Methods

### Motion Control

```python
# Joint space motion
robot.move_joint(j1=10.0, j2=-5.0, j3=15.0)  # Relative joint move
robot.move_to_position(10)                    # Move to taught position
robot.move_straight(10)                       # Linear move to position

# Cartesian space motion
robot.move_position(100.0, 200.0, 300.0)     # Move to XYZ coordinates
robot.move_position(100.0, 200.0, 300.0,     # With orientation
                   a=0.0, b=0.0, c=90.0)
```

### Position Teaching

```python
robot.here(10)              # Save current position as #10
robot.define_origin(2)      # Define user origin
robot.nest()                # Move to user origin
robot.origin_move()         # Move to origin
```

### Speed and Timing

```python
robot.set_speed(75)         # Set speed to 75%
robot.set_override(50)      # Set override to 50%
robot.timer(2.5)            # Wait 2.5 seconds
robot.set_tool_length(50.0) # Set tool length
```

### Gripper Control

```python
robot.grip_open()           # Open gripper
robot.grip_close()          # Close gripper
robot.grip_pressure(50, 50, 50)  # Set grip force
```

### I/O Operations

```python
robot.output_bit(1, True)   # Turn ON output bit 1
robot.output_bit(2, False)  # Turn OFF output bit 2
robot.input_direct(1)       # Read input bit 1
```

### Status Queries

```python
robot.get_position()        # Get joint positions (JPOSF)
robot.where()               # Get XYZ coordinates (WH)
robot.get_error()           # Read error code (ER)
robot.get_version()         # Get firmware version (VR)
robot.position_read(10)     # Read stored position #10
```

### Program Control

```python
robot.halt()                # Stop program
robot.goto(100)             # Jump to line 100
robot.gosub(200)            # Call subroutine at line 200
robot.return_sub()          # Return from subroutine
robot.end()                 # End program
```

### Conditional Branching

```python
robot.if_equal(10, 100)     # If register == 10, goto line 100
robot.if_not_equal(5, 200)  # If register != 5, goto line 200
robot.if_larger(20, 300)    # If register > 20, goto line 300
robot.if_smaller(15, 400)   # If register < 15, goto line 400
```

### Tool Configuration

```python
robot.set_tool_length(50.0)           # Set tool length
robot.set_tool_matrix(0, 0, 50,       # Set tool coordinate system
                     0, 0, 0)
```

### System Control

```python
robot.servo_on()            # Turn on servos (SRVON)
robot.servo_off()           # Turn off servos (SRVOFF)
robot.reset_alarm()         # Reset alarm (RSTALRM)
robot.control_on()          # Enable controller (CNTLON)
robot.initialize()          # Complete initialization
robot.shutdown()            # Safe shutdown
```

### Custom Commands
### Example Files

1. **`command_examples.py`** - High-level command examples ⭐ **Start here**
   - Basic motion control
   - Position teaching and recall
   - Gripper control
   - Speed control
   - I/O operations
   - Tool setup
   - Error handling
   - Complex sequences

2. **`example_usage.py`** - Serial communication examples
   - Parser examples (no robot required)
   - Error handling
   - Position monitoring
   - Custom commands

### Run Examples

```bashCommands Class (Recommended)

#### Constructor
```python
RV2AJCommands(config_path="rv2aj_config.json", use_parser=True)
```
- `config_path`: Path to configuration JSON file
- `use_parser`: Enable automatic response parsing (default: True)

#### Methods (50+ Available)

All methods return a `ParsedResponse` object (or raw string if parser disabled).

**Motion Commands:**
- `move_joint(j1, j2, j3, j4, j5, j6)` - Move joints (relative)
- `move_to_position(position, posture)` - Move to taught position
- `move_straight(position, posture)` - Linear move to position
- `move_position(x, y, z, a, b, c)` - Move to Cartesian coordinates

**Position Teaching:**
- `here(position)` - Save current position
- `define_origin(origin_type)` - Define origin
- `nest()` - Move to user origin
- `origin_move()` - Move to origin

**Speed Control:**
- `set_speed(speed)` - Set speed level
- `set_override(percentage)` - Set override percentage
- `timer(seconds)` - Pause execution

**Gripper Control:**
- `grip_open()` - Open gripper
- `grip_close()` - Close gripper
- `grip_pressure(a1, a2, a3)` - Set grip force

**I/O Operations:**
- `output_bit(bit, state)` - Set output bit
- `input_direct(bit)` - Read input bit

**Status Queries:**
- `get_position()` - Get joint positions
- `where()` - Get Cartesian coordinates
- `get_error()` - Read error code
- `get_version()` - Get firmware version

**System Control:**
- `initialize()` - Complete initialization
- `shutdown()` - Safe shutdown
- `servo_on()` / `servo_off()` - Control servos
- `reset_alarm()` - Reset alarm

See `rv2aj_commands.py` for complete list.

### RV2AJSerial Class (Low-Level)
# Test response parser (no robot required)
python example_usage.py

# Run command examples (robot required)
# Edit command_examples.py and uncomment desired examples
python command_examples.py
robot.get_coordinates()   # Get XYZ coordinates (WH)
robot.get_error()         # Read error code (ER)
robot.initialize_robot()  # Complete initialization sequence
robot.shutdown_robot()    # Safe shutdown
```

### Custom Commands

```python
# Send any command
response = robot.send_and_read("JPOSF")

# Send without prefix (if needed)
response = robot.send_and_read("COMMAND", use_prefix=False)

# Send and read separately
robot.send_command("JPOSF")
time.sleep(0.2)
response = robot.read_response()
```

## Error Levels

The controller uses three error levels:

- **H (High)**: Critical error, servo OFF
- **L (Low)**: Error, operation stopped
- **C (Warning)**: Warning, operation continues

```python
response = robot.get_error()
if response.is_error:
    level = response.error_level
    if level == 'H':
        print("Critical error - servos disabled")
    elif level == 'L':
        print("Error - operation stopped")
    elif level == 'C':
        print("Warning - can continue")
```

## Position Data Format

Position responses contain semicolon-delimited joint angles:

```
QoK;J1;10.50;J2;-5.30;J3;45.00;J5;0.00;J6;90.00
```

The parser automatically extracts this into a dictionary:

```python
response = robot.get_position()
positions = robot.parser.parse_position(response.raw)
# {'J1': 10.5, 'J2': -5.3, 'J3': 45.0, 'J5': 0.0, 'J6': 90.0}
```

Note: RV-2AJ has 5 joints (J4 is not present).

## Examples

See `example_usage.py` for comprehensive examples including:
- Basic commands with automatic parsing
- Error handling and error code lookup
- Position monitoring
- Custom commands
- Raw string mode (without parser)
- Context manager usage

Run the parser test (no robot required):
```bash
python example_usage.py
```

Run full examples (robot required):
```python
# Edit example_usage.py and uncomment desired examples in main()
```

## API Reference

### RV2AJSerial Class

#### Constructor
```python
RV2AJSerial(config_path="rv2aj_config.json", use_parser=True)
```
- `config_path`: Path to configuration JSON file
- `use_parser`: Enable automatic response parsing (default: True)

#### Methods
- `connect()` - Establish serial connection
- `disconnect()` - Close serial connection
- `send_command(command, use_prefix=True, terminator="\r\r\n")` - Send command
- `read_response(timeout=None, parse=None)` - Read response
- `send_and_read(command, use_prefix=True, read_delay=0.2, parse=None)` - Send and read
- `clear_buffer()` - Clear input buffer

### RV2AJResponseParser Class

#### Constructor
```python
RV2AJResponseParser(error_codes_path="RV2AJ_ErrorCodes.json")
```

#### Methods
- `parse(response)` - Parse any response, returns `ParsedResponse`
- `parse_position(response)` - Parse JPOSF response, returns dict of joints
- `parse_coordinates(response)` - Parse WH response, returns dict of coords
- `lookup_error(code)` - Look up error information by code
- `extract_value(response)` - Extract single value from response

### ParsedResponse Object

#### Properties
- `raw` - Original response string
- `response_type` - Type (SUCCESS, ERROR, DATA, UNKNOWN)
- `is_success` - True if success response
- `is_error` - True if error response
- `is_data` - True if data response
- `error_code` - Error code if error response
- `error_info` - Detailed ErrorInfo object if available
- `error_message` - Error message string
- `error_level` - Error level (H/L/C)
- `data` - Parsed data dictionary
- `data_list` - List of raw data values

## Troubleshooting

### Connection Issues
- Verify COM port in `rv2aj_config.json` matches your setup
- Check that controller is powered on
- Ensure RS-232 cable is properly connected
- Verify no other program is using the COM port

### Parser Issues
- If parser is not working, check that `RV2AJ_ErrorCodes.json` exists
- Use `use_parser=False` to fall back to raw string mode
- Override parsing per-command: `robot.send_and_read("CMD", parse=False)`

### Timeout Issues
- Increase timeout in `rv2aj_config.json`
- Use longer `read_delay` parameter: `robot.send_and_read("CMD", read_delay=0.5)`
- Override timeout per-read: `robot.read_response(timeout=2.0)`

## License

This project is provided as-is for use with Mitsubishi RV-2AJ robot systems.

## Support

For issues or questions:
1. Check the error message and error code lookup
2. Review the examples in `example_usage.py`
3. Verify configuration in `rv2aj_config.json`
4. Check the Mitsubishi RS-232 protocol manual in the Manuals folder
