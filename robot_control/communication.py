"""Communication layer for the Mitsubishi RV-2AJ robot controller.

Provides two transport back-ends:

* :class:`SerialCommunication` – RS-232 serial port (CR1 / CR2 controller).
* :class:`EthernetCommunication` – TCP socket (CR2B / CR750 controller with
  Ethernet option).

Both classes share the :class:`CommunicationBase` interface so that the
higher-level :class:`~robot_control.controller.RobotController` is transport-
agnostic.
"""

from __future__ import annotations

import socket
import time
from abc import ABC, abstractmethod
from typing import Optional

from .exceptions import (
    CommunicationError,
    ConnectionError,
    TimeoutError,
)

# Default terminator used by MELFA-BASIC IV over RS-232 / TCP
_TERMINATOR = "\r\n"
_ENCODING = "ascii"

# Default network settings
DEFAULT_TCP_PORT = 10001
DEFAULT_TIMEOUT = 5.0  # seconds

# Default serial settings (CR1 / CR2 hardware manual)
DEFAULT_BAUD_RATE = 9600
DEFAULT_BYTESIZE = 8
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1


class CommunicationBase(ABC):
    """Abstract base class for robot controller communication."""

    @abstractmethod
    def connect(self) -> None:
        """Open the communication channel to the controller."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the communication channel."""

    @abstractmethod
    def send(self, command: str) -> None:
        """Send a raw command string to the controller.

        Args:
            command: MELFA-BASIC IV command string (without terminator).

        Raises:
            CommunicationError: If the command cannot be sent.
        """

    @abstractmethod
    def receive(self) -> str:
        """Read a response from the controller.

        Returns:
            Response string (stripped of terminator and whitespace).

        Raises:
            CommunicationError: If reading fails.
            TimeoutError: If no response arrives within the timeout period.
        """

    def send_receive(self, command: str) -> str:
        """Send a command and return the controller's response.

        Args:
            command: MELFA-BASIC IV command string.

        Returns:
            Controller response string.
        """
        self.send(command)
        return self.receive()

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return ``True`` if the communication channel is open."""


# ---------------------------------------------------------------------------
# Serial (RS-232) back-end
# ---------------------------------------------------------------------------

class SerialCommunication(CommunicationBase):
    """RS-232 serial communication with the Mitsubishi CR1/CR2 controller.

    Args:
        port: Serial port name (e.g. ``"COM3"`` on Windows or
            ``"/dev/ttyUSB0"`` on Linux).
        baud_rate: Baud rate.  Defaults to 9600 (hardware default).
        timeout: Read timeout in seconds.  Defaults to 5.0.
        bytesize: Number of data bits.  Defaults to 8.
        parity: Parity (``"N"``, ``"E"``, or ``"O"``).  Defaults to ``"N"``.
        stopbits: Number of stop bits (1 or 2).  Defaults to 1.
    """

    def __init__(
        self,
        port: str,
        baud_rate: int = DEFAULT_BAUD_RATE,
        timeout: float = DEFAULT_TIMEOUT,
        bytesize: int = DEFAULT_BYTESIZE,
        parity: str = DEFAULT_PARITY,
        stopbits: int = DEFAULT_STOPBITS,
    ) -> None:
        self._port = port
        self._baud_rate = baud_rate
        self._timeout = timeout
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._serial = None  # pyserial Serial object, set on connect()

    # ------------------------------------------------------------------
    # CommunicationBase interface
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the serial port.

        Raises:
            ConnectionError: If pyserial is not installed or the port
                cannot be opened.
        """
        try:
            import serial  # type: ignore[import]
        except ImportError as exc:
            raise ConnectionError(
                "pyserial is not installed. Install it with: pip install pyserial"
            ) from exc

        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baud_rate,
                bytesize=self._bytesize,
                parity=self._parity,
                stopbits=self._stopbits,
                timeout=self._timeout,
            )
        except serial.SerialException as exc:
            raise ConnectionError(
                f"Failed to open serial port '{self._port}': {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Close the serial port."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def send(self, command: str) -> None:
        """Write *command* to the serial port.

        Raises:
            CommunicationError: If the port is not open or the write fails.
        """
        if not self.is_connected:
            raise CommunicationError("Serial port is not open. Call connect() first.")
        try:
            raw = (command + _TERMINATOR).encode(_ENCODING)
            self._serial.write(raw)
            self._serial.flush()
        except Exception as exc:
            raise CommunicationError(f"Failed to send command: {exc}") from exc

    def receive(self) -> str:
        """Read one line from the serial port.

        Returns:
            Decoded response string.

        Raises:
            CommunicationError: If the port is not open or reading fails.
            TimeoutError: If no response is received before the timeout.
        """
        if not self.is_connected:
            raise CommunicationError("Serial port is not open. Call connect() first.")
        try:
            raw = self._serial.readline()
        except Exception as exc:
            raise CommunicationError(f"Failed to read response: {exc}") from exc

        if not raw:
            raise TimeoutError(
                f"No response received within {self._timeout} seconds."
            )
        return raw.decode(_ENCODING, errors="replace").strip()

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the serial port is open."""
        return self._serial is not None and self._serial.is_open

    def __repr__(self) -> str:
        return (
            f"SerialCommunication(port={self._port!r}, "
            f"baud_rate={self._baud_rate}, connected={self.is_connected})"
        )


# ---------------------------------------------------------------------------
# Ethernet (TCP) back-end
# ---------------------------------------------------------------------------

class EthernetCommunication(CommunicationBase):
    """TCP socket communication with the Mitsubishi robot controller.

    Suitable for controllers equipped with an Ethernet option board
    (CR2B-574W / CR750-D / CR800-D).

    Args:
        host: IP address or hostname of the controller.
        port: TCP port.  Defaults to 10001.
        timeout: Socket timeout in seconds.  Defaults to 5.0.
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_TCP_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._socket: Optional[socket.socket] = None

    # ------------------------------------------------------------------
    # CommunicationBase interface
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Establish a TCP connection to the controller.

        Raises:
            ConnectionError: If the connection cannot be established.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout)
            sock.connect((self._host, self._port))
            self._socket = sock
        except OSError as exc:
            raise ConnectionError(
                f"Cannot connect to robot controller at {self._host}:{self._port}: {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Close the TCP connection."""
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None

    def send(self, command: str) -> None:
        """Send *command* over the TCP socket.

        Raises:
            CommunicationError: If the socket is not connected or sending fails.
        """
        if not self.is_connected:
            raise CommunicationError("Socket is not connected. Call connect() first.")
        try:
            raw = (command + _TERMINATOR).encode(_ENCODING)
            self._socket.sendall(raw)
        except OSError as exc:
            raise CommunicationError(f"Failed to send command: {exc}") from exc

    def receive(self) -> str:
        """Receive a response from the controller (terminated by ``\\r\\n``).

        Returns:
            Decoded response string.

        Raises:
            CommunicationError: If the socket is not connected or receiving fails.
            TimeoutError: If no data arrives before the socket timeout.
        """
        if not self.is_connected:
            raise CommunicationError("Socket is not connected. Call connect() first.")
        try:
            buffer = b""
            deadline = time.monotonic() + self._timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._socket.settimeout(remaining)
                chunk = self._socket.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                if b"\r\n" in buffer or b"\n" in buffer:
                    break
        except socket.timeout:
            pass
        except OSError as exc:
            raise CommunicationError(f"Failed to receive response: {exc}") from exc

        if not buffer:
            raise TimeoutError(
                f"No response received within {self._timeout} seconds."
            )
        return buffer.decode(_ENCODING, errors="replace").strip()

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the TCP socket is open."""
        return self._socket is not None

    def __repr__(self) -> str:
        return (
            f"EthernetCommunication(host={self._host!r}, "
            f"port={self._port}, connected={self.is_connected})"
        )
