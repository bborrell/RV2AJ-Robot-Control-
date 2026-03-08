"""Tests for robot_control.communication.

These tests use a minimal stub/mock to avoid requiring real hardware or
network connections.
"""

import pytest

from robot_control.communication import CommunicationBase, EthernetCommunication, SerialCommunication
from robot_control.exceptions import CommunicationError, TimeoutError


# ---------------------------------------------------------------------------
# Stub implementation for testing the abstract base class
# ---------------------------------------------------------------------------

class StubCommunication(CommunicationBase):
    """In-memory communication stub for unit testing."""

    def __init__(self, responses=None):
        self._connected = False
        self._sent = []
        self._responses = list(responses or [])

    def connect(self):
        self._connected = True

    def disconnect(self):
        self._connected = False

    def send(self, command):
        if not self._connected:
            raise CommunicationError("Not connected")
        self._sent.append(command)

    def receive(self):
        if not self._connected:
            raise CommunicationError("Not connected")
        if not self._responses:
            raise TimeoutError("No more responses")
        return self._responses.pop(0)

    @property
    def is_connected(self):
        return self._connected


class TestCommunicationBase:
    def test_send_receive_calls_both(self):
        stub = StubCommunication(responses=["OK"])
        stub.connect()
        result = stub.send_receive("SERVO ON")
        assert result == "OK"
        assert stub._sent == ["SERVO ON"]

    def test_is_connected_false_before_connect(self):
        stub = StubCommunication()
        assert not stub.is_connected

    def test_is_connected_true_after_connect(self):
        stub = StubCommunication()
        stub.connect()
        assert stub.is_connected

    def test_is_connected_false_after_disconnect(self):
        stub = StubCommunication()
        stub.connect()
        stub.disconnect()
        assert not stub.is_connected

    def test_send_raises_when_not_connected(self):
        stub = StubCommunication()
        with pytest.raises(CommunicationError):
            stub.send("SERVO ON")

    def test_receive_raises_timeout_when_no_responses(self):
        stub = StubCommunication()
        stub.connect()
        with pytest.raises(TimeoutError):
            stub.receive()


class TestSerialCommunication:
    def test_repr_shows_port(self):
        comm = SerialCommunication(port="/dev/ttyUSB0")
        assert "/dev/ttyUSB0" in repr(comm)

    def test_not_connected_before_connect(self):
        comm = SerialCommunication(port="/dev/ttyUSB0")
        assert not comm.is_connected

    def test_send_raises_when_not_connected(self):
        comm = SerialCommunication(port="/dev/ttyUSB0")
        with pytest.raises(CommunicationError):
            comm.send("SERVO ON")

    def test_receive_raises_when_not_connected(self):
        comm = SerialCommunication(port="/dev/ttyUSB0")
        with pytest.raises(CommunicationError):
            comm.receive()

    def test_connect_raises_connection_error_on_bad_port(self):
        from robot_control.exceptions import ConnectionError as RobotConnectionError
        comm = SerialCommunication(port="/dev/nonexistent_port_xyz")
        with pytest.raises(RobotConnectionError):
            comm.connect()


class TestEthernetCommunication:
    def test_repr_shows_host(self):
        comm = EthernetCommunication(host="192.168.0.10")
        assert "192.168.0.10" in repr(comm)

    def test_not_connected_before_connect(self):
        comm = EthernetCommunication(host="192.168.0.10")
        assert not comm.is_connected

    def test_send_raises_when_not_connected(self):
        comm = EthernetCommunication(host="192.168.0.10")
        with pytest.raises(CommunicationError):
            comm.send("SERVO ON")

    def test_receive_raises_when_not_connected(self):
        comm = EthernetCommunication(host="192.168.0.10")
        with pytest.raises(CommunicationError):
            comm.receive()

    def test_connect_raises_on_unreachable_host(self):
        from robot_control.exceptions import ConnectionError as RobotConnectionError
        comm = EthernetCommunication(host="192.0.2.1", timeout=0.5)  # TEST-NET, guaranteed unreachable
        with pytest.raises(RobotConnectionError):
            comm.connect()
