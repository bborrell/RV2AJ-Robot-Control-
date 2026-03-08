"""MELFA-BASIC IV command builders for the Mitsubishi RV-2AJ robot.

Commands are compatible with the CR1 / CR2 / CR2B robot controllers and
follow the MELFA-BASIC IV language specification.  Each helper returns an
ASCII string that can be sent directly to the controller over RS-232 or
Ethernet.
"""

from __future__ import annotations

from typing import Optional

from .positions import CartesianPosition, JointPosition


# ---------------------------------------------------------------------------
# Low-level formatting helpers
# ---------------------------------------------------------------------------

def _fmt(value: float) -> str:
    """Format a float for inclusion in a MELFA-BASIC command."""
    return f"{value:.3f}"


def _joint_str(pos: JointPosition) -> str:
    """Encode a JointPosition as MELFA-BASIC joint data string.

    Format: (J1, J2, J3, J4, J5, J6)
    """
    angles = [_fmt(v) for v in pos.as_list()]
    return f"({', '.join(angles)})"


def _cartesian_str(pos: CartesianPosition) -> str:
    """Encode a CartesianPosition as MELFA-BASIC position data string.

    Format: (X, Y, Z, Rx, Ry, Rz)(FL1, FL2, FL3)
    """
    coords = f"({_fmt(pos.x)}, {_fmt(pos.y)}, {_fmt(pos.z)}, {_fmt(pos.rx)}, {_fmt(pos.ry)}, {_fmt(pos.rz)})"
    return f"{coords}({pos.configuration})"


# ---------------------------------------------------------------------------
# Command builders
# ---------------------------------------------------------------------------

def servo_on() -> str:
    """Enable the servo motors.

    Returns:
        MELFA-BASIC command string ``SERVO ON``.
    """
    return "SERVO ON"


def servo_off() -> str:
    """Disable the servo motors.

    Returns:
        MELFA-BASIC command string ``SERVO OFF``.
    """
    return "SERVO OFF"


def move_joint(position: JointPosition, interpolation: str = "JOINT") -> str:
    """Move to a joint-space position.

    Args:
        position: Target joint angles.
        interpolation: Motion type – ``"JOINT"`` (joint interpolation, default)
            or ``"LINEAR"`` (Cartesian straight-line in joint space).

    Returns:
        MELFA-BASIC ``MOV`` command string.
    """
    return f"MOV {_joint_str(position)}"


def move_cartesian(position: CartesianPosition, linear: bool = False) -> str:
    """Move to a Cartesian position.

    Args:
        position: Target Cartesian coordinates.
        linear: If ``True`` use straight-line (``MVS``) interpolation;
            otherwise use point-to-point (``MOV``) interpolation.

    Returns:
        MELFA-BASIC ``MOV`` or ``MVS`` command string.
    """
    cmd = "MVS" if linear else "MOV"
    return f"{cmd} {_cartesian_str(position)}"


def set_speed(override: int) -> str:
    """Set the speed override percentage.

    Args:
        override: Speed override value, 1–100 (%).

    Returns:
        MELFA-BASIC ``OVRD`` command string.

    Raises:
        ValueError: If *override* is outside the 1–100 range.
    """
    if not 1 <= override <= 100:
        raise ValueError(f"Speed override must be between 1 and 100, got {override}")
    return f"OVRD {override}"


def hand_open(hand: int = 1) -> str:
    """Open the robot hand (gripper).

    Args:
        hand: Hand number (1 or 2).  Defaults to ``1``.

    Returns:
        MELFA-BASIC ``HOPEN`` command string.
    """
    return f"HOPEN {hand}"


def hand_close(hand: int = 1) -> str:
    """Close the robot hand (gripper).

    Args:
        hand: Hand number (1 or 2).  Defaults to ``1``.

    Returns:
        MELFA-BASIC ``HCLOSE`` command string.
    """
    return f"HCLOSE {hand}"


def go_home() -> str:
    """Move to the robot home position.

    Returns:
        MELFA-BASIC ``HOME`` command string.
    """
    return "HOME"


def get_current_position() -> str:
    """Request the current Cartesian position from the controller.

    Returns:
        MELFA-BASIC variable read command for the current position
        variable ``P_CURR``.
    """
    return "P_CURR"


def get_current_joint() -> str:
    """Request the current joint position from the controller.

    Returns:
        MELFA-BASIC variable read command for the current joint variable
        ``J_CURR``.
    """
    return "J_CURR"


def reset_alarm() -> str:
    """Reset any active alarms on the controller.

    Returns:
        MELFA-BASIC ``RELALM`` command string.
    """
    return "RELALM"


def stop() -> str:
    """Immediately stop all motion.

    Returns:
        MELFA-BASIC ``STOP`` command string.
    """
    return "STOP"


def set_tool(tool_number: int) -> str:
    """Select the active tool definition.

    Args:
        tool_number: Tool number (1–16).

    Returns:
        MELFA-BASIC ``TOOL`` command string.

    Raises:
        ValueError: If *tool_number* is outside 1–16.
    """
    if not 1 <= tool_number <= 16:
        raise ValueError(f"Tool number must be between 1 and 16, got {tool_number}")
    return f"TOOL {tool_number}"


def wait(seconds: float) -> str:
    """Pause execution for the given number of seconds.

    Args:
        seconds: Duration to wait (must be positive).

    Returns:
        MELFA-BASIC ``DLY`` command string.

    Raises:
        ValueError: If *seconds* is not positive.
    """
    if seconds <= 0:
        raise ValueError(f"Wait duration must be positive, got {seconds}")
    return f"DLY {seconds:.3f}"
