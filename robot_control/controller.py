"""High-level controller for the Mitsubishi RV-2AJ robot arm.

:class:`RobotController` wraps a :class:`~robot_control.communication.CommunicationBase`
transport and exposes a Pythonic API for common robot operations:

* Servo management
* Joint / Cartesian motion
* Gripper (hand) control
* Safety limits enforcement
* Alarm reset

Example usage::

    from robot_control.communication import SerialCommunication
    from robot_control.controller import RobotController
    from robot_control.positions import JointPosition

    comm = SerialCommunication(port="/dev/ttyUSB0")
    robot = RobotController(comm)

    with robot:
        robot.servo_on()
        robot.set_speed(30)
        robot.move_joint(JointPosition(j1=45.0, j2=-30.0))
        robot.hand_open()
"""

from __future__ import annotations

import logging
from typing import Optional

from . import commands
from .communication import CommunicationBase
from .exceptions import CommandError, PositionError, SafetyError, ServoError
from .positions import (
    JOINT_LIMITS,
    CartesianPosition,
    JointPosition,
)

logger = logging.getLogger(__name__)

# Prefix returned by the CR1/CR2 controller on a successful response
_OK_PREFIX = "OK"
# Prefix returned on errors
_ERROR_PREFIX = "ERROR"
# Maximum allowed speed override (%)
_MAX_SPEED = 100
_MIN_SPEED = 1


def _check_response(response: str, command: str) -> str:
    """Validate a controller response and raise :exc:`CommandError` on failure.

    Args:
        response: Raw response string from the controller.
        command: The command that was sent (used for error messages).

    Returns:
        The response string on success.

    Raises:
        CommandError: If the response indicates an error.
    """
    stripped = response.strip()
    if stripped.upper().startswith(_ERROR_PREFIX):
        parts = stripped.split()
        error_code = parts[1] if len(parts) > 1 else "UNKNOWN"
        message = " ".join(parts[2:]) if len(parts) > 2 else ""
        raise CommandError(command=command, error_code=error_code, message=message)
    return stripped


def _validate_joint_limits(position: JointPosition) -> None:
    """Check that *position* is within the hardware joint limits.

    Args:
        position: Joint angles to validate.

    Raises:
        SafetyError: If any joint angle exceeds the allowed range.
    """
    angles = position.as_list()
    for limit, angle in zip(JOINT_LIMITS, angles):
        if not limit["min"] <= angle <= limit["max"]:
            raise SafetyError(
                f"Joint {limit['axis']} angle {angle:.3f}° is outside the "
                f"allowed range [{limit['min']:.1f}°, {limit['max']:.1f}°]."
            )


