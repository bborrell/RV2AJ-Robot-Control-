# RV-2AJ Command Quick Reference

Quick reference guide for all available commands in the `rv2aj_commands` library.

## Import and Setup

```python
from rv2aj_commands import RV2AJCommands

# Connect and initialize
robot = RV2AJCommands()
robot.connect()
robot.initialize()

# ... use robot ...

# Shutdown and disconnect
robot.shutdown()
robot.disconnect()
```

## Command Reference

### Motion Commands

| Command | Description | Example |
|---------|-------------|---------|
| `move_joint(j1, j2, j3, j5, j6)` | Move joints relatively | `robot.move_joint(j1=10.0, j2=-5.0)` |
| `move_to_position(pos, posture)` | Move to taught position | `robot.move_to_position(10)` |
| `move_straight(pos, posture)` | Linear move to position | `robot.move_straight(10, 'O')` |
| `move_position(x, y, z, a, b, c)` | Move to XYZ coordinates | `robot.move_position(100, 200, 300)` |

### Position Teaching

| Command | Description | Example |
|---------|-------------|---------|
| `here(position)` | Save current position | `robot.here(10)` |
| `define_origin(type)` | Define origin | `robot.define_origin(2)` |
| `nest()` | Move to user origin | `robot.nest()` |
| `origin_move()` | Move to origin | `robot.origin_move()` |

### Speed & Timing

| Command | Description | Example |
|---------|-------------|---------|
| `set_speed(speed)` | Set speed level (1-100) | `robot.set_speed(75)` |
| `set_override(pct)` | Set override percentage | `robot.set_override(50)` |
| `timer(seconds)` | Wait for time | `robot.timer(2.5)` |
| `define_speed(params)` | Define detailed speed | `robot.define_speed("...")` |

### Tool Control

| Command | Description | Example |
|---------|-------------|---------|
| `set_tool_length(len)` | Set tool length (mm) | `robot.set_tool_length(50.0)` |
| `set_tool_matrix(x,y,z,a,b,c)` | Set tool coordinate system | `robot.set_tool_matrix(0,0,50,0,0,0)` |

### Gripper Control

| Command | Description | Example |
|---------|-------------|---------|
| `grip_open()` | Open gripper | `robot.grip_open()` |
| `grip_close()` | Close gripper | `robot.grip_close()` |
| `grip_pressure(a1, a2, a3)` | Set grip force | `robot.grip_pressure(50, 50, 50)` |

### I/O Operations

| Command | Description | Example |
|---------|-------------|---------|
| `output_bit(bit, state)` | Set output bit ON/OFF | `robot.output_bit(1, True)` |
| `input_direct(bit)` | Read input bit | `robot.input_direct(1)` |

### Status Queries

| Command | Description | Example |
|---------|-------------|---------|
| `get_position()` | Get joint positions | `pos = robot.get_position()` |
| `where()` | Get XYZ coordinates | `coords = robot.where()` |
| `position_read(pos)` | Read stored position | `robot.position_read(10)` |
| `get_error()` | Read error code | `err = robot.get_error()` |
| `get_version()` | Get firmware version | `ver = robot.get_version()` |

### System Control

| Command | Description | Example |
|---------|-------------|---------|
| `servo_on()` | Turn on servos | `robot.servo_on()` |
| `servo_off()` | Turn off servos | `robot.servo_off()` |
| `reset_alarm()` | Reset alarm | `robot.reset_alarm()` |
| `control_on()` | Enable controller | `robot.control_on()` |
| `initialize()` | Complete initialization | `robot.initialize()` |
| `shutdown()` | Safe shutdown | `robot.shutdown()` |

### Program Control

| Command | Description | Example |
|---------|-------------|---------|
| `halt()` | Stop program | `robot.halt()` |
| `goto(line)` | Jump to line | `robot.goto(100)` |
| `gosub(line)` | Call subroutine | `robot.gosub(200)` |
| `return_sub()` | Return from subroutine | `robot.return_sub()` |
| `end()` | End program | `robot.end()` |

### Conditional Branching

