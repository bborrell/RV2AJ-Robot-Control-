# RV-2AJ Command Types: Serial vs MoveMaster

**CRITICAL UNDERSTANDING:** The RV-2AJ robot uses two distinct command sets with different purposes and interfaces.

---

## Overview

### 🔌 Serial Commands (RS-232 Control)
**Purpose:** Real-time robot control from external computer  
**Interface:** RS-232 serial port  
**Usage:** Direct control, monitoring, jogging  
**Prefix:** `1;1;` (for most commands)

### 📝 MoveMaster Commands (Program Building)
**Purpose:** Creating stored programs on the robot controller  
**Interface:** Teaching pendant or program transfer  
**Usage:** Automated sequences, production programs  
**Execution:** Runs on the controller itself

---

## Serial Commands (RS-232 Interface)

### What They Do
- Control robot in **real-time** from a computer
- Query robot status and position
- Enable/disable servos and controller
- **Cannot** branch, loop, or create programs
- Execute **immediately** when sent

### Available Serial Commands

#### System Control
| Command | Function | Sent As |
|---------|----------|---------|
| `SRVON` | Turn on servos | `1;1;SRVON\r\r\n` |
| `SRVOFF` | Turn off servos | `1;1;SRVOFF\r\r\n` |
| `CNTLON` | Enable controller | `1;1;CNTLON\r\r\n` |
| `RSTALRM` | Reset alarm | `1;1;RSTALRM\r\r\n` |

#### Motion (Real-Time)
| Command | Function | Sent As |
|---------|----------|---------|
| `MJ j1,j2,j3,j4,j5,j6` | Move joints incrementally | `1;1;MJ 1.0,,,,,\r\r\n` |
| `MO a` | Move to stored position | `1;1;MO 10\r\r\n` |
| `MS a` | Linear move to position | `1;1;MS 10\r\r\n` |
| `MP X,Y,Z,A,B,C` | Move to coordinates | `1;1;MP 100,200,300\r\r\n` |

#### Teaching & Position
| Command | Function | Sent As |
|---------|----------|---------|
| `HE a` | Save current position | `1;1;HE 10\r\r\n` |
| `HO [a]` | Define origin | `1;1;HO\r\r\n` |

#### Gripper
| Command | Function | Sent As |
|---------|----------|---------|
| `GC` | Close gripper | `1;1;GC\r\r\n` |
| `GO` | Open gripper | `1;1;GO\r\r\n` |

#### Status Queries
| Command | Function | Sent As |
|---------|----------|---------|
| `JPOSF` | Get joint positions | `1;1;JPOSF\r\r\n` |
| `WH` | Get Cartesian position | `1;1;WH\r\r\n` |
| `ER` | Get error code | `1;1;ER\r\r\n` |
| `VR` | Get version | `VR\r\r\n` (NO PREFIX!) |
| `PR a` | Read position data | `1;1;PR 10\r\r\n` |

#### I/O Control
| Command | Function | Sent As |
|---------|----------|---------|
| `OB +a` | Turn ON output bit | `1;1;OB +1\r\r\n` |
| `OB -a` | Turn OFF output bit | `1;1;OB -1\r\r\n` |
| `ID a` | Read input bit | `1;1;ID 1\r\r\n` |

### Characteristics
- ✅ Real-time execution
- ✅ Immediate response
- ✅ Position feedback
- ✅ Jogging capability
- ❌ No branching (GT, GS, RT)
- ❌ No conditionals (EQ, NE, LG, SM)
- ❌ No program flow control
- ❌ Cannot store programs

### Use Cases
- **Manual control** via GUI or CLI
- **Jogging** individual axes
- **Testing** and setup
- **Position teaching** (saving positions)
- **Real-time monitoring**
- **Integration** with external systems

---

## MoveMaster Commands (Program Building)

### What They Do
- Create **programs** stored on the robot controller
- Support **branching** and **loops**
- Run **autonomously** without computer connection
- Enable **production automation**

### Program-Only Commands

#### Program Flow
| Command | Function | Example |
|---------|----------|---------|
| `GT a` | Jump to line | `GT 100` |
| `GS a` | Call subroutine | `GS 200` |
| `RT` | Return from subroutine | `RT` |
| `ED` | End program | `ED` |
| `HLT` | Halt program | `HLT` |

#### Conditionals
| Command | Function | Example |
|---------|----------|---------|
| `EQ a,b` | If equal, goto line | `EQ 5,100` |
| `NE a,b` | If not equal, goto | `NE 5,100` |
| `LG a,b` | If larger, goto | `LG 10,200` |
| `SM a,b` | If smaller, goto | `SM 3,50` |

