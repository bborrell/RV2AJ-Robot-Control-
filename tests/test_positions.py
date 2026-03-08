"""Tests for robot_control.positions."""

import pytest

from robot_control.positions import (
    CartesianPosition,
    JointPosition,
    HOME_POSITION,
    JOINT_LIMITS,
)


class TestJointPosition:
    def test_defaults_are_zero(self):
        pos = JointPosition()
        assert pos.as_list() == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def test_as_list_order(self):
        pos = JointPosition(j1=1, j2=2, j3=3, j4=4, j5=5, j6=6)
        assert pos.as_list() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]

    def test_str_contains_all_joints(self):
        pos = JointPosition(j1=10.0, j2=-20.0, j3=30.0, j4=-40.0, j5=50.0, j6=-60.0)
        s = str(pos)
        for label in ("J1=", "J2=", "J3=", "J4=", "J5=", "J6="):
            assert label in s

    def test_home_position_is_all_zeros(self):
        assert HOME_POSITION.as_list() == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


class TestCartesianPosition:
    def test_defaults_are_zero(self):
        pos = CartesianPosition()
        assert pos.x == 0.0
        assert pos.y == 0.0
        assert pos.z == 0.0

    def test_str_contains_all_coords(self):
        pos = CartesianPosition(x=100, y=200, z=300, rx=10, ry=20, rz=30)
        s = str(pos)
        for label in ("X=", "Y=", "Z=", "Rx=", "Ry=", "Rz="):
            assert label in s

    def test_configuration_default(self):
        pos = CartesianPosition()
        assert pos.configuration == "7"

    def test_custom_configuration(self):
        pos = CartesianPosition(configuration="4")
        assert pos.configuration == "4"


class TestJointLimits:
    def test_six_joints_defined(self):
        assert len(JOINT_LIMITS) == 6

    def test_j1_limits(self):
        j1 = JOINT_LIMITS[0]
        assert j1["axis"] == "J1"
        assert j1["min"] < 0
        assert j1["max"] > 0
