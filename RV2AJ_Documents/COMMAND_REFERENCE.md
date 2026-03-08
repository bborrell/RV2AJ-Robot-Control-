# RV-2AJ Command Reference: High-Level Functions → Raw Commands

This document shows the exact raw commands sent by each high-level function, including when the `1;1;` prefix is used.

## Command Format

**With Prefix (Most Commands):**
```
Transmitted: '1;1;SRVON\r\r\n'
            └─┬─┘└─┬─┘└─┬──┘
           Prefix Cmd  Term
```

**Without Prefix (Version Only):**
```
Transmitted: 'VR\r\r\n'
            └┬┘└─┬──┘
           Cmd  Term
```

Where:
- **Prefix:** `1;1;` (Station 1, Command 1)
- **Term:** `\r\r\n` (CR + CR + LF)

---

## Connection & System Control

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `servo_on()` | `1;1;SRVON\r\r\n` | ✅ YES |
| `servo_off()` | `1;1;SRVOFF\r\r\n` | ✅ YES |
| `control_on()` | `1;1;CNTLON\r\r\n` | ✅ YES |
| `reset_alarm()` | `1;1;RSTALRM\r\r\n` | ✅ YES |
| `initialize()` | Multiple commands | ✅ YES (all) |
| `shutdown()` | `1;1;SRVOFF\r\r\n` | ✅ YES |

**Examples:**
```python
robot.servo_on()      # Sends: '1;1;SRVON\r\r\n'
robot.reset_alarm()   # Sends: '1;1;RSTALRM\r\r\n'
```

---

## Joint Motion Commands

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `move_joint(j1=10, j2=20, j3=30)` | `1;1;MJ 10.00,20.00,30.00,,,\r\r\n` | ✅ YES |
| `move_joint(j1=10, j5=-5)` | `1;1;MJ 10.00,,,,-5.00,\r\r\n` | ✅ YES |
| `move_joint(j1=10)` | `1;1;MJ 10.00,,,,,\r\r\n` | ✅ YES |

**Examples:**
```python
robot.move_joint(j1=10.0, j2=20.0)  # Sends: '1;1;MJ 10.00,20.00,,,,\r\r\n'
robot.move_joint(j3=-15.5)          # Sends: '1;1;MJ ,,15.50,,,\r\r\n'
```

**Notes:**
- Empty positions are represented by commas with no value
- All 6 joint positions are always included in the command

---

## Position-Based Motion

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `move_to_position(10)` | `1;1;MO 10\r\r\n` | ✅ YES |
| `move_to_position(10, 'O')` | `1;1;MO 10,O\r\r\n` | ✅ YES |
| `move_to_position(10, 'C')` | `1;1;MO 10,C\r\r\n` | ✅ YES |
| `move_straight(20)` | `1;1;MS 20\r\r\n` | ✅ YES |
| `move_straight(20, 'O')` | `1;1;MS 20,O\r\r\n` | ✅ YES |

**Examples:**
```python
robot.move_to_position(10)      # Sends: '1;1;MO 10\r\r\n'
robot.move_to_position(10, 'O') # Sends: '1;1;MO 10,O\r\r\n'
robot.move_straight(50)         # Sends: '1;1;MS 50\r\r\n'
```

**Posture Flags:**
- `'O'` = Open posture
- `'C'` = Close posture

---

## Cartesian Motion

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `move_position(100, 200, 300)` | `1;1;MP 100.00,200.00,300.00\r\r\n` | ✅ YES |
| `move_position(100, 200, 300, 0, 0, 90)` | `1;1;MP 100.00,200.00,300.00,0.00,0.00,90.00\r\r\n` | ✅ YES |

**Examples:**
```python
# XYZ only
robot.move_position(100, 200, 300)
# Sends: '1;1;MP 100.00,200.00,300.00\r\r\n'

# XYZ + ABC orientation
robot.move_position(100, 200, 300, 0, 0, 90)
# Sends: '1;1;MP 100.00,200.00,300.00,0.00,0.00,90.00\r\r\n'
```

**Units:**
- X, Y, Z: millimeters
- A, B, C: degrees

---

## Position Teaching & Origin

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `here(10)` | `1;1;HE 10\r\r\n` | ✅ YES |
| `here(999)` | `1;1;HE 999\r\r\n` | ✅ YES |
| `define_origin()` | `1;1;HO\r\r\n` | ✅ YES |
| `define_origin(0)` | `1;1;HO 0\r\r\n` | ✅ YES |
| `define_origin(1)` | `1;1;HO 1\r\r\n` | ✅ YES |
| `nest()` | `1;1;NT\r\r\n` | ✅ YES |
| `origin_move()` | `1;1;OG\r\r\n` | ✅ YES |