class RobotController:
    """High-level interface to the Mitsubishi RV-2AJ robot controller.

    Args:
        communication: A connected (or ready-to-connect) communication
            back-end (:class:`~robot_control.communication.SerialCommunication`
            or :class:`~robot_control.communication.EthernetCommunication`).
        validate_limits: If ``True`` (default), joint angles are checked
            against the hardware limits before sending motion commands.
    """

    def __init__(
        self,
        communication: CommunicationBase,
        validate_limits: bool = True,
    ) -> None:
        self._comm = communication
        self._validate_limits = validate_limits
        self._servo_enabled: bool = False
        self._speed: int = 10  # default speed override on startup

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "RobotController":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if self._servo_enabled:
                self.servo_off()
        finally:
            self.disconnect()
        return False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the communication channel to the controller."""
        logger.info("Connecting to robot controller …")
        self._comm.connect()
        logger.info("Connected.")

    def disconnect(self) -> None:
        """Close the communication channel."""
        logger.info("Disconnecting from robot controller …")
        self._comm.disconnect()
        logger.info("Disconnected.")

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the communication channel is open."""
        return self._comm.is_connected

    # ------------------------------------------------------------------
    # Servo control
    # ------------------------------------------------------------------

    def servo_on(self) -> None:
        """Enable the servo motors.

        Raises:
            ServoError: If the servo cannot be enabled.
        """
        logger.info("Enabling servo motors …")
        cmd = commands.servo_on()
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)
        self._servo_enabled = True
        logger.info("Servo ON.")

    def servo_off(self) -> None:
        """Disable the servo motors.

        Raises:
            ServoError: If the servo cannot be disabled.
        """
        logger.info("Disabling servo motors …")
        cmd = commands.servo_off()
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)
        self._servo_enabled = False
        logger.info("Servo OFF.")

    @property
    def servo_enabled(self) -> bool:
        """Return ``True`` if the servo motors are currently enabled."""
        return self._servo_enabled

    # ------------------------------------------------------------------
    # Speed control
    # ------------------------------------------------------------------

    def set_speed(self, override: int) -> None:
        """Set the speed override percentage.

        Args:
            override: Speed as a percentage of maximum (1–100).

        Raises:
            ValueError: If *override* is out of range.
        """
        cmd = commands.set_speed(override)
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)
        self._speed = override
        logger.info("Speed override set to %d%%.", override)

    @property
    def current_speed(self) -> int:
        """Return the currently active speed override percentage."""
        return self._speed

    # ------------------------------------------------------------------
    # Motion commands
    # ------------------------------------------------------------------

    def move_joint(self, position: JointPosition) -> None:
        """Move the robot to a joint-space position.

        Args:
            position: Target joint angles in degrees.

        Raises:
            SafetyError: If *position* violates joint limits and
                *validate_limits* is ``True``.
        """
        if self._validate_limits:
            _validate_joint_limits(position)
        cmd = commands.move_joint(position)
        logger.info("Moving to joint position: %s", position)
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)

    def move_cartesian(self, position: CartesianPosition, linear: bool = False) -> None:
        """Move the robot to a Cartesian position.

        Args:
            position: Target Cartesian coordinates.
            linear: If ``True``, use straight-line (``MVS``) interpolation.

        Raises:
            PositionError: If the position is out of reach (reported by the
                controller).
        """
        cmd = commands.move_cartesian(position, linear=linear)
        logger.info("Moving to Cartesian position: %s", position)
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)

    def go_home(self) -> None:
        """Move the robot to its home position (all joints = 0°)."""
        logger.info("Moving to home position …")
        cmd = commands.go_home()
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)

    def stop(self) -> None:
        """Immediately stop all robot motion."""
        logger.info("Sending STOP command.")
        self._comm.send(commands.stop())

    # ------------------------------------------------------------------
    # Gripper (hand) control
    # ------------------------------------------------------------------

    def hand_open(self, hand: int = 1) -> None:
        """Open the robot gripper.

        Args:
            hand: Gripper number (1 or 2).  Defaults to ``1``.
        """
        cmd = commands.hand_open(hand)
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)
        logger.info("Hand %d opened.", hand)

    def hand_close(self, hand: int = 1) -> None:
        """Close the robot gripper.

        Args:
            hand: Gripper number (1 or 2).  Defaults to ``1``.
        """
        cmd = commands.hand_close(hand)
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)
        logger.info("Hand %d closed.", hand)

    # ------------------------------------------------------------------
    # State enquiry
    # ------------------------------------------------------------------

    def get_current_position(self) -> str:
        """Request the current Cartesian position from the controller.

        Returns:
            Raw position string as reported by the controller.
        """
        cmd = commands.get_current_position()
        response = self._comm.send_receive(cmd)
        return _check_response(response, cmd)

    def get_current_joint(self) -> str:
        """Request the current joint position from the controller.

        Returns:
            Raw joint position string as reported by the controller.
        """
        cmd = commands.get_current_joint()
        response = self._comm.send_receive(cmd)
        return _check_response(response, cmd)

    # ------------------------------------------------------------------
    # Alarm management
    # ------------------------------------------------------------------

    def reset_alarm(self) -> None:
        """Reset any active alarms on the controller."""
        logger.info("Resetting alarms …")
        cmd = commands.reset_alarm()
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)
        logger.info("Alarms reset.")

    # ------------------------------------------------------------------
    # Tool selection
    # ------------------------------------------------------------------

    def set_tool(self, tool_number: int) -> None:
        """Select the active tool definition.

        Args:
            tool_number: Tool number (1–16).
        """
        cmd = commands.set_tool(tool_number)
        response = self._comm.send_receive(cmd)
        _check_response(response, cmd)
        logger.info("Tool %d selected.", tool_number)

    def __repr__(self) -> str:
        return (
            f"RobotController(communication={self._comm!r}, "
            f"servo_enabled={self._servo_enabled}, speed={self._speed}%)"
        )
