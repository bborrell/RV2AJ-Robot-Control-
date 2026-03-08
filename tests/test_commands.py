"""Tests for robot_control.commands."""

import pytest

from robot_control.commands import (
    go_home,
    get_current_joint,
    get_current_position,
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
from robot_control.positions import CartesianPosition, JointPosition


class TestServoCommands:
    def test_servo_on(self):
        assert servo_on() == "SERVO ON"

    def test_servo_off(self):
        assert servo_off() == "SERVO OFF"


class TestMoveJoint:
    def test_move_to_zero_position(self):
        pos = JointPosition()
        cmd = move_joint(pos)
        assert cmd.startswith("MOV")
        assert "0.000" in cmd

    def test_move_with_angles(self):
        pos = JointPosition(j1=45.0, j2=-30.0, j3=90.0, j4=0.0, j5=0.0, j6=0.0)
        cmd = move_joint(pos)
        assert "45.000" in cmd
        assert "-30.000" in cmd
        assert "90.000" in cmd

    def test_command_contains_all_six_joints(self):
        pos = JointPosition(j1=1, j2=2, j3=3, j4=4, j5=5, j6=6)
        cmd = move_joint(pos)
        for val in ("1.000", "2.000", "3.000", "4.000", "5.000", "6.000"):
            assert val in cmd


class TestMoveCartesian:
    def test_ptp_command(self):
        pos = CartesianPosition(x=300, y=0, z=400)
        cmd = move_cartesian(pos, linear=False)
        assert cmd.startswith("MOV")
        assert "300.000" in cmd

    def test_linear_command(self):
        pos = CartesianPosition(x=300, y=0, z=400)
        cmd = move_cartesian(pos, linear=True)
        assert cmd.startswith("MVS")

    def test_coordinates_in_command(self):
        pos = CartesianPosition(x=100.5, y=-200.0, z=300.0, rx=10.0, ry=20.0, rz=30.0)
        cmd = move_cartesian(pos)
        assert "100.500" in cmd
        assert "-200.000" in cmd
        assert "10.000" in cmd


class TestSetSpeed:
    def test_valid_speeds(self):
        for v in (1, 50, 100):
            cmd = set_speed(v)
            assert cmd == f"OVRD {v}"

    def test_zero_is_invalid(self):
        with pytest.raises(ValueError):
            set_speed(0)

    def test_over_100_is_invalid(self):
        with pytest.raises(ValueError):
            set_speed(101)


class TestHandCommands:
    def test_hand_open_default(self):
        assert hand_open() == "HOPEN 1"

    def test_hand_open_second(self):
        assert hand_open(2) == "HOPEN 2"

    def test_hand_close_default(self):
        assert hand_close() == "HCLOSE 1"

    def test_hand_close_second(self):
        assert hand_close(2) == "HCLOSE 2"


class TestMiscCommands:
    def test_go_home(self):
        assert go_home() == "HOME"

    def test_stop(self):
        assert stop() == "STOP"

    def test_reset_alarm(self):
        assert reset_alarm() == "RELALM"

    def test_get_current_position(self):
        assert get_current_position() == "P_CURR"

    def test_get_current_joint(self):
        assert get_current_joint() == "J_CURR"


class TestSetTool:
    def test_valid_tool(self):
        cmd = set_tool(3)
        assert cmd == "TOOL 3"

    def test_tool_zero_invalid(self):
        with pytest.raises(ValueError):
            set_tool(0)

    def test_tool_17_invalid(self):
        with pytest.raises(ValueError):
            set_tool(17)


class TestWait:
    def test_wait_command(self):
        cmd = wait(1.5)
        assert cmd == "DLY 1.500"

    def test_zero_duration_invalid(self):
        with pytest.raises(ValueError):
            wait(0)

    def test_negative_duration_invalid(self):
        with pytest.raises(ValueError):
            wait(-1)
