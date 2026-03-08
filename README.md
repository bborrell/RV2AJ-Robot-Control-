# RV2AJ Robot Control

A Python application for controlling the **Mitsubishi RV-2AJ** 6-axis robot
arm via its CR1 / CR2 controller.  It exposes a high-level Python API as well
as a ready-to-use command-line interface (CLI).

---

## Features

* **Serial (RS-232) and Ethernet (TCP)** communication back-ends
* **MELFA-BASIC IV** command generation (servo, motion, gripper, tool,
  alarm reset, …)
* **Joint-limit safety checks** using the RV-2AJ hardware specifications
* Context-manager support (`with RobotController(…):`)
* Fully unit-tested with mocked hardware (no physical robot required to run
  the tests)

---

## Requirements

| Dependency | Version |
|------------|---------|
| Python     | ≥ 3.8   |
| pyserial   | ≥ 3.5   |

Install runtime dependencies:

```bash
pip install -r requirements.txt
```

Install development/test dependencies:

```bash
pip install -r requirements-dev.txt
```

---

## Hardware setup

### Serial (RS-232) – CR1 / CR2 controller

Connect a null-modem RS-232 cable between the PC's COM port and the robot
controller's **SIO** port.  Default settings (match the controller's DIP
switch):

| Parameter | Value |
|-----------|-------|
| Baud rate | 9600  |
| Data bits | 8     |
| Parity    | None  |
| Stop bits | 1     |
| Flow ctrl | None  |

### Ethernet – CR2B / CR750 / CR800 controller

Install the optional Ethernet board and configure the controller's IP address.
The default TCP port is **10001**.

---

## Command-line usage

```
python main.py [--serial PORT | --host HOST] [options] COMMAND
```

### Global options

| Flag | Description |
|------|-------------|
| `--serial PORT` | Connect via RS-232 (e.g. `/dev/ttyUSB0` or `COM3`) |
| `--host HOST` | Connect via TCP/IP |
| `--port N` | TCP port (default: 10001) |
| `--baud N` | Baud rate for serial (default: 9600) |
| `--timeout S` | Communication timeout in seconds (default: 5) |
| `--speed N` | Speed override % before motion (default: 10) |
| `--no-servo` | Skip automatic servo-on before motion commands |
| `-v` | Verbose logging |

### Commands

| Command | Description |
|---------|-------------|
| `servo-on` | Enable servo motors |
| `servo-off` | Disable servo motors |
| `home` | Move to home position (all joints 0°) |
| `stop` | Immediately stop all motion |
| `reset-alarm` | Reset active controller alarms |
| `get-pos` | Print current Cartesian position |
| `get-joint` | Print current joint position |
| `hand-open [--hand N]` | Open gripper (N=1 or 2) |
| `hand-close [--hand N]` | Close gripper |
| `move-joint` | Move to a joint-space position |
| `move-cartesian` | Move to a Cartesian position |

### Examples

```bash
# Enable servo via serial
python main.py --serial /dev/ttyUSB0 servo-on

# Move to a joint position at 30 % speed
python main.py --serial /dev/ttyUSB0 --speed 30 move-joint \
    --j1 45 --j2 -30 --j3 90

# Move to a Cartesian position (straight-line) via Ethernet
python main.py --host 192.168.0.10 move-cartesian \
    --x 300 --y 0 --z 400 --rx 0 --ry 90 --linear

# Open/close the gripper
python main.py --serial COM3 hand-open
python main.py --serial COM3 hand-close

# Go to home position
python main.py --serial COM3 home

# Reset alarms
python main.py --serial COM3 reset-alarm
```

---

## Python API

```python
from robot_control.communication import SerialCommunication
from robot_control.controller import RobotController
from robot_control.positions import JointPosition, CartesianPosition

# --- Serial connection ---
comm = SerialCommunication(port="/dev/ttyUSB0", baud_rate=9600)
robot = RobotController(comm)

with robot:                              # auto-connects, disconnects & servo-off on exit
    robot.servo_on()
    robot.set_speed(30)                  # 30 % of maximum speed

    # Joint-space motion
    robot.move_joint(JointPosition(j1=45.0, j2=-30.0, j3=90.0))

    # Cartesian straight-line motion
    robot.move_cartesian(
        CartesianPosition(x=300, y=0, z=400, rx=0, ry=90, rz=0),
        linear=True,
    )

    robot.hand_open()                    # open gripper
    robot.hand_close()                   # close gripper
    robot.go_home()                      # return to home

# --- Ethernet connection ---
from robot_control.communication import EthernetCommunication

comm = EthernetCommunication(host="192.168.0.10", port=10001)
robot = RobotController(comm)
# … same API as above
```

### Position data classes

```python
from robot_control.positions import JointPosition, CartesianPosition

# Joint angles (degrees)
jp = JointPosition(j1=0, j2=0, j3=0, j4=0, j5=0, j6=0)

# Cartesian coordinates (mm + degrees)
cp = CartesianPosition(x=300, y=0, z=400, rx=0, ry=90, rz=0)
```

### Exceptions

| Exception | When raised |
|-----------|-------------|
| `RobotError` | Base class for all robot errors |
| `CommunicationError` | I/O failure on the transport layer |
| `ConnectionError` | Cannot open port / socket |
| `TimeoutError` | No response within the timeout window |
| `CommandError` | Controller returns an ERROR response |
| `SafetyError` | Joint angle exceeds hardware limit |
| `ServoError` | Servo operation fails |
| `PositionError` | Unreachable / invalid position |

---

## Running the tests

```bash
pytest tests/ -v
```

Run with coverage report:

```bash
pytest tests/ --cov=robot_control --cov-report=term-missing
```

---

## Project structure

```
RV2AJ-Robot-Control-/
├── main.py                     # CLI entry point
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Test dependencies
├── robot_control/
│   ├── __init__.py             # Public API
│   ├── commands.py             # MELFA-BASIC IV command builders
│   ├── communication.py        # Serial / Ethernet transport
│   ├── controller.py           # High-level RobotController class
│   ├── exceptions.py           # Custom exception hierarchy
│   └── positions.py            # JointPosition / CartesianPosition data classes
└── tests/
    ├── test_commands.py
    ├── test_communication.py
    ├── test_controller.py
    └── test_positions.py
```

---

## Joint limits (RV-2AJ hardware specification)

| Axis | Min (°) | Max (°) |
|------|---------|---------|
| J1   | −240    | +240    |
| J2   | −115    | +115    |
| J3   | −70     | +165    |
| J4   | −200    | +200    |
| J5   | −115    | +115    |
| J6   | −360    | +360    |

Angles outside these ranges are rejected by `RobotController` before any
command is sent to the hardware.

---

## License

This project is provided as-is for educational and research purposes.