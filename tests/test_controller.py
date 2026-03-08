"""Tests for robot_control.controller.RobotController."""

import pytest

from robot_control.communication import CommunicationBase
from robot_control.controller import RobotController
from robot_control.exceptions import (
    CommunicationError,
    CommandError,
    SafetyError,
    TimeoutError,
)
from robot_control.positions import CartesianPosition, JointPosition


# ---------------------------------------------------------------------------
# Stub communication back-end
# ---------------------------------------------------------------------------

class StubCommunication(CommunicationBase):
    """Controllable stub for unit-testing RobotController."""

    def __init__(self, responses=None):
        self._connected = False
        self._sent = []
        self._responses = list(responses or [])

    def connect(self):
        self._connected = True

    def disconnect(self):
        self._connected = False

    def send(self, command):
        self._sent.append(command)

    def receive(self):
        if not self._responses:
            raise TimeoutError("No more stub responses")
        return self._responses.pop(0)

    @property
    def is_connected(self):
        return self._connected

    def queue_response(self, response: str):
        self._responses.append(response)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_robot(responses=None) -> RobotController:
    stub = StubCommunication(responses=responses)
    robot = RobotController(stub)
    robot.connect()
    return robot


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestServoControl:
    def test_servo_on_sends_command(self):
        robot = make_robot(responses=["OK"])
        robot.servo_on()
        assert any("SERVO ON" in s for s in robot._comm._sent)

    def test_servo_on_sets_flag(self):
        robot = make_robot(responses=["OK"])
        robot.servo_on()
        assert robot.servo_enabled

    def test_servo_off_sends_command(self):
        robot = make_robot(responses=["OK", "OK"])
        robot.servo_on()
        robot.servo_off()
        assert any("SERVO OFF" in s for s in robot._comm._sent)

    def test_servo_off_clears_flag(self):
        robot = make_robot(responses=["OK", "OK"])
        robot.servo_on()
        robot.servo_off()
        assert not robot.servo_enabled

    def test_servo_on_raises_on_error_response(self):
        robot = make_robot(responses=["ERROR 7100"])
        with pytest.raises(CommandError):
            robot.servo_on()


class TestSpeedControl:
    def test_set_speed_sends_ovrd(self):
        robot = make_robot(responses=["OK"])
        robot.set_speed(50)
        assert any("OVRD 50" in s for s in robot._comm._sent)

    def test_set_speed_updates_property(self):
        robot = make_robot(responses=["OK"])
        robot.set_speed(75)
        assert robot.current_speed == 75

    def test_set_speed_out_of_range_raises(self):
        robot = make_robot()
        with pytest.raises(ValueError):
            robot.set_speed(0)


class TestMotionCommands:
    def test_move_joint_sends_mov(self):
        robot = make_robot(responses=["OK"])
        pos = JointPosition(j1=45.0, j2=-30.0)
        robot.move_joint(pos)
        assert any("MOV" in s for s in robot._comm._sent)

    def test_move_joint_validates_limits(self):
        robot = make_robot()
        pos = JointPosition(j1=999.0)  # exceeds J1 limit of ±240°
        with pytest.raises(SafetyError):
            robot.move_joint(pos)

    def test_move_joint_no_limit_check_when_disabled(self):
        robot = make_robot(responses=["OK"])
        robot._validate_limits = False
        pos = JointPosition(j1=999.0)
        robot.move_joint(pos)  # should not raise

    def test_move_cartesian_ptp(self):
        robot = make_robot(responses=["OK"])
        pos = CartesianPosition(x=300, y=0, z=400)
        robot.move_cartesian(pos, linear=False)
        assert any("MOV" in s for s in robot._comm._sent)

    def test_move_cartesian_linear(self):
        robot = make_robot(responses=["OK"])
        pos = CartesianPosition(x=300, y=0, z=400)
        robot.move_cartesian(pos, linear=True)
        assert any("MVS" in s for s in robot._comm._sent)

    def test_go_home_sends_home(self):
        robot = make_robot(responses=["OK"])
        robot.go_home()
        assert any("HOME" in s for s in robot._comm._sent)

    def test_stop_sends_stop(self):
        robot = make_robot()
        robot.stop()
        assert any("STOP" in s for s in robot._comm._sent)


class TestGripperControl:
    def test_hand_open_sends_hopen(self):
        robot = make_robot(responses=["OK"])
        robot.hand_open()
        assert any("HOPEN 1" in s for s in robot._comm._sent)

    def test_hand_close_sends_hclose(self):
        robot = make_robot(responses=["OK"])
        robot.hand_close()
        assert any("HCLOSE 1" in s for s in robot._comm._sent)

    def test_hand_open_second_gripper(self):
        robot = make_robot(responses=["OK"])
        robot.hand_open(2)
        assert any("HOPEN 2" in s for s in robot._comm._sent)


class TestStateEnquiry:
    def test_get_current_position(self):
        robot = make_robot(responses=["(300.000, 0.000, 400.000, 0.000, 90.000, 0.000)(7)"])
        result = robot.get_current_position()
        assert "300.000" in result

    def test_get_current_joint(self):
        robot = make_robot(responses=["(45.000, -30.000, 0.000, 0.000, 0.000, 0.000)"])
        result = robot.get_current_joint()
        assert "45.000" in result


class TestAlarmReset:
    def test_reset_alarm_sends_relalm(self):
        robot = make_robot(responses=["OK"])
        robot.reset_alarm()
        assert any("RELALM" in s for s in robot._comm._sent)


class TestContextManager:
    def test_context_manager_connects_and_disconnects(self):
        stub = StubCommunication(responses=["OK"])  # for servo_off on exit
        robot = RobotController(stub)
        with robot:
            assert robot.is_connected
        assert not robot.is_connected

    def test_context_manager_disables_servo_on_exit(self):
        stub = StubCommunication(responses=["OK", "OK"])
        robot = RobotController(stub)
        with robot:
            robot._servo_enabled = True
        assert any("SERVO OFF" in s for s in stub._sent)


class TestRepr:
    def test_repr_contains_key_info(self):
        robot = make_robot()
        r = repr(robot)
        assert "RobotController" in r
        assert "servo_enabled" in r
