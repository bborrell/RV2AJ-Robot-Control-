"""robot_control – Mitsubishi RV-2AJ robot control library."""

from .commands import (
    go_home,
    hand_close,
    hand_open,
    move_cartesian,
    move_joint,
    reset_alarm,
    servo_off,
    servo_on,
    set_speed,
    set_tool,
    stop,
    wait,
)
from .communication import EthernetCommunication, SerialCommunication
from .controller import RobotController
from .exceptions import (
    CommandError,
    CommunicationError,
    ConnectionError,
    PositionError,
    RobotError,
    SafetyError,
    ServoError,
    TimeoutError,
)
from .positions import CartesianPosition, JointPosition

__all__ = [
    # High-level controller
    "RobotController",
    # Communication back-ends
    "SerialCommunication",
    "EthernetCommunication",
    # Position types
    "JointPosition",
    "CartesianPosition",
    # Command builders
    "servo_on",
    "servo_off",
    "move_joint",
    "move_cartesian",
    "go_home",
    "hand_open",
    "hand_close",
    "set_speed",
    "set_tool",
    "stop",
    "wait",
    "reset_alarm",
    # Exceptions
    "RobotError",
    "CommunicationError",
    "ConnectionError",
    "TimeoutError",
    "CommandError",
    "ServoError",
    "PositionError",
    "SafetyError",
]