**Examples:**
```python
robot.here(10)          # Sends: '1;1;HE 10\r\r\n'      - Save current position as P10
robot.define_origin()   # Sends: '1;1;HO\r\r\n'        - Define current as origin
robot.define_origin(1)  # Sends: '1;1;HO 1\r\r\n'      - Define jig origin
robot.nest()            # Sends: '1;1;NT\r\r\n'        - Move to user origin
```

**Origin Types:**
- `0` = Mechanical origin
- `1` = Jig origin
- `2` = User origin

---

## Speed & Timing Control

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `set_speed(50)` | `1;1;SP 50\r\r\n` | ✅ YES |
| `set_speed(100)` | `1;1;SP 100\r\r\n` | ✅ YES |
| `set_override(75)` | `1;1;OVR 75\r\r\n` | ✅ YES |
| `timer(2.5)` | `1;1;TI 2.50\r\r\n` | ✅ YES |
| `define_speed("params")` | `1;1;SD params\r\r\n` | ✅ YES |

**Examples:**
```python
robot.set_speed(50)      # Sends: '1;1;SP 50\r\r\n'    - Set speed to 50%
robot.set_override(75)   # Sends: '1;1;OVR 75\r\r\n'   - Set override to 75%
robot.timer(2.5)         # Sends: '1;1;TI 2.50\r\r\n'  - Wait 2.5 seconds
```

**Speed Range:** 1-100 (percentage)

---

## Tool Control

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `set_tool_length(50.5)` | `1;1;TL 50.50\r\r\n` | ✅ YES |
| `set_tool_matrix(10, 20, 30, 0, 0, 90)` | `1;1;TLM 10.00,20.00,30.00,0.00,0.00,90.00\r\r\n` | ✅ YES |

**Examples:**
```python
robot.set_tool_length(50.5)
# Sends: '1;1;TL 50.50\r\r\n'

robot.set_tool_matrix(10, 20, 30, 0, 0, 90)
# Sends: '1;1;TLM 10.00,20.00,30.00,0.00,0.00,90.00\r\r\n'
```

**Units:**
- Tool length: millimeters
- X, Y, Z offsets: millimeters
- A, B, C angles: degrees

---

## Gripper/Hand Control

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `grip_open()` | `1;1;GO\r\r\n` | ✅ YES |
| `grip_close()` | `1;1;GC\r\r\n` | ✅ YES |
| `grip_pressure(10, 20, 30)` | `1;1;GP 10,20,30\r\r\n` | ✅ YES |

**Examples:**
```python
robot.grip_open()            # Sends: '1;1;GO\r\r\n'
robot.grip_close()           # Sends: '1;1;GC\r\r\n'
robot.grip_pressure(10,20,30)# Sends: '1;1;GP 10,20,30\r\r\n'
```

---

## Program Control

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `goto(100)` | `1;1;GT 100\r\r\n` | ✅ YES |
| `gosub(200)` | `1;1;GS 200\r\r\n` | ✅ YES |
| `return_sub()` | `1;1;RT\r\r\n` | ✅ YES |
| `end()` | `1;1;ED\r\r\n` | ✅ YES |
| `halt()` | `1;1;HLT\r\r\n` | ✅ YES |

**Examples:**
```python
robot.goto(100)       # Sends: '1;1;GT 100\r\r\n'   - Jump to line 100
robot.gosub(200)      # Sends: '1;1;GS 200\r\r\n'   - Call subroutine at line 200
robot.return_sub()    # Sends: '1;1;RT\r\r\n'       - Return from subroutine
robot.halt()          # Sends: '1;1;HLT\r\r\n'      - Stop program
```

---

## Conditional Branching

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `if_equal(5, 100)` | `1;1;EQ 5,100\r\r\n` | ✅ YES |
| `if_not_equal(5, 100)` | `1;1;NE 5,100\r\r\n` | ✅ YES |
| `if_larger(5, 100)` | `1;1;LG 5,100\r\r\n` | ✅ YES |
| `if_smaller(5, 100)` | `1;1;SM 5,100\r\r\n` | ✅ YES |

**Examples:**
```python
robot.if_equal(5, 100)      # Sends: '1;1;EQ 5,100\r\r\n'  - If reg == 5, goto 100
robot.if_not_equal(5, 100)  # Sends: '1;1;NE 5,100\r\r\n'  - If reg != 5, goto 100
robot.if_larger(10, 200)    # Sends: '1;1;LG 10,200\r\r\n' - If reg > 10, goto 200
robot.if_smaller(3, 50)     # Sends: '1;1;SM 3,50\r\r\n'   - If reg < 3, goto 50
```

---

