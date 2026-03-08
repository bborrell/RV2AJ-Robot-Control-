"""Custom exceptions for the RV-2AJ robot control application."""


class RobotError(Exception):
    """Base exception for all robot-related errors."""


class CommunicationError(RobotError):
    """Raised when communication with the robot controller fails."""


class ConnectionError(CommunicationError):
    """Raised when a connection to the robot controller cannot be established."""


class TimeoutError(CommunicationError):
    """Raised when a command times out waiting for a response."""


class CommandError(RobotError):
    """Raised when the robot controller returns an error response to a command."""

    def __init__(self, command: str, error_code: str, message: str = "") -> None:
        self.command = command
        self.error_code = error_code
        super().__init__(
            f"Command '{command}' failed with error code {error_code}"
            + (f": {message}" if message else "")
        )


class ServoError(RobotError):
    """Raised when servo-related operations fail."""


class PositionError(RobotError):
    """Raised when an invalid or unreachable position is specified."""


class SafetyError(RobotError):
    """Raised when a requested operation would violate safety limits."""