| Command | Description | Example |
|---------|-------------|---------|
| `if_equal(val, line)` | If register == val, goto line | `robot.if_equal(10, 100)` |
| `if_not_equal(val, line)` | If register != val, goto line | `robot.if_not_equal(5, 200)` |
| `if_larger(val, line)` | If register > val, goto line | `robot.if_larger(20, 300)` |
| `if_smaller(val, line)` | If register < val, goto line | `robot.if_smaller(15, 400)` |

## Response Handling

All commands return a `ParsedResponse` object:

```python
response = robot.move_joint(j1=10.0)

# Check success
if response.is_success:
    print("Command succeeded!")

# Check for errors
if response.is_error:
    print(f"Error: {response.error_message}")
    print(f"Code: {response.error_code}")
    print(f"Level: {response.error_level}")
```

### Parse Position Data

```python
response = robot.get_position()
if response.is_success:
    positions = robot.parser.parse_position(response.raw)
    print(f"J1: {positions['J1']}°")
    print(f"J2: {positions['J2']}°")
```

### Parse Coordinate Data

```python
response = robot.where()
if response.is_success:
    coords = robot.parser.parse_coordinates(response.raw)
    print(f"X: {coords['X']} mm")
    print(f"Y: {coords['Y']} mm")
    print(f"Z: {coords['Z']} mm")
```

## Common Patterns

### Pick and Place

```python
with RV2AJCommands() as robot:
    robot.initialize()
    
    # Move to pick position
    robot.move_to_position(10)
    robot.grip_open()
    robot.move_straight(11)  # Approach
    robot.grip_close()
    
    # Move to place position
    robot.move_to_position(20)
    robot.move_straight(21)  # Approach
    robot.grip_open()
    
    # Return home
    robot.move_to_position(1)
    robot.shutdown()
```

### Position Teaching

```python
robot = RV2AJCommands()
robot.connect()
robot.initialize()

# Manually move robot to desired position
input("Move robot to position 1, then press Enter")
robot.here(1)

input("Move robot to position 2, then press Enter")
robot.here(2)

# Now use the positions
robot.move_to_position(1)
robot.move_to_position(2)

robot.shutdown()
robot.disconnect()
```

### Speed Control

```python
robot.set_speed(25)  # Slow for precision
robot.move_to_position(10)

robot.set_speed(100)  # Fast for travel
robot.move_to_position(1)
```

### Error Checking

```python
response = robot.move_joint(j1=10.0)
if response.is_error:
    print(f"Motion failed: {response.error_message}")
    if response.error_info:
        print(f"Cause: {response.error_info.cause}")
        print(f"Fix: {response.error_info.measures}")
    
    # Try to recover
    robot.reset_alarm()
```

## Tips

1. **Use context manager** for automatic cleanup:
   ```python
   with RV2AJCommands() as robot:
       # robot automatically connects and disconnects
   ```

2. **Check responses** for critical operations:
   ```python
   response = robot.servo_on()
   if not response.is_success:
       print("Failed to enable servos!")
   ```

3. **Parse position data** for decision making:
   ```python
   pos = robot.get_position()
   positions = robot.parser.parse_position(pos.raw)
   if positions['J1'] > 45.0:
       # Take action
   ```

4. **Save frequently used positions** for easy recall:
   ```python
   robot.here(1)   # Home position
   robot.here(10)  # Pick position
   robot.here(20)  # Place position
   ```

5. **Use appropriate speeds** for different tasks:
   ```python
   robot.set_speed(25)   # Slow for precision work
   robot.set_speed(100)  # Fast for travel moves
   ```

## Configuration

Edit `rv2aj_config.json` to set your COM port:

```json
{
  "port": "COM3",
  "baudrate": 9600,
  "parity": "EVEN",
  "stopbits": 2,
  "bytesize": 8,
  "timeout": 1.0,
  "prefix": "1;1;"
}
```

## See Also

- **LIBRARY_README.md** - Complete documentation
- **command_examples.py** - 10 comprehensive examples
- **example_usage.py** - Parser and serial communication examples
- **rv2aj_commands.py** - Source code with full API documentation