## I/O Control

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `output_bit(1, True)` | `1;1;OB +1\r\r\n` | ✅ YES |
| `output_bit(2, False)` | `1;1;OB -2\r\r\n` | ✅ YES |
| `input_direct(3)` | `1;1;ID 3\r\r\n` | ✅ YES |

**Examples:**
```python
robot.output_bit(1, True)   # Sends: '1;1;OB +1\r\r\n'  - Turn ON output bit 1
robot.output_bit(2, False)  # Sends: '1;1;OB -2\r\r\n'  - Turn OFF output bit 2
robot.input_direct(3)       # Sends: '1;1;ID 3\r\r\n'   - Read input bit 3
```

**Note:** 
- `+` prefix = Turn ON
- `-` prefix = Turn OFF

---

## Status Queries

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `get_position()` | `1;1;JPOSF\r\r\n` | ✅ YES |
| `where()` | `1;1;WH\r\r\n` | ✅ YES |
| `position_read(10)` | `1;1;PR 10\r\r\n` | ✅ YES |
| `get_error()` | `1;1;ER\r\r\n` | ✅ YES |
| `get_version()` | `VR\r\r\n` | ❌ **NO** |

**Examples:**
```python
robot.get_position()     # Sends: '1;1;JPOSF\r\r\n'  - Get joint positions
robot.where()            # Sends: '1;1;WH\r\r\n'     - Get Cartesian position
robot.position_read(10)  # Sends: '1;1;PR 10\r\r\n' - Read saved position 10
robot.get_error()        # Sends: '1;1;ER\r\r\n'    - Get current error
robot.get_version()      # Sends: 'VR\r\r\n'        - Get version (NO PREFIX!)
```

**⚠️ IMPORTANT:** Only `get_version()` does NOT use the `1;1;` prefix!

---

## Custom Commands

| Function | Raw Command Sent | Use Prefix? |
|----------|------------------|-------------|
| `send_command("CUSTOM")` | `1;1;CUSTOM\r\r\n` | ✅ YES (default) |
| `send_command("CUSTOM", use_prefix=False)` | `CUSTOM\r\r\n` | ❌ NO |
| `send_command("VR", use_prefix=False)` | `VR\r\r\n` | ❌ NO |

**Examples:**
```python
# With prefix (default)
robot.send_command("SRVON")
# Sends: '1;1;SRVON\r\r\n'

# Without prefix (explicit)
robot.send_command("VR", use_prefix=False)
# Sends: 'VR\r\r\n'
```

---

## Quick Reference: Prefix Usage

### ✅ Commands WITH `1;1;` Prefix (ALL except VR)
- All motion commands (MJ, MO, MS, MP)
- All servo/control commands (SRVON, SRVOFF, CNTLON, RSTALRM)
- All position teaching (HE, HO, NT, OG)
- All speed control (SP, OVR, TI)
- All gripper commands (GO, GC, GP)
- All program control (GT, GS, RT, ED, HLT)
- All conditionals (EQ, NE, LG, SM)
- All I/O (OB, ID)
- Status queries: JPOSF, WH, PR, ER

### ❌ Commands WITHOUT Prefix
- **VR** (Version) - ONLY THIS ONE!

---

## Debugging Commands

To see exactly what's being sent, enable **Verbose Mode** in the GUI:
1. Check the "Verbose (Show Raw Commands)" checkbox
2. Execute any command
3. See the TX/RX logs:
   ```
   [VERBOSE] TX → '1;1;SRVON\r\r\n'
   [VERBOSE] RX ← 'QoK'
   ```

This shows:
- **TX →** What was transmitted TO the robot
- **RX ←** What was received FROM the robot

---

## Response Format

All commands return one of three response types:

| Response | Meaning | Example |
|----------|---------|---------|
| `QoK` | Success | Command executed successfully |
| `QeRXXXX` | Error | `QeR6020` = Error code 6020 |
| `Q...` | Data | `Q+0000000.00,...` = Position data |

---

## Summary Table

| Category | Total Commands | With Prefix | Without Prefix |
|----------|----------------|-------------|----------------|
| Connection/System | 6 | 6 | 0 |
| Motion | 5 | 5 | 0 |
| Position Teaching | 4 | 4 | 0 |
| Speed/Timing | 4 | 4 | 0 |
| Tool Control | 2 | 2 | 0 |
| Gripper | 3 | 3 | 0 |
| Program Control | 5 | 5 | 0 |
| Conditionals | 4 | 4 | 0 |
| I/O | 2 | 2 | 0 |
| Status Queries | 5 | 4 | 1 (VR) |
| **TOTAL** | **40** | **39** | **1** |

**Only 1 out of 40 commands does NOT use the prefix: `VR` (get_version)**

---

*Generated: 2026-02-15*  
*Library: rv2aj_commands.py*