#### Advanced Features (Program Mode)
- Variable manipulation
- Counters and timers in programs
- Complex motion sequences
- Synchronized I/O
- Error handling routines

### Characteristics
- ✅ Full programming capability
- ✅ Branching and loops
- ✅ Conditional logic
- ✅ Subroutines
- ✅ Autonomous execution
- ❌ Requires program transfer
- ❌ Not for real-time jogging
- ❌ No immediate position queries

### Use Cases
- **Production sequences** (pick and place)
- **Automated cycles** (palletizing)
- **Complex routines** with decision logic
- **Teaching pendant programming**
- **Batch operations**

---

## Key Differences Summary

| Feature | Serial Commands | MoveMaster Commands |
|---------|----------------|---------------------|
| **Interface** | RS-232 | Teaching pendant / Program transfer |
| **Execution** | Immediate | Stored program |
| **Control Source** | External computer | Robot controller |
| **Branching** | ❌ No | ✅ Yes |
| **Conditionals** | ❌ No | ✅ Yes |
| **Subroutines** | ❌ No | ✅ Yes |
| **Real-time Jog** | ✅ Yes | ❌ No |
| **Position Query** | ✅ Yes | Limited |
| **Integration** | ✅ Easy | ❌ Complex |
| **Autonomy** | ❌ Requires PC | ✅ Standalone |

---

## Current Implementation Status

### ✅ Implemented (Serial Commands)
- GUI with JOG panel for real-time control
- Arrow key jogging
- Position queries (JPOSF, WH)
- Servo control (SRVON/SRVOFF)
- Error checking (ER)
- Gripper control (GO/GC)
- I/O control (OB, ID)
- Position teaching (HE)

### 🔜 Future (MoveMaster Programs)
- Program editor interface
- Program upload/download
- Branching and conditional logic
- Subroutine management
- Program execution control
- Variable handling

---

## GUI Tab Organization

### Current Tabs (Serial Control)
1. **Connection** - Connect, initialize, servo control
2. **⚡ JOG** - Real-time axis jogging with arrow keys
3. **Motion** - Position-based moves (MO, MS, MP)
4. **Positions** - Position teaching and recall
5. **Gripper** - Gripper control
6. **Speed & Control** - Speed settings
7. **I/O** - Digital I/O control
8. **Status** - Position queries, error checking

### Future Tabs (Program Building)
- **Program Editor** - Create MoveMaster programs
- **Program Manager** - Upload/download/execute programs
- **Variables** - Manage program variables

---

## Example: Serial Control Workflow

```python
# Connect and initialize
robot.connect()
robot.initialize()  # RSTALRM, CNTLON, SRVON

# Real-time jogging
robot.move_joint(j1=1.0)   # Jog J1 +1 degree
robot.move_joint(j2=-0.5)  # Jog J2 -0.5 degree

# Save position
robot.here(10)  # Save current as P10

# Move to position
robot.move_to_position(10)  # Move to P10

# Query status
position = robot.get_position()  # Get current position
error = robot.get_error()        # Check for errors
```

---

## Example: MoveMaster Program (Future)

```
Line 10: MO 1         ; Move to position 1
Line 20: GO           ; Open gripper
Line 30: MS 10        ; Linear move to position 10
Line 40: GC           ; Close gripper
Line 50: TI 0.5       ; Wait 0.5 seconds
Line 60: MS 20        ; Linear move to position 20
Line 70: GO           ; Open gripper
Line 80: GT 10        ; Loop back to line 10
Line 90: ED           ; End program
```

---

## Important Notes

### When Using Serial Commands:
1. **Prefix required** for almost all commands (`1;1;`)
2. **Exception:** VR command has NO prefix
3. **Terminator:** All commands end with `\r\r\n`
4. **Responses:** QoK (success), QeRXXXX (error), Q (data)
5. **Real-time only:** Cannot store sequences

### When Building Programs (Future):
1. Programs stored in controller memory
2. Line numbers required
3. Can run without PC connection
4. Use teaching pendant for manual programming
5. Can be uploaded from PC

---

## References

- **Serial Commands:** See `COMMAND_REFERENCE.md`
- **moveMaster Commands:** See `RV2AJ_command_moveMaster.json`
- **Error Codes:** See `RV2AJ_ErrorCodes.json`
- **Protocol:** See `Mitsubishi RS232 Protocol.pdf`

---

*Generated: 2026-02-15*  
*Critical discovery: Two distinct command sets!*
